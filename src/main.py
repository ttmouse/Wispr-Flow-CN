import sys
import traceback
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, QMetaObject, Qt, Q_ARG, QObject
from ui.main_window import MainWindow
from audio_capture import AudioCapture
from funasr_engine import FunASREngine
from hotkey_manager import HotkeyManager
from clipboard_manager import ClipboardManager
from download_model import download_funasr_model
import re

class AudioCaptureThread(QThread):
    audio_captured = pyqtSignal(object)

    def __init__(self, audio_capture):
        super().__init__()
        self.audio_capture = audio_capture
        self.is_recording = False

    def run(self):
        self.is_recording = True
        self.audio_capture.start_recording()
        while self.is_recording:
            data = self.audio_capture.read_audio()
            if len(data) > 0:
                self.audio_captured.emit(data)
        audio_data = self.audio_capture.stop_recording()
        self.audio_captured.emit(audio_data)

    def stop(self):
        self.is_recording = False

class TranscriptionThread(QThread):
    transcription_done = pyqtSignal(str)

    def __init__(self, audio_data, funasr_engine):
        super().__init__()
        self.audio_data = audio_data
        self.funasr_engine = funasr_engine

    def run(self):
        try:
            result = self.funasr_engine.transcribe(self.audio_data)
            print("转写完成，发送结果信号")
            self.transcription_done.emit(result)
        except Exception as e:
            print(f"转写过程中出错: {e}")
            print(traceback.format_exc())
            self.transcription_done.emit("转写失败，请重试")

class Application(QObject):
    update_ui_signal = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        try:
            print("正在初始化应用程序...")
            self.app = QApplication(sys.argv)
            print("QApplication 已创建")
            
            self.main_window = MainWindow()
            print("主窗口已创建")
            
            self.audio_capture = AudioCapture()
            print("音频捕获已初始化")
            
            print("正在下载模型...")
            model_dir = download_funasr_model()
            print(f"模型已下载到: {model_dir}")
            
            self.funasr_engine = FunASREngine(model_dir)
            print("FunASR引擎已初始化")
            
            self.hotkey_manager = HotkeyManager()
            self.clipboard_manager = ClipboardManager()
            print("热键管理器和剪贴板管理器已初始化")
            
            self.recording = False
            self.audio_data = []

            self.setup_connections()
            print("连接已设置")

            self.update_timer = QTimer()
            self.update_timer.timeout.connect(self.main_window.update)
            self.update_timer.start(100)  # 每100毫秒刷新一次UI
            print("UI更新定时器已启动")
            
        except Exception as e:
            print(f"初始化过程中出错: {e}")
            print(traceback.format_exc())
            sys.exit(1)

    def setup_connections(self):
        self.hotkey_manager.set_press_callback(self.on_option_press)
        self.hotkey_manager.set_release_callback(self.on_option_release)
        self.update_ui_signal.connect(self.update_ui)

    def run(self):
        try:
            self.main_window.show()
            self.hotkey_manager.start_listening()
            return self.app.exec()
        finally:
            self.cleanup()

    def cleanup(self):
        self.audio_capture.clear_recording_data()
        if hasattr(self, 'transcription_thread'):
            self.transcription_thread.quit()
            self.transcription_thread.wait()
        print("应用程序清理完成")

    def on_option_press(self):
        if not self.recording:
            self.main_window.update_status("正在录音...")
            self.recording = True
            self.audio_data = []
            print("开始录音")
            self.audio_capture_thread = AudioCaptureThread(self.audio_capture)
            self.audio_capture_thread.audio_captured.connect(self.on_audio_captured)
            self.audio_capture_thread.start()

    def on_option_release(self):
        if self.recording:
            self.recording = False
            self.audio_capture_thread.stop()
            self.audio_capture_thread.wait()
            self.main_window.update_status("正在转写...")
            
            audio_data = self.audio_capture.get_audio_data()
            print(f"捕获的音频数据总长度：{len(audio_data)}，数据类型：{audio_data.dtype}")
            
            if len(audio_data) > 0:
                self.transcription_thread = TranscriptionThread(audio_data, self.funasr_engine)
                self.transcription_thread.transcription_done.connect(self.on_transcription_done)
                self.transcription_thread.start()
            else:
                print("没有捕获到音频数据")
                self.main_window.update_status("录音失败")
            print("停止录音")

    def on_transcription_done(self, result):
        # 提取纯文本内容
        if isinstance(result, str):
            text = result
        elif isinstance(result, dict):
            text = result.get('text', '')
        elif isinstance(result, list) and len(result) > 0:
            text = result[0].get('text', '') if isinstance(result[0], dict) else str(result[0])
        else:
            text = str(result)

        # 清理文本
        # 移除所有 <|...|> 标记及其内容
        text = re.sub(r'<\s*\|[^|]*\|\s*>', '', text)
        # 移除多余的空格
        text = re.sub(r'\s+', ' ', text)
        # 移除首尾空白字符
        text = text.strip()

        print(f"转写结果：{text}")
        self.clipboard_manager.copy_to_clipboard(text)
        self.clipboard_manager.paste_to_current_app()
        
        # 发送信号以更新UI
        self.update_ui_signal.emit("转写完成", text)
        
        print("UI 更新信号已发送")
        
        if hasattr(self, 'transcription_thread'):
            self.transcription_thread.quit()
            self.transcription_thread.wait()
            del self.transcription_thread
        
        self.audio_capture.clear_recording_data()

    def update_ui(self, status, result):
        self.main_window.update_status(status)
        self.main_window.display_result(result)
        print("UI 已更新")

    def on_audio_captured(self, data):
        # 不需要在里累积数据，因为我们在 get_audio_data 中获取所有数据
        pass

    def set_hotwords(self, hotwords):
        if hasattr(self, 'funasr_engine'):
            self.funasr_engine.model.set_hotwords(hotwords)

if __name__ == "__main__":
    try:
        print("正在创建应用程序实例...")
        app = Application()
        print("应用程序实例已创建，正在运行...")
        sys.exit(app.run())
    except Exception as e:
        print(f"运行应用程序时出错: {e}")
        print(traceback.format_exc())
        sys.exit(1)