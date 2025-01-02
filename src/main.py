import sys
import traceback
import os
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMenuBar
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, QMetaObject, Qt, Q_ARG, QObject, pyqtSlot
from PyQt6.QtGui import QIcon, QAction, QKeySequence
from ui.main_window import MainWindow
from audio_capture import AudioCapture
from funasr_engine import FunASREngine
from hotkey_manager import HotkeyManager
from clipboard_manager import ClipboardManager
from state_manager import StateManager
from context_manager import Context
import time
import re
from pynput import keyboard

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
    show_window_signal = pyqtSignal()  # 新增信号用于在主线程中显示窗口

    def __init__(self):
        super().__init__()
        try:
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("语音识别")
            self.app.setQuitOnLastWindowClosed(False)  # 关闭最后一个窗口时不退出
            
            self.context = Context()
            self.state_manager = StateManager()
            self.main_window = MainWindow()
            self.main_window.set_state_manager(self.state_manager)
            
            # 创建顶部菜单栏
            self.setup_menu_bar()
            
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

            # 连接信号
            self.show_window_signal.connect(self._show_window_internal)
            
            # 设置全局快捷键
            self.setup_global_hotkey()
            
            self.setup_connections()
            
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            print(traceback.format_exc())
            sys.exit(1)

    def start_recording(self):
        """开始录音"""
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
                self.state_manager.start_recording()
            except Exception as e:
                error_msg = f"开始录音时出错: {str(e)}"
                self.context.record_error(error_msg)
                print(error_msg)
                self.update_ui_signal.emit(f"❌ {error_msg}", "")

    def stop_recording(self):
        """停止录音"""
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

    def cleanup(self):
        """清理资源"""
        try:
            self.audio_capture.clear_recording_data()
            if hasattr(self, 'transcription_thread'):
                self.transcription_thread.quit()
                self.transcription_thread.wait()
            self.hotkey_manager.stop_listening()
            if hasattr(self, 'keyboard_listener'):
                self.keyboard_listener.stop()
        except Exception as e:
            print(f"❌ 清理资源失败: {e}")

    def setup_menu_bar(self):
        """设置顶部菜单栏"""
        try:
            # 创建菜单栏
            menubar = self.main_window.menuBar()
            
            # 创建应用程序菜单
            app_menu = menubar.addMenu("语音识别")
            
            # 添加显示窗口选项
            show_action = QAction("显示窗口", self.main_window)
            show_action.setShortcut("Cmd+.")  # 设置快捷键
            show_action.triggered.connect(self.show_window)
            app_menu.addAction(show_action)
            
            # 添加分隔线
            app_menu.addSeparator()
            
            # 添加退出选项
            quit_action = QAction("退出", self.main_window)
            quit_action.setShortcut("Cmd+Q")  # 设置标准的退出快捷键
            quit_action.triggered.connect(self.quit_application)
            app_menu.addAction(quit_action)
            
            print("✓ 顶部菜单栏已创建")
        except Exception as e:
            print(f"❌ 创建顶部菜单栏失败: {e}")
            print(traceback.format_exc())

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
        self.main_window.space_key_pressed.connect(self.on_space_key_pressed)
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

    def on_space_key_pressed(self):
        """处理空格键按下事件"""
        self.toggle_recording()

    def on_audio_captured(self, data):
        """音频数据捕获回调"""
        if self.recording and not self.paused:
            self.state_manager.update_status()

    def quit_application(self):
        """退出应用程序"""
        self.cleanup()
        self.app.quit()

    def setup_global_hotkey(self):
        """设置全局快捷键"""
        try:
            # 创建热键监听器
            self.pressed_keys = set()
            
            def on_press(key):
                try:
                    # 记录按下的键
                    if key == keyboard.Key.cmd:
                        self.pressed_keys.add('cmd')
                    elif hasattr(key, 'char') and key.char == '.':
                        self.pressed_keys.add('.')
                    
                    # 检查组合键
                    if 'cmd' in self.pressed_keys and '.' in self.pressed_keys:
                        print("检测到快捷键: Command + .")
                        # 使用信号来显示窗口
                        self.show_window_signal.emit()
                except Exception as e:
                    print(f"❌ 处理按键事件失败: {e}")
                    print(traceback.format_exc())
            
            def on_release(key):
                try:
                    # 移除释放的键
                    if key == keyboard.Key.cmd:
                        self.pressed_keys.discard('cmd')
                    elif hasattr(key, 'char') and key.char == '.':
                        self.pressed_keys.discard('.')
                except Exception as e:
                    print(f"❌ 处理按键释放事件失败: {e}")
                    print(traceback.format_exc())

            # 启动监听器
            self.keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
            self.keyboard_listener.daemon = True  # 设置为守护线程
            self.keyboard_listener.start()
            print("✓ 全局快捷键已注册: Command + .")
        except Exception as e:
            print(f"❌ 设置全局快捷键失败: {e}")
            print(traceback.format_exc())

    def _show_window_internal(self):
        """在主线程中显示窗口"""
        try:
            print("正在显示主窗口...")
            
            # 确保窗口可见
            if not self.main_window.isVisible():
                self.main_window.show()
            
            # 确保窗口不是最小化状态
            if self.main_window.isMinimized():
                self.main_window.showNormal()
            
            # 使用多重方法确保窗口在最前面
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()
            self.main_window.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
            
            # 在macOS上特别处理
            if sys.platform == 'darwin':
                # 临时设置窗口置顶来确保激活
                self.main_window.setWindowFlags(self.main_window.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
                self.main_window.show()
                # 短暂延迟后取消置顶
                QTimer.singleShot(300, self._remove_top_hint)
            
            print("✓ 窗口已显示并激活")
        except Exception as e:
            print(f"❌ 显示窗口失败: {e}")
            print(traceback.format_exc())
    
    def _remove_top_hint(self):
        """移除窗口置顶标志"""
        try:
            # 移除置顶标志
            self.main_window.setWindowFlags(self.main_window.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
            self.main_window.show()
            # 确保窗口仍然是激活的
            self.main_window.raise_()
            self.main_window.activateWindow()
        except Exception as e:
            print(f"❌ 移除窗口置顶失败: {e}")
            print(traceback.format_exc())
    
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

class MainApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        
        # 初始化组件
        self.state_manager = StateManager()
        self.audio_manager = AudioCaptureManager(self.state_manager)
        self.asr_engine = FunASREngine()
        self.clipboard_manager = ClipboardManager()
        self.hotkey_manager = HotkeyManager()
        
        # 创建主窗口
        self.main_window = MainWindow()
        self.main_window.set_state_manager(self.state_manager)
        
        # 连接信号
        self._connect_signals()
        
        # 设置窗口图标
        icon_path = os.path.join("resources", "icon.png")
        if os.path.exists(icon_path):
            self.main_window.setWindowIcon(QIcon(icon_path))
        
        print("应用程序就绪")
        
    def _connect_signals(self):
        """连接信号"""
        # 录音控制
        self.main_window.record_button_clicked.connect(self._toggle_recording)
        self.main_window.space_key_pressed.connect(self._toggle_recording)
        self.main_window.status_update_needed.connect(self.state_manager.update_status)
        
        # 历史记录点击
        self.main_window.history_item_clicked.connect(self._on_history_item_clicked)
        
        # 全局热键
        self.hotkey_manager.hotkey_triggered.connect(self._toggle_recording)
    
    def _toggle_recording(self):
        """切换录音状态"""
        if not self.state_manager.is_recording:
            self._start_recording()
        else:
            self._stop_recording()
    
    def _start_recording(self):
        """开始录音"""
        self.state_manager.start_recording()
        self.audio_manager.start_recording()
        self.main_window.record_button.setText("停止录音")
    
    def _stop_recording(self):
        """停止录音"""
        self.audio_manager.stop_recording()
        self.state_manager.stop_recording()
        self.main_window.record_button.setText("开始录音")
        
        # 处理录音数据
        audio_data = self.audio_manager.get_audio_data()
        if audio_data:
            text = self.asr_engine.transcribe(audio_data)
            if text:
                self._on_transcription_done(text)
    
    def _on_transcription_done(self, text):
        """处理转写结果"""
        if text.strip():
            self.main_window.display_result(text)
            self.clipboard_manager.copy_to_clipboard(text)
            print(f"✓ {text}")
    
    def _on_history_item_clicked(self, text):
        """处理历史记录点击"""
        self.clipboard_manager.copy_to_clipboard(text)
        self.clipboard_manager.paste_to_current_app()
        
    def exec(self):
        """运行应用程序"""
        self.main_window.show()
        return super().exec()

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