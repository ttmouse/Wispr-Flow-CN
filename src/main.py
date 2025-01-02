import sys
import traceback
import os
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, QMetaObject, Qt, Q_ARG, QObject, pyqtSlot
from PyQt6.QtGui import QIcon
from ui.main_window import MainWindow
from audio_capture import AudioCapture
from funasr_engine import FunASREngine
from hotkey_manager import HotkeyManager
from clipboard_manager import ClipboardManager
from state_manager import StateManager
from context_manager import Context
from audio_threads import AudioCaptureThread, TranscriptionThread
from global_hotkey import GlobalHotkeyManager
import time
import re

# 应用信息
APP_NAME = "Dou-flow"  # 统一应用名称
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

class Application(QObject):
    update_ui_signal = pyqtSignal(str, str)
    show_window_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        try:
            self.app = QApplication(sys.argv)
            
            # 设置应用程序属性
            if sys.platform == 'darwin':
                self.app.setAttribute(Qt.ApplicationAttribute.AA_DontShowIconsInMenus, False)
            
            # 设置应用程序信息
            self.app.setApplicationName(APP_NAME)
            self.app.setApplicationDisplayName(APP_NAME)
            self.app.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "..", "resources", "mic1.png")))
            self.app.setQuitOnLastWindowClosed(False)
            
            # 创建系统托盘图标
            self.tray_icon = QSystemTrayIcon(QIcon(os.path.join(os.path.dirname(__file__), "..", "resources", "mic1.png")), self.app)
            
            # 创建托盘菜单
            tray_menu = QMenu()
            show_action = tray_menu.addAction("显示/隐藏")
            show_action.triggered.connect(self.show_window)
            tray_menu.addSeparator()
            quit_action = tray_menu.addAction("退出")
            quit_action.triggered.connect(self.quit_application)
            
            # 设置托盘图标的菜单
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()
            
            # 初始化组件
            self.state_manager = StateManager()
            self.main_window = MainWindow()
            self.main_window.set_state_manager(self.state_manager)
            
            # 初始化其他组件
            self.audio_capture = AudioCapture()
            print("正在加载语音识别模型...")
            self.funasr_engine = FunASREngine()
            print("✓ 语音识别就绪")
            
            self.hotkey_manager = HotkeyManager()
            self.clipboard_manager = ClipboardManager()
            self.global_hotkey = GlobalHotkeyManager()
            
            self.recording = False

            # 连接信号
            self.show_window_signal.connect(self._show_window_internal)
            self.global_hotkey.hotkey_triggered.connect(self.show_window)
            self.setup_connections()
            
            # 设置全局快捷键
            self.global_hotkey.setup()

        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            print(traceback.format_exc())
            sys.exit(1)

    def start_recording(self):
        """开始录音"""
        if not self.recording:
            self.recording = True
            
            try:
                self.audio_capture_thread = AudioCaptureThread(self.audio_capture)
                self.audio_capture_thread.audio_captured.connect(self.on_audio_captured)
                self.audio_capture_thread.recording_stopped.connect(self.stop_recording)
                self.audio_capture_thread.start()
                self.state_manager.start_recording()
            except Exception as e:
                error_msg = f"开始录音时出错: {str(e)}"
                print(error_msg)
                self.update_ui_signal.emit(f"❌ {error_msg}", "")

    def stop_recording(self):
        """停止录音"""
        if self.recording:
            self.recording = False
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

    def cleanup(self):
        """清理资源"""
        try:
            self.audio_capture.clear_recording_data()
            if hasattr(self, 'transcription_thread'):
                self.transcription_thread.quit()
                self.transcription_thread.wait()
            self.hotkey_manager.stop_listening()
            self.global_hotkey.cleanup()
        except Exception as e:
            print(f"❌ 清理资源失败: {e}")

    @pyqtSlot()
    def show_window(self):
        """显示主窗口（可以从其他线程调用）"""
        self.show_window_signal.emit()

    def setup_connections(self):
        """设置信号连接"""
        self.hotkey_manager.set_press_callback(self.on_option_press)
        self.hotkey_manager.set_release_callback(self.on_option_release)
        self.update_ui_signal.connect(self.update_ui)
        self.main_window.record_button_clicked.connect(self.toggle_recording)
        self.main_window.history_item_clicked.connect(self.on_history_item_clicked)
        self.state_manager.status_changed.connect(self.main_window.update_status)
        self.show_window_signal.connect(self._show_window_internal)

    def toggle_recording(self):
        """切换录音状态"""
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()

    def on_option_press(self):
        """处理Option键按下事件"""
        if not self.recording:
            self.start_recording()

    def on_option_release(self):
        """处理Option键释放事件"""
        if self.recording:
            self.stop_recording()

    def on_audio_captured(self, data):
        """音频数据捕获回调"""
        # 录音过程中不需要频繁更新状态，因为状态已经在start_recording时设置了
        pass

    def quit_application(self):
        """退出应用程序"""
        self.cleanup()
        self.app.quit()

    def _show_window_internal(self):
        """在主线程中显示窗口"""
        try:
            # 显示并激活窗口
            self.main_window.show()
            self.main_window.activateWindow()
            print("✓ 窗口已显示")
        except Exception as e:
            print(f"❌ 显示窗口失败: {e}")
    
    def _paste_and_reactivate(self, text):
        """执行粘贴操作"""
        try:
            # 只执行粘贴，不影响窗口状态
            self.clipboard_manager.paste_to_current_app()
        except Exception as e:
            print(f"❌ 粘贴操作失败: {e}")
            print(traceback.format_exc())
    
    def on_transcription_done(self, text):
        """转写完成的回调"""
        if text and text.strip():
            # 1. 先复制到剪贴板
            self.clipboard_manager.copy_to_clipboard(text)
            # 2. 更新UI（如果窗口可见）
            if self.main_window.isVisible():
                self.main_window.display_result(text)
            # 3. 延迟执行粘贴操作
            QTimer.singleShot(100, lambda: self._paste_and_reactivate(text))
            # 打印日志
            print(f"✓ {text}")
    
    def on_history_item_clicked(self, text):
        """处理历史记录点击事件"""
        # 1. 先复制到剪贴板
        self.clipboard_manager.copy_to_clipboard(text)
        # 2. 更新UI
        self.update_ui_signal.emit("准备粘贴历史记录", text)
        # 3. 延迟执行粘贴操作
        QTimer.singleShot(100, lambda: self._paste_and_reactivate(text))

    def update_ui(self, status, result):
        """更新界面显示"""
        self.main_window.update_status(status)
        if result and result.strip():
            # 只有在不是历史记录点击的情况下才添加到历史记录
            if status != "准备粘贴历史记录":
                self.main_window.display_result(result)

    def run(self):
        """运行应用程序"""
        try:
            # 显示主窗口
            self.main_window.show()
            
            # 启动热键监听
            self.hotkey_manager.start_listening()
            
            # 运行应用程序主循环
            return self.app.exec()
        except Exception as e:
            print(f"❌ 运行应用程序时出错: {e}")
            print(traceback.format_exc())
            return 1
        finally:
            self.cleanup()

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