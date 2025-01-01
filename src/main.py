import sys
import traceback
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, QMetaObject, Qt, Q_ARG, QObject
from ui.main_window import MainWindow
from audio_capture import AudioCapture
from funasr_engine import FunASREngine
from hotkey_manager import HotkeyManager
from clipboard_manager import ClipboardManager
import re
from context_manager import Context

# 设置环境变量以隐藏系统日志
os.environ['QT_LOGGING_RULES'] = '*.debug=false;qt.qpa.*=false'
os.environ['QT_MAC_DISABLE_FOREGROUND_APPLICATION_TRANSFORM'] = '1'

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
            # 处理 FunASR 返回的结果格式
            if isinstance(result, list) and len(result) > 0:
                text = result[0].get('text', '')
            elif isinstance(result, dict):
                text = result.get('text', '')
            else:
                text = str(result)
            self.transcription_done.emit(text)
        except Exception as e:
            print(f"❌ 转写失败: {e}")
            self.transcription_done.emit("转写失败，请重试")

class Application(QObject):
    update_ui_signal = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        try:
            self.app = QApplication(sys.argv)
            self.context = Context()
            self.main_window = MainWindow()
            self.audio_capture = AudioCapture()
            
            print("正在加载语音识别模型...")
            self.funasr_engine = FunASREngine()
            print("✓ 语音识别就绪")
            
            self.hotkey_manager = HotkeyManager()
            self.clipboard_manager = ClipboardManager()
            
            self.recording = False
            self.paused = False
            self.audio_data = []

            self.setup_connections()
            self.update_timer = QTimer()
            self.update_timer.timeout.connect(self.main_window.update)
            self.update_timer.start(100)
            
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            print(traceback.format_exc())
            sys.exit(1)

    def setup_connections(self):
        self.hotkey_manager.set_press_callback(self.on_option_press)
        self.hotkey_manager.set_release_callback(self.on_option_release)
        self.update_ui_signal.connect(self.update_ui)
        self.main_window.record_button_clicked.connect(self.toggle_recording)
        self.main_window.pause_button_clicked.connect(self.toggle_pause)
        self.main_window.space_key_pressed.connect(self.on_space_key_pressed)

    def toggle_recording(self):
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()

    def toggle_pause(self):
        if self.recording:
            if not self.paused:
                self.pause_recording()
            else:
                self.resume_recording()

    def start_recording(self):
        if not self.recording:
            self.context.record_action("开始录音")
            self.context.set_recording_state("recording")
            self.recording = True
            self.paused = False
            self.audio_data = []
            
            try:
                self.audio_capture_thread = AudioCaptureThread(self.audio_capture)
                self.audio_capture_thread.audio_captured.connect(self.on_audio_captured)
                self.audio_capture_thread.start()
                self.main_window.set_recording_state(True)
                self.main_window.update_status("正在录音...")
            except Exception as e:
                error_msg = f"开始录音时出错: {str(e)}"
                self.context.record_error(error_msg)
                print(error_msg)
                self.main_window.update_status("录音失败")

    def stop_recording(self):
        if self.recording:
            self.recording = False
            self.paused = False
            self.audio_capture_thread.stop()
            self.audio_capture_thread.wait()
            
            try:
                audio_data = self.audio_capture.get_audio_data()
                duration = len(audio_data) / (16000 * 4)  # 采样率16000，每个样本4字节
                
                if len(audio_data) > 0:
                    print(f"⏺️  录音完成 ({duration:.1f}秒)")
                    self.main_window.update_status("正在转写...")
                    self.transcription_thread = TranscriptionThread(audio_data, self.funasr_engine)
                    self.transcription_thread.transcription_done.connect(self.on_transcription_done)
                    self.transcription_thread.start()
                else:
                    print("❌ 未检测到声音")
                    self.main_window.update_status("录音失败")
            except Exception as e:
                print(f"❌ 录音失败: {e}")
                self.main_window.update_status("录音失败")

    def pause_recording(self):
        if self.recording and not self.paused:
            self.context.record_action("暂停录音")
            self.context.set_recording_state("paused")
            self.paused = True
            self.audio_capture_thread.stop()
            self.main_window.update_status("录音已暂停")
            self.main_window.set_paused_state(True)

    def resume_recording(self):
        if self.recording and self.paused:
            self.context.record_action("恢复录音")
            self.context.set_recording_state("recording")
            self.paused = False
            self.audio_capture_thread = AudioCaptureThread(self.audio_capture)
            self.audio_capture_thread.audio_captured.connect(self.on_audio_captured)
            self.audio_capture_thread.start()
            self.main_window.update_status("正在录音...")
            self.main_window.set_paused_state(False)

    def on_option_press(self):
        if not self.recording:
            self.start_recording()

    def on_option_release(self):
        if self.recording:
            self.stop_recording()

    def on_space_key_pressed(self):
        self.toggle_recording()

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
        self.hotkey_manager.stop_listening()

    def on_transcription_done(self, result):
        try:
            # 处理 FunASR 返回的结果格式
            if isinstance(result, list) and len(result) > 0:
                text = result[0].get('text', '')
            elif isinstance(result, dict):
                text = result.get('text', '')
            else:
                text = str(result)

            # 只移除特殊标记，保留标点符号
            text = re.sub(r'<\s*\|[^|]*\|\s*>', '', text)
            # 移除多余空格但保留标点
            text = re.sub(r'\s+', '', text)
            text = text.strip()

            print(f"✓ {text}")
            self.clipboard_manager.copy_to_clipboard(text)
            self.clipboard_manager.paste_to_current_app()
            self.update_ui_signal.emit("转写完成", text)
            
            if hasattr(self, 'transcription_thread'):
                self.transcription_thread.quit()
                self.transcription_thread.wait()
                
            self.context.reset()
        except Exception as e:
            print(f"❌ 处理转写结果失败: {e}")
            self.update_ui_signal.emit("转写失败", "处理结果时出错")

    def update_ui(self, status, result):
        self.main_window.update_status(status)
        self.main_window.display_result(result)

    def on_audio_captured(self, data):
        # 不需要在里累积数据，因为我们在 get_audio_data 中获取所有数据
        pass

    def set_hotwords(self, hotwords):
        if hasattr(self, 'funasr_engine'):
            self.funasr_engine.model.set_hotwords(hotwords)

if __name__ == "__main__":
    try:
        print("正在创建应用程实例...")
        app = Application()
        print("应用程序实例已创建，正在运行...")
        sys.exit(app.run())
    except Exception as e:
        print(f"运行应用程序时出错: {e}")
        print(traceback.format_exc())
        sys.exit(1)