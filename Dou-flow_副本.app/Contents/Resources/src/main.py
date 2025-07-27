import sys
import traceback
import os
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox, QDialog
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
from config import APP_VERSION  # 从config导入版本号
import atexit
import multiprocessing
import logging
from datetime import datetime
from ui.settings_window import SettingsWindow
from settings_manager import SettingsManager

# 在文件开头添加日志配置
def setup_logging():
    """配置日志系统"""
    # 创建logs目录（如果不存在）
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 生成日志文件名（使用当前时间）
    log_filename = f"logs/app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # 配置日志
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logging.info(f"日志文件: {log_filename}")

# 应用信息
APP_NAME = "Dou-flow"  # 统一应用名称3
APP_AUTHOR = "ttmouse"
# 设置环境变量以隐藏系统日志
os.environ['QT_LOGGING_RULES'] = '*.debug=false;qt.qpa.*=false;qt.core.qobject.timer=false'
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
    start_recording_signal = pyqtSignal()
    stop_recording_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        # 初始化资源清理
        atexit.register(self.cleanup_resources)
        
        try:
            # 异步检查权限，避免阻塞启动
            if not getattr(sys, 'frozen', False):
                QTimer.singleShot(1000, self._check_development_permissions)  # 延迟1秒后检查权限
            
            self.app = QApplication(sys.argv)
            
            # 初始化设置管理器
            self.settings_manager = SettingsManager()
            
            # 设置应用程序属性
            if sys.platform == 'darwin':
                self.app.setAttribute(Qt.ApplicationAttribute.AA_DontShowIconsInMenus, False)
            
            # 设置应用程序信息
            self.app.setApplicationName(APP_NAME)
            self.app.setApplicationDisplayName(APP_NAME)
            
            # 加载应用图标
            icon_path = os.path.join(os.path.dirname(__file__), "..", "iconset.icns")
            app_icon = QIcon(icon_path)
            self.app.setWindowIcon(app_icon)
            self.app.setQuitOnLastWindowClosed(False)
            
            # 在 macOS 上设置 Dock 图标点击事件
            if sys.platform == 'darwin':
                self.app.setProperty("DOCK_CLICK_HANDLER", True)
                self.app.event = self.handle_mac_events
            
            # 创建系统托盘图标
            self.tray_icon = QSystemTrayIcon(app_icon, self.app)  # 使用相同的图标
            self.tray_icon.setToolTip("Dou-flow")  # 设置提示文本
            
            # 创建托盘菜单
            tray_menu = QMenu()
            
            # 显示窗口
            show_action = tray_menu.addAction("显示窗口")
            show_action.triggered.connect(self.show_window)
            
            # 添加设置菜单项
            settings_action = tray_menu.addAction("快捷键设置...")
            settings_action.triggered.connect(self.show_settings)
            
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
            
            # 延迟初始化FunASR引擎，避免阻塞启动
            print("准备初始化语音识别引擎...")
            self.funasr_engine = None
            
            # 使用定时器延迟初始化模型
            QTimer.singleShot(500, self._init_funasr_engine)
            
            # 初始化热键管理器，传入设置管理器
            self.hotkey_manager = HotkeyManager(self.settings_manager)
            self.clipboard_manager = ClipboardManager()
            self.context = Context()
            
            self.recording = False
            self.previous_volume = None
            
            # 初始化音频管理器
            self.audio_manager = AudioManager(self)
            
            # 预初始化 AudioCaptureThread
            self.audio_capture_thread = AudioCaptureThread(self.audio_capture)
            self.audio_capture_thread.audio_captured.connect(self.on_audio_captured)
            self.audio_capture_thread.recording_stopped.connect(self.stop_recording)
            
            # 连接信号
            self.show_window_signal.connect(self._show_window_internal)
            self.setup_connections()

        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            print(traceback.format_exc())
            sys.exit(1)

    def _check_development_permissions(self):
        """检查开发环境权限"""
        try:
            print("检查开发环境权限...")
            
            # 检查辅助功能权限
            accessibility_check = subprocess.run([
                'osascript',
                '-e', 'tell application "System Events"',
                '-e', 'set isEnabled to UI elements enabled',
                '-e', 'return isEnabled',
                '-e', 'end tell'
            ], capture_output=True, text=True)
            
            has_accessibility = 'true' in accessibility_check.stdout.lower()
            
            # 检查麦克风权限
            mic_check = subprocess.run([
                'osascript',
                '-e', 'tell application "System Events"',
                '-e', 'return "mic_check"',
                '-e', 'end tell'
            ], capture_output=True, text=True)
            
            # 如果能执行 AppleScript，说明有基本权限
            has_mic_access = 'mic_check' in mic_check.stdout
            
            missing_permissions = []
            if not has_accessibility:
                missing_permissions.append("辅助功能")
            
            if missing_permissions:
                print(f"⚠️  缺少权限: {', '.join(missing_permissions)}")
                print("\n快捷键录音功能需要以下权限：")
                print("\n【辅助功能权限】- 用于监听快捷键和自动粘贴")
                print("1. 打开 系统设置 > 隐私与安全性 > 辅助功能")
                print("2. 点击 '+' 按钮添加您的终端应用：")
                print("   - Terminal.app (系统终端)")
                print("   - iTerm.app (如果使用 iTerm)")
                print("   - PyCharm (如果使用 PyCharm)")
                print("   - VS Code (如果使用 VS Code)")
                print("3. 确保对应应用已勾选")
                print("\n【麦克风权限】- 用于录制音频")
                print("1. 打开 系统设置 > 隐私与安全性 > 麦克风")
                print("2. 确保您的终端应用已勾选")
                print("\n完成权限设置后，请重新运行程序")
                
                # 尝试打开系统设置
                try:
                    subprocess.run(['open', 'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'], check=False)
                    print("\n✓ 已尝试打开系统设置页面")
                except:
                    pass
                
                print("\n提示：打包后的应用 (bash tools/build_app.sh) 会自动请求权限")
                
                # 移除强制等待，让用户自己决定何时查看信息
                # import time
                # time.sleep(3)
            else:
                print("✓ 权限检查通过")
                
        except Exception as e:
            print(f"权限检查失败: {e}")
            print("如果快捷键无法正常工作，请手动检查系统权限设置")
    
    def _init_funasr_engine(self):
        """延迟初始化FunASR引擎"""
        try:
            print("开始初始化语音识别引擎...")
            self.funasr_engine = FunASREngine()
            
            # 连接模型加载信号
            self.funasr_engine.model_ready.connect(self._on_model_ready)
            self.funasr_engine.loading_progress.connect(self._on_loading_progress)
            self.funasr_engine.loading_error.connect(self._on_loading_error)
            
            # 更新设置中的模型路径
            model_paths = self.funasr_engine.get_model_paths()
            self.settings_manager.update_model_paths(model_paths)
            
            # 开始异步加载模型
            self.funasr_engine.start_async_loading()
            
        except Exception as e:
            print(f"❌ 初始化语音识别引擎失败: {e}")
            # 更新主窗口状态显示错误信息
            if hasattr(self, 'main_window'):
                self.main_window.update_status(f"❌ 语音识别引擎初始化失败")
    
    def _on_model_ready(self):
        """模型加载完成的回调"""
        print("✓ 语音识别模型加载完成，系统就绪")
        # 更新主窗口状态，显示模型已就绪
        if hasattr(self, 'main_window'):
            self.main_window.update_status("✓ 语音识别就绪")
        
        # 模型加载完成后，应用ASR相关设置
        try:
            if self.funasr_engine:  # 确保引擎已初始化
                model_path = self.settings_manager.get_setting('asr.model_path')
                if model_path and hasattr(self.funasr_engine, 'load_model'):
                    self.funasr_engine.load_model(model_path)
                
                punc_model_path = self.settings_manager.get_setting('asr.punc_model_path')
                if punc_model_path and hasattr(self.funasr_engine, 'load_punctuation_model'):
                    self.funasr_engine.load_punctuation_model(punc_model_path)
                
                print("✓ ASR设置已应用")
            else:
                print("⚠️ 语音识别引擎尚未初始化，ASR设置将在引擎就绪后应用")
        except Exception as e:
            print(f"❌ 应用ASR设置失败: {e}")
    
    def _on_loading_progress(self, message):
        """模型加载进度的回调"""
        print(f"模型加载: {message}")
        # 更新主窗口状态显示加载进度
        if hasattr(self, 'main_window'):
            self.main_window.update_status(f"🔄 {message}")
    
    def _on_loading_error(self, error_message):
        """模型加载错误的回调"""
        print(f"模型加载错误: {error_message}")
        # 更新主窗口状态显示错误信息
        if hasattr(self, 'main_window'):
            self.main_window.update_status(f"❌ 模型加载失败")

    def cleanup_resources(self):
        """清理资源"""
        try:
            print("开始清理资源...")
            
            # 停止录音（如果正在录音）
            if hasattr(self, 'recording') and self.recording:
                self.recording = False
                print("✓ 停止录音状态")
            
            # 停止并清理定时器
            if hasattr(self, 'recording_timer'):
                try:
                    if self.recording_timer.isActive():
                        self.recording_timer.stop()
                    self.recording_timer.deleteLater()
                    print("✓ 录音定时器已清理")
                except Exception as e:
                    print(f"⚠️ 清理录音定时器失败: {e}")
            
            # 恢复系统音量（如果有保存的音量）
            if hasattr(self, 'previous_volume') and self.previous_volume is not None:
                try:
                    self._set_system_volume(self.previous_volume)
                    print("✓ 系统音量已恢复")
                except Exception as e:
                    print(f"⚠️ 恢复系统音量失败: {e}")
            
            # 安全停止音频捕获线程
            if hasattr(self, 'audio_capture_thread') and self.audio_capture_thread:
                try:
                    if self.audio_capture_thread.isRunning():
                        print("正在停止音频捕获线程...")
                        self.audio_capture_thread.stop()
                        # 线程的stop方法已经包含了wait逻辑
                    print("✓ 音频捕获线程已停止")
                except Exception as e:
                    print(f"⚠️ 停止音频捕获线程失败: {e}")
            
            # 安全停止转写线程
            if hasattr(self, 'transcription_thread') and self.transcription_thread:
                try:
                    if self.transcription_thread.isRunning():
                        print("正在停止转写线程...")
                        # 使用新的stop方法，它包含了完整的停止逻辑
                        if hasattr(self.transcription_thread, 'stop'):
                            self.transcription_thread.stop()
                        else:
                            # 兼容旧版本
                            self.transcription_thread.quit()
                            if not self.transcription_thread.wait(2000):  # 等待2秒
                                print("⚠️ 转写线程未能正常结束，强制终止")
                                self.transcription_thread.terminate()
                                self.transcription_thread.wait(1000)
                    print("✓ 转写线程已停止")
                except Exception as e:
                    print(f"⚠️ 停止转写线程失败: {e}")
            
            # 清理音频资源
            if hasattr(self, 'audio_capture'):
                try:
                    if hasattr(self.audio_capture, 'cleanup'):
                        self.audio_capture.cleanup()
                    print("✓ 音频捕获资源已清理")
                except Exception as e:
                    print(f"⚠️ 清理音频捕获资源失败: {e}")
            
            # 停止热键监听
            if hasattr(self, 'hotkey_manager'):
                try:
                    self.hotkey_manager.stop_listening()
                    print("✓ 热键监听已停止")
                except Exception as e:
                    print(f"⚠️ 停止热键监听失败: {e}")
            
            # 清理状态管理器
            if hasattr(self, 'state_manager'):
                try:
                    if hasattr(self.state_manager, 'cleanup'):
                        self.state_manager.cleanup()
                    print("✓ 状态管理器已清理")
                except Exception as e:
                    print(f"⚠️ 清理状态管理器失败: {e}")
            
            # 清理FunASR引擎
            if hasattr(self, 'funasr_engine') and self.funasr_engine:
                try:
                    if hasattr(self.funasr_engine, 'cleanup'):
                        self.funasr_engine.cleanup()
                    print("✓ FunASR引擎已清理")
                except Exception as e:
                    print(f"⚠️ 清理FunASR引擎失败: {e}")
            
            print("✓ 资源清理完成")
            
        except Exception as e:
            print(f"❌ 资源清理过程中出错: {e}")
            import traceback
            print(traceback.format_exc())

    def closeEvent(self, event):
        """处理关闭事件"""
        self.cleanup_resources()
        super().closeEvent(event)

    def _set_system_volume(self, volume):
        """设置系统音量
        volume: 0-100 的整数，或者 None 表示静音"""
        try:
            if volume is None:
                # 直接静音，不检查当前状态以减少延迟
                subprocess.run([
                    'osascript',
                    '-e', 'set volume output muted true'
                ], check=True)
                print("系统已静音")
            else:
                # 设置音量并取消静音
                volume = max(0, min(100, volume))  # 确保音量在 0-100 范围内
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
            # 检查模型是否准备就绪
            if not self.funasr_engine.is_model_ready():
                print("⚠️ 语音识别模型尚未加载完成，请稍后重试")
                self.update_ui_signal.emit("⚠️ 模型加载中，请稍后重试", "")
                return
            
            self.recording = True
            
            try:
                # 先播放音效，让用户立即听到反馈
                self.state_manager.start_recording()
                
                # 然后保存当前音量并静音系统
                self.previous_volume = self._get_system_volume()
                if self.previous_volume is not None:
                    self._set_system_volume(None)  # 静音
                
                # 重新初始化录音线程（如果之前已经使用过）
                if self.audio_capture_thread.isFinished():
                    self.audio_capture_thread = AudioCaptureThread(self.audio_capture)
                    self.audio_capture_thread.audio_captured.connect(self.on_audio_captured)
                    self.audio_capture_thread.recording_stopped.connect(self.stop_recording)
                
                # 启动录音线程
                self.audio_capture_thread.start()
                
                # 清理之前的定时器
                if hasattr(self, 'recording_timer') and self.recording_timer:
                    try:
                        if self.recording_timer.isActive():
                            self.recording_timer.stop()
                        self.recording_timer.deleteLater()
                        self.recording_timer = None
                    except Exception as e:
                        print(f"⚠️ 清理旧定时器失败: {e}")
                
                # 创建新的录音定时器
                max_duration = self.settings_manager.get_setting('audio.max_recording_duration', 10)
                try:
                    self.recording_timer = QTimer(self)
                    self.recording_timer.setSingleShot(True)
                    self.recording_timer.timeout.connect(self._auto_stop_recording)
                    self.recording_timer.start(max_duration * 1000)  # 转换为毫秒
                    print(f"✓ 录音开始，将在{max_duration}秒后自动停止")
                except Exception as e:
                    print(f"⚠️ 创建录音定时器失败: {e}")
                    # 即使定时器创建失败，录音仍可以手动停止
                
            except Exception as e:
                error_msg = f"开始录音时出错: {str(e)}"
                print(error_msg)
                self.update_ui_signal.emit(f"❌ {error_msg}", "")

    def stop_recording(self):
        """停止录音"""
        if self.recording:
            self.recording = False
            
            # 安全停止定时器
            if hasattr(self, 'recording_timer') and self.recording_timer:
                try:
                    if self.recording_timer.isActive():
                        self.recording_timer.stop()
                    print("✓ 录音定时器已停止")
                except Exception as e:
                    print(f"⚠️ 停止录音定时器失败: {e}")
            
            # 安全停止音频捕获线程
            try:
                if hasattr(self, 'audio_capture_thread') and self.audio_capture_thread:
                    if self.audio_capture_thread.isRunning():
                        self.audio_capture_thread.stop()
                        # stop方法已经包含了wait逻辑
                    print("✓ 音频捕获线程已停止")
            except Exception as e:
                print(f"⚠️ 停止音频捕获线程失败: {e}")
                return  # 如果线程停止失败，不继续后续操作
            
            # 临时恢复音量以确保音效能正常播放
            if self.previous_volume is not None:
                self._set_system_volume(self.previous_volume)
                # 添加短暂延迟，确保音量恢复完成
                import time
                time.sleep(0.1)
            
            # 播放停止音效
            self.state_manager.stop_recording()
            
            # 重置 previous_volume
            self.previous_volume = None
            
            try:
                audio_data = self.audio_capture.get_audio_data()
                
                if len(audio_data) > 0:
                    # 检查语音识别引擎是否已初始化
                    if self.funasr_engine is None:
                        print("⚠️ 语音识别引擎尚未初始化，请稍后重试")
                        self.update_ui_signal.emit("⚠️ 语音识别引擎正在初始化，请稍后重试", "")
                        return
                    
                    # 检查模型是否已加载
                    if not self.funasr_engine.is_model_ready():
                        print("⚠️ 语音识别模型正在加载中，请稍后重试")
                        self.update_ui_signal.emit("⚠️ 语音识别模型正在加载中，请稍后重试", "")
                        return
                    
                    self.transcription_thread = TranscriptionThread(audio_data, self.funasr_engine)
                    self.transcription_thread.transcription_done.connect(self.on_transcription_done)
                    self.transcription_thread.start()
                else:
                    print("❌ 未检测到声音")
                    self.update_ui_signal.emit("❌ 未检测到声音", "")
            except Exception as e:
                print(f"❌ 录音失败: {e}")
                self.update_ui_signal.emit(f"❌ 录音失败: {e}", "")
    
    def _auto_stop_recording(self):
        """定时器触发的自动停止录音"""
        print(f"⏰ 定时器触发！当前录音状态: {self.recording}")
        if self.recording:
            print("⏰ 录音时间达到10秒，自动停止录音")
            self.stop_recording()
        else:
            print("⏰ 定时器触发，但当前未在录音状态")

    def cleanup(self):
        """清理资源"""
        try:
            # 停止录音定时器
            if hasattr(self, 'recording_timer') and self.recording_timer.isActive():
                self.recording_timer.stop()
            
            self.audio_capture.clear_recording_data()
            
            # 安全停止转写线程
            if hasattr(self, 'transcription_thread') and self.transcription_thread:
                if self.transcription_thread.isRunning():
                    # 使用新的stop方法
                    if hasattr(self.transcription_thread, 'stop'):
                        self.transcription_thread.stop()
                    else:
                        # 兼容旧版本
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
        # 连接录音信号，确保在主线程中执行
        self.start_recording_signal.connect(self.start_recording)
        self.stop_recording_signal.connect(self.stop_recording)
        # 连接退出请求信号
        self.main_window.quit_requested.connect(self.quit_application)

    def toggle_recording(self):
        """切换录音状态"""
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()

    def on_option_press(self):
        """处理Control键按下事件"""
        if not self.recording:
            print("✓ Control 键按下，开始录音")
            # 使用信号确保在主线程中执行
            self.start_recording_signal.emit()
        else:
            print("⚠️ Control 键按下，但已经在录音中")

    def on_option_release(self):
        """处理Control键释放事件"""
        if self.recording:
            print("✓ Control 键释放，停止录音")
            # 使用信号确保在主线程中执行
            self.stop_recording_signal.emit()
        else:
            print("⚠️ Control 键释放，但未在录音中")

    def on_audio_captured(self, data):
        """音频数据捕获回调"""
        # 录音过程中不需要频繁更新状态，因为状态已经在start_recording时设置了
        pass

    def quit_application(self):
        """安全退出应用程序"""
        try:
            print("正在退出应用程序...")
            
            # 先清理资源
            self.cleanup_resources()
            
            # 隐藏托盘图标
            if hasattr(self, 'tray_icon'):
                self.tray_icon.hide()
            
            # 关闭所有窗口
            if hasattr(self, 'main_window'):
                self.main_window.close()
            
            if hasattr(self, 'settings_window'):
                self.settings_window.close()
            
            # 延迟退出应用，确保所有清理工作完成
            QTimer.singleShot(100, self._force_quit)
            
        except Exception as e:
            print(f"❌ 退出应用程序时出错: {e}")
            # 强制退出
            self._force_quit()
    
    def _force_quit(self):
        """强制退出应用程序"""
        try:
            if hasattr(self, 'app'):
                self.app.quit()
            print("✓ 应用程序已退出")
        except Exception as e:
            print(f"❌ 强制退出失败: {e}")
            import sys
            sys.exit(0)

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
            # 立即显示主窗口，不等待模型加载
            print("✓ 界面启动完成，模型正在后台加载...")
            # 显示主窗口
            self.main_window.show()
            
            # 异步应用初始设置（避免阻塞界面显示）
            QTimer.singleShot(100, self.apply_settings)
            
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

    def show_settings(self):
        """显示设置窗口"""
        if not hasattr(self, 'settings_window'):
            self.settings_window = SettingsWindow(
                settings_manager=self.settings_manager,
                audio_capture=self.audio_capture
            )
            self.settings_window.settings_saved.connect(self.apply_settings)
        
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def apply_settings(self):
        """应用设置"""
        try:
            # 应用热键设置
            current_hotkey = self.settings_manager.get_hotkey()
            self.hotkey_manager.stop_listening()  # 先停止监听
            self.hotkey_manager.update_hotkey(current_hotkey)  # 更新热键
            self.hotkey_manager.start_listening()  # 重新开始监听
            
            # 应用音频设置
            volume_threshold = self.settings_manager.get_setting('audio.volume_threshold')
            self.audio_capture.set_volume_threshold(volume_threshold)
            
            # ASR设置只在模型准备好后应用
            if self.funasr_engine and self.funasr_engine.is_model_ready():
                # 应用ASR设置
                model_path = self.settings_manager.get_setting('asr.model_path')
                if model_path and hasattr(self.funasr_engine, 'load_model'):
                    self.funasr_engine.load_model(model_path)
                
                punc_model_path = self.settings_manager.get_setting('asr.punc_model_path')
                if punc_model_path and hasattr(self.funasr_engine, 'load_punctuation_model'):
                    self.funasr_engine.load_punctuation_model(punc_model_path)
            else:
                print("⚠️ 语音识别引擎或模型尚未加载完成，ASR设置将在就绪后应用")
            
            print("✓ 设置已应用")
        except Exception as e:
            print(f"❌ 应用设置失败: {e}")

def signal_handler(signum, frame):
    """处理系统信号"""
    print(f"\n收到信号 {signum}，正在安全退出...")
    if 'app_instance' in globals():
        app_instance.cleanup_resources()
    sys.exit(0)

if __name__ == "__main__":
    setup_logging()  # 初始化日志系统
    logging.info("应用程序启动")
    
    # 注册信号处理器
    import signal
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # 终止信号
    
    app_instance = None
    try:
        print("正在创建应用程实例...")
        app_instance = Application()
        print("应用程序实例已创建，正在运行...")
        sys.exit(app_instance.run())
    except KeyboardInterrupt:
        print("\n用户中断程序")
        if app_instance:
            app_instance.cleanup_resources()
        sys.exit(0)
    except Exception as e:
        print(f"运行应用程序时出错: {e}")
        print(traceback.format_exc())
        if app_instance:
            app_instance.cleanup_resources()
        sys.exit(1)