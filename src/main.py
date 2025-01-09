import sys
import traceback
import os
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
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
import subprocess
from audio_manager import AudioManager

# 应用信息
APP_NAME = "Dou-flow"  # 统一应用名称3
APP_VERSION = "1.0.0"
APP_AUTHOR = "ttmouse"
# 设置环境变量以隐藏系统1
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
            self.app.setWindowIcon(QIcon("icon_1024.png"))
            self.app.setQuitOnLastWindowClosed(False)
            
            # 在 macOS 上设置 Dock 图标点击事件
            if sys.platform == 'darwin':
                self.app.setProperty("DOCK_CLICK_HANDLER", True)
                self.app.event = self.handle_mac_events
            
            # 创建系统托盘图标1
            self.tray_icon = QSystemTrayIcon(QIcon(os.path.join(os.path.dirname(__file__), "..", "resources", "mic1.png")), self.app)
            self.tray_icon.setToolTip("Dou-flow")  # 设置提示文本
            
            # 创建托盘菜单
            tray_menu = QMenu()
            
            # 显示窗口
            show_action = tray_menu.addAction("显示窗口")
            show_action.triggered.connect(self.show_window)
            
            # 编辑热词
            edit_hotwords_action = tray_menu.addAction("编辑热词...")
            edit_hotwords_action.triggered.connect(lambda: self.main_window.show_hotwords_window())
            
            # 检查权限
            check_permissions_action = tray_menu.addAction("检查权限")
            check_permissions_action.triggered.connect(self.check_permissions)
            
            # 分隔线
            tray_menu.addSeparator()
            
            # 退出
            quit_action = tray_menu.addAction("退出")
            quit_action.triggered.connect(self.quit_application)
            
            # 设置托盘图标的菜单
            self.tray_icon.setContextMenu(tray_menu)
            # 移除托盘图标的点击事件连接
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
            self.context = Context()
            
            self.recording = False
            self.previous_volume = None  # 保存之前的音量设置
            
            # 初始化音频管理器
            self.audio_manager = AudioManager(self)  # 传入 self 作为父对象
            
            # 连接信号1
            self.show_window_signal.connect(self._show_window_internal)
            self.setup_connections()

        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            print(traceback.format_exc())
            sys.exit(1)

    def _set_system_volume(self, volume):
        """设置系统音量
        volume: 0-100 的整数，或者 None 表示静音"""
        try:
            if volume is None:
                # 检查当前是否已经静音
                result = subprocess.run([
                    'osascript',
                    '-e', 'get volume settings'
                ], capture_output=True, text=True)
                if "output muted:true" in result.stdout:
                    print("系统已经处于静音状态")
                    return
                
                # 静音所有音频输出
                subprocess.run([
                    'osascript',
                    '-e', 'set volume output muted true'
                ], check=True)
                print("系统已静音")
            else:
                # 设置音量并取消静音
                volume = max(0, min(100, volume))  # 确保音量在 0-100 范围内
                # 将 0-100 的音量转换为 0-7 的范围（macOS 使用 0-7 的音量范围）
                mac_volume = int((volume / 100.0) * 7)
                subprocess.run([
                    'osascript',
                    '-e', f'set volume output volume {volume}',
                    '-e', 'set volume output muted false'
                ], check=True)
                print(f"系统音量已设置为: {volume}")
        except subprocess.CalledProcessError as e:
            print(f"❌ 设置系统音量失败: {e}")
        except Exception as e:
            print(f"❌ 设置系统音量时发生错误: {e}")

    def _get_system_volume(self):
        """获取当前系统音量"""
        try:
            # 获取完整的音量设置
            result = subprocess.run([
                'osascript',
                '-e', 'get volume settings'
            ], capture_output=True, text=True, check=True)
            
            settings = result.stdout.strip()
            # 解析输出，格式类似：output volume:50, input volume:75, alert volume:75, output muted:false
            volume_str = settings.split(',')[0].split(':')[1].strip()
            muted = "output muted:true" in settings
            
            if muted:
                print("系统当前处于静音状态")
                return 0
            
            volume = int(volume_str)
            print(f"当前系统音量: {volume}")
            return volume
        except subprocess.CalledProcessError as e:
            print(f"❌ 获取系统音量失败: {e}")
            return None
        except Exception as e:
            print(f"❌ 获取系统音量时发生错误: {e}")
            return None

    def start_recording(self):
        """开始录音"""
        if not self.recording:
            self.recording = True
            
            try:
                # 暂停其他应用的音频（替换原来的音量控制代码）
                self.audio_manager.mute_other_apps()
                
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
                # 恢复其他应用的音频（替换原来的音量控制代码）
                self.audio_manager.resume_other_apps()
                
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
        except Exception as e:
            print(f"❌ 清理资源失败: {e}")

    @pyqtSlot()
    def show_window(self):
        """显示主窗口（可以从其他线程调用）"""
        # 如果在主线程中，直接调用
        if QThread.currentThread() == QApplication.instance().thread():
            self._show_window_internal()
        else:
            # 在其他线程中，使用信号
            self.show_window_signal.emit()

    def setup_connections(self):
        """设置信号连接"""
        self.hotkey_manager.set_press_callback(self.on_option_press)
        self.hotkey_manager.set_release_callback(self.on_option_release)
        self.update_ui_signal.connect(self.update_ui)
        self.main_window.record_button_clicked.connect(self.toggle_recording)
        self.main_window.history_item_clicked.connect(self.on_history_item_clicked)
        self.state_manager.status_changed.connect(self.main_window.update_status)
        # 连接窗口显示信号
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
            print("✓ Option 键按下，开始录音")
            self.start_recording()
        else:
            print("⚠️ Option 键按下，但已经在录音中")

    def on_option_release(self):
        """处理Option键释放事件"""
        if self.recording:
            print("✓ Option 键释放，停止录音")
            self.stop_recording()
        else:
            print("⚠️ Option 键释放，但未在录音中")

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
            # 在 macOS 上使用 NSWindow 来激活窗口
            if sys.platform == 'darwin':
                try:
                    from AppKit import NSApplication, NSWindow
                    # 获取应用和窗口
                    app = NSApplication.sharedApplication()
                    window = self.main_window.windowHandle().nativeHandle()
                    
                    # 显示窗口
                    if not self.main_window.isVisible():
                        self.main_window.show()
                    
                    # 设置窗口级别为浮动窗口并激活
                    window.setLevel_(NSWindow.FloatingWindowLevel)
                    window.makeKeyAndOrderFront_(None)
                    app.activateIgnoringOtherApps_(True)
                    
                    # 恢复正常窗口级别
                    QTimer.singleShot(100, lambda: (
                        window.setLevel_(NSWindow.NormalWindowLevel),
                        self.main_window.raise_(),
                        self.main_window.activateWindow()
                    ))
                    
                except Exception as e:
                    print(f"激活窗口时出错: {e}")
                    # 如果原生方法失败，使用 Qt 方法
                    self.main_window.show()
                    self.main_window.raise_()
                    self.main_window.activateWindow()
            else:
                # 非 macOS 系统的处理
                if not self.main_window.isVisible():
                    self.main_window.show()
                self.main_window.raise_()
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
            # 2. 更新UI并添加到历史记录（无论窗口是否可见）
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

    def check_permissions(self):
        """检查应用权限状态"""
        try:
            # 检查麦克风权限
            mic_status = subprocess.run([
                'osascript',
                '-e', 'tell application "System Events" to tell process "SystemUIServer"',
                '-e', 'get value of first menu bar item of menu bar 1 whose description contains "麦克风"',
                '-e', 'end tell'
            ], capture_output=True, text=True)
            
            # 检查辅助功能权限
            accessibility_status = subprocess.run([
                'osascript',
                '-e', 'tell application "System Events"',
                '-e', 'set isEnabled to UI elements enabled',
                '-e', 'return isEnabled',
                '-e', 'end tell'
            ], capture_output=True, text=True)
            
            # 检查自动化权限
            automation_status = subprocess.run([
                'osascript',
                '-e', 'tell application "System Events"',
                '-e', 'return "已授权"',
                '-e', 'end tell'
            ], capture_output=True, text=True)
            
            # 准备状态消息
            status_msg = "权限状态：\n\n"
            status_msg += f"麦克风：{'已授权' if '1' in mic_status.stdout else '未授权'}\n"
            status_msg += f"辅助功能：{'已授权' if 'true' in accessibility_status.stdout.lower() else '未授权'}\n"
            status_msg += f"自动化：{'已授权' if '已授权' in automation_status.stdout else '未授权'}\n\n"
            
            if '未授权' in status_msg:
                status_msg += "请在系统设置中授予以下权限：\n"
                status_msg += "1. 系统设置 > 隐私与安全性 > 麦克风\n"
                status_msg += "2. 系统设置 > 隐私与安全性 > 辅助功能\n"
                status_msg += "3. 系统设置 > 隐私与安全性 > 自动化"
            
            # 显示状态
            msg_box = QMessageBox()
            msg_box.setWindowTitle("权限检查")
            msg_box.setText(status_msg)
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.exec()
        except Exception as e:
            msg_box = QMessageBox()
            msg_box.setWindowTitle("权限检查失败")
            msg_box.setText(f"检查权限时出错：{str(e)}")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.exec()

    def handle_mac_events(self, event):
        """处理 macOS 特定事件"""
        try:
            # 处理 Dock 图标点击事件
            if event.type() == 214:  # Qt.Type.ApplicationStateChange
                # 使用与状态栏菜单相同的方法
                if QThread.currentThread() == QApplication.instance().thread():
                    self._show_window_internal()
                else:
                    self.show_window_signal.emit()
                return True
            return QApplication.event(self.app, event)
        except Exception as e:
            print(f"❌ 处理 macOS 事件失败: {e}")
            return False

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