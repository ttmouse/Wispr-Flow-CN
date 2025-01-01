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
from state_manager import StateManager
from context_manager import Context
import time
import re

# 应用信息
APP_NAME = "FunASR"
APP_VERSION = "1.0.0"
APP_AUTHOR = "ttmouse"
# 设置环境变量以隐藏系统日志
os.environ['QT_LOGGING_RULES'] = '*.debug=false;qt.qpa.*=false'
os.environ['QT_MAC_DISABLE_FOREGROUND_APPLICATION_TRANSFORM'] = '1'

def get_app_path():
    """获取应用程序路径"""
    if getattr(sys, 'frozen', False):
        # 打包后的路径
        return os.path.dirname(sys.executable)
    else:
        # 开发环境路径
        return os.path.dirname(os.path.abspath(__file__))

class AudioCaptureThread(QThread):
    audio_captured = pyqtSignal(object)
    recording_stopped = pyqtSignal()  # 新增信号用于通知录音停止

    def __init__(self, audio_capture):
        super().__init__()
        self.audio_capture = audio_capture
        self.is_recording = False

    def run(self):
        self.is_recording = True
        self.audio_capture.start_recording()
        while self.is_recording:
            data = self.audio_capture.read_audio()
            if data is None:  # 检测到需要停止录音
                self.is_recording = False
                break
            if len(data) > 0:
                self.audio_captured.emit(data)
        audio_data = self.audio_capture.stop_recording()
        self.audio_captured.emit(audio_data)
        if not self.is_recording:  # 如果是自动停止，发送信号
            self.recording_stopped.emit()

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
            self.state_manager = StateManager()
            self.main_window = MainWindow()
            self.main_window.set_state_manager(self.state_manager)
            self.audio_capture = AudioCapture()
            
            print("正在加载语音识别模型...")
            self.funasr_engine = FunASREngine()
            print("✓ 语音识别就绪")
            
            self.hotkey_manager = HotkeyManager()
            self.clipboard_manager = ClipboardManager()
            
            self.recording = False
            self.paused = False
            self.audio_data = []
            self._recording_start_time = 0

            self.setup_connections()
            
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
        self.main_window.history_item_clicked.connect(self.on_history_item_clicked)

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
            self._recording_start_time = time.time()
            
            try:
                self.audio_capture_thread = AudioCaptureThread(self.audio_capture)
                self.audio_capture_thread.audio_captured.connect(self.on_audio_captured)
                self.audio_capture_thread.recording_stopped.connect(self.stop_recording)
                self.audio_capture_thread.start()
                self.main_window.record_button.setText("停止录音")
                self.main_window.pause_button.setEnabled(True)
                self.state_manager.start_recording()
            except Exception as e:
                error_msg = f"开始录音时出错: {str(e)}"
                self.context.record_error(error_msg)
                print(error_msg)
                self.update_ui_signal.emit(f"❌ {error_msg}", "")

    def stop_recording(self):
        if self.recording:
            self.recording = False
            self.paused = False
            self.audio_capture_thread.stop()
            self.audio_capture_thread.wait()
            
            try:
                audio_data = self.audio_capture.get_audio_data()
                
                if len(audio_data) > 0:
                    self.state_manager.stop_recording()
                    self.transcription_thread = TranscriptionThread(audio_data, self.funasr_engine)
                    self.transcription_thread.transcription_done.connect(self.on_transcription_done)
                    self.transcription_thread.start()
                else:
                    print("❌ 未检测到声音")
                    self.update_ui_signal.emit("❌ 未检测到声音", "")
            except Exception as e:
                print(f"❌ 录音失败: {e}")
                self.update_ui_signal.emit(f"❌ 录音失败: {e}", "")
            
            self.main_window.record_button.setText("开始录音")
            self.main_window.pause_button.setEnabled(False)

    def pause_recording(self):
        if self.recording and not self.paused:
            self.context.record_action("暂停录音")
            self.context.set_recording_state("paused")
            self.paused = True
            self.audio_capture_thread.stop()
            self.state_manager.toggle_pause()
            self.main_window.set_paused_state(True)

    def resume_recording(self):
        if self.recording and self.paused:
            self.context.record_action("恢复录音")
            self.context.set_recording_state("recording")
            self.paused = False
            self.audio_capture_thread = AudioCaptureThread(self.audio_capture)
            self.audio_capture_thread.audio_captured.connect(self.on_audio_captured)
            self.audio_capture_thread.start()
            self.state_manager.toggle_pause()
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
            # 确保窗口显示在最前面
            self.main_window.raise_()
            self.main_window.activateWindow()
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

            # 只移除特殊标记，保留标点符号和英文单词间的空格
            text = re.sub(r'<\s*\|[^|]*\|\s*>', '', text)
            # 移除中文间的空格，但保留英文单词间的空格
            text = re.sub(r'(?<![a-zA-Z])\s+(?![a-zA-Z])', '', text)
            text = text.strip()

            print(f"✓ {text}")
            self.clipboard_manager.copy_to_clipboard(text)
            self.clipboard_manager.paste_to_current_app()
            self.update_ui_signal.emit("✓ 转写完成", text)
            
            if hasattr(self, 'transcription_thread'):
                self.transcription_thread.quit()
                self.transcription_thread.wait()
                
            self.context.reset()
        except Exception as e:
            print(f"❌ 处理转写结果失败: {e}")
            self.update_ui_signal.emit(f"❌ 处理转写结果失败: {e}", "")

    def update_ui(self, status, result):
        """更新界面显示"""
        self.main_window.update_status(status)
        if result:
            self.main_window.display_result(result)

    def on_audio_captured(self, data):
        """音频数据捕获回调"""
        if self.recording and not self.paused:
            duration = time.time() - self._recording_start_time
            self.state_manager.update_recording_status(duration)

    def set_hotwords(self, hotwords):
        if hasattr(self, 'funasr_engine'):
            self.funasr_engine.model.set_hotwords(hotwords)

    def on_history_item_clicked(self, text):
        """处理历史记录点击事件"""
        self.clipboard_manager.copy_to_clipboard(text)
        self.clipboard_manager.paste_to_current_app()
        self.update_ui_signal.emit("已粘贴历史记录", text)

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