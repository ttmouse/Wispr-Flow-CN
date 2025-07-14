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

def clean_html_tags(text):
    """清理HTML标签，返回纯文本"""
    if not text:
        return text
    # 移除HTML标签
    clean_text = re.sub(r'<[^>]+>', '', text)
    # 解码HTML实体
    clean_text = clean_text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"').replace('&#39;', "'")
    return clean_text
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
            
            # 初始化基础组件
            self.state_manager = StateManager()
            self.main_window = MainWindow(app_instance=self)
            self.main_window.set_state_manager(self.state_manager)
            
            # 初始化基础音频组件
            self.audio_capture = AudioCapture()
            
            # 初始化状态变量
            self.recording = False
            self.previous_volume = None
            self._pending_paste_text = None  # 用于延迟粘贴的文本
            self.funasr_engine = None  # 延迟初始化
            self.hotkey_manager = None  # 延迟初始化
            self.clipboard_manager = None  # 延迟初始化
            self.context = None  # 延迟初始化
            self.audio_manager = None  # 延迟初始化
            self.audio_capture_thread = None  # 延迟初始化
            
            # 连接信号
            self.show_window_signal.connect(self._show_window_internal)
            
            # 显示主窗口
            self.main_window.show()
            print("✓ 主界面已启动")
            
            # 启动后台初始化
            self._start_background_initialization()

        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            print(traceback.format_exc())
            sys.exit(1)
    
    def _start_background_initialization(self):
        """启动后台初始化任务"""
        from PyQt6.QtCore import QTimer
        
        # 使用异步初始化，避免阻塞主线程
        self._init_step = 0
        self._init_timer = QTimer()
        self._init_timer.setSingleShot(True)
        self._init_timer.timeout.connect(self._async_initialization_step)
        self._init_timer.start(100)  # 100ms后开始后台初始化
    
    def _async_initialization_step(self):
        """异步初始化步骤，避免阻塞主线程"""
        try:
            if self._init_step == 0:
                # 步骤1：检查权限
                try:
                    if not getattr(sys, 'frozen', False):
                        if self.settings_manager.is_cache_expired('permissions'):
                            self.main_window.update_loading_status("正在检查权限...")
                            print("正在检查权限...")
                            self._check_development_permissions()
                            print("✓ 权限检查完成")
                        else:
                            print("✓ 权限缓存有效，跳过检查")
                            cache = self.settings_manager.get_permissions_cache()
                            if not cache['accessibility'] or not cache['microphone']:
                                print("⚠️  缓存显示权限可能不完整，建议检查系统设置")
                except Exception as e:
                    print(f"⚠️  权限检查失败: {e}")
                    # 权限检查失败不应阻止程序继续运行
                self._init_step = 1
                self._init_timer.start(50)  # 50ms后执行下一步
                
            elif self._init_step == 1:
                # 步骤2：初始化语音识别引擎
                try:
                    if self.settings_manager.is_cache_expired('models'):
                        self.main_window.update_loading_status("正在加载语音识别模型...")
                        print("正在加载语音识别模型...")
                        try:
                            self.funasr_engine = FunASREngine(self.settings_manager)
                            model_paths = self.funasr_engine.get_model_paths()
                            self.settings_manager.update_model_paths(model_paths)
                            asr_available = bool(model_paths.get('asr_model_path'))
                            punc_available = bool(model_paths.get('punc_model_path'))
                            self.settings_manager.update_models_cache(asr_available, punc_available)
                            print("✓ 语音识别就绪")
                        except Exception as e:
                            print(f"❌ 模型加载失败: {e}")
                            self.settings_manager.update_models_cache(False, False)
                            self.funasr_engine = None
                    else:
                        print("✓ 模型缓存有效，跳过加载")
                        cache = self.settings_manager.get_models_cache()
                        if cache['asr_available']:
                            try:
                                self.funasr_engine = FunASREngine(self.settings_manager)
                                print("✓ 基于缓存快速初始化语音识别")
                            except Exception as e:
                                print(f"⚠️  缓存显示模型可用但初始化失败: {e}")
                                self.funasr_engine = None
                                self.settings_manager.update_models_cache(False, False)
                        else:
                            print("⚠️  缓存显示模型不可用")
                            self.funasr_engine = None
                except Exception as e:
                    print(f"⚠️  语音识别引擎初始化失败: {e}")
                    self.funasr_engine = None
                self._init_step = 2
                self._init_timer.start(50)  # 50ms后执行下一步
                
            elif self._init_step == 2:
                # 步骤3：初始化其他组件
                try:
                    self.main_window.update_loading_status("正在初始化组件...")
                    
                    # 安全初始化各个组件
                    try:
                        self.hotkey_manager = HotkeyManager(self.settings_manager)
                    except Exception as e:
                        print(f"⚠️  热键管理器初始化失败: {e}")
                        self.hotkey_manager = None
                    
                    try:
                        self.clipboard_manager = ClipboardManager()
                    except Exception as e:
                        print(f"⚠️  剪贴板管理器初始化失败: {e}")
                        self.clipboard_manager = None
                    
                    try:
                        self.context = Context()
                    except Exception as e:
                        print(f"⚠️  上下文管理器初始化失败: {e}")
                        self.context = None
                    
                    try:
                        self.audio_manager = AudioManager(self)
                    except Exception as e:
                        print(f"⚠️  音频管理器初始化失败: {e}")
                        self.audio_manager = None
                    
                    # 预初始化 AudioCaptureThread
                    try:
                        self.audio_capture_thread = AudioCaptureThread(self.audio_capture)
                        self.audio_capture_thread.audio_captured.connect(self.on_audio_captured)
                        self.audio_capture_thread.recording_stopped.connect(self.stop_recording)
                    except Exception as e:
                        print(f"⚠️  音频捕获线程初始化失败: {e}")
                        self.audio_capture_thread = None
                        
                except Exception as e:
                    print(f"⚠️  组件初始化过程中出现错误: {e}")
                
                self._init_step = 3
                self._init_timer.start(50)  # 50ms后执行下一步
                
            elif self._init_step == 3:
                # 步骤4：设置连接和应用设置
                try:
                    self.setup_connections()
                    self.apply_settings()
                except Exception as e:
                    print(f"⚠️  设置连接和应用设置失败: {e}")
                self._init_step = 4
                self._init_timer.start(50)  # 50ms后执行下一步
                
            elif self._init_step == 4:
                # 步骤5：完成初始化
                self.main_window.update_loading_status("初始化完成")
                self._init_step = 5
                self._init_timer.start(1000)  # 1秒后清除状态
                
            elif self._init_step == 5:
                # 步骤6：清除加载状态
                self.main_window.update_loading_status("")
                print("✓ 所有组件初始化完成")
                self._init_step = -1  # 标记完成
                
        except Exception as e:
            print(f"❌ 初始化步骤 {self._init_step} 发生严重错误: {e}")
            import traceback
            print(traceback.format_exc())
            self.main_window.update_loading_status("初始化失败")
            self._init_step = -1  # 标记完成（即使失败）
            # 2秒后清除错误状态
            QTimer.singleShot(2000, self._clear_error_status)

    def _clear_error_status(self):
        """清除错误状态"""
        try:
            self.main_window.update_loading_status("")
        except Exception as e:
            print(f"清除错误状态失败: {e}")

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
                
                # 给用户一些时间查看信息
                import time
                time.sleep(3)
            else:
                print("✓ 权限检查通过")
            
            # 更新权限缓存
            self.settings_manager.update_permissions_cache(has_accessibility, has_mic_access)
                
        except Exception as e:
            print(f"权限检查失败: {e}")
            print("如果快捷键无法正常工作，请手动检查系统权限设置")
            # 权限检查失败时也更新缓存，避免重复检查
            self.settings_manager.update_permissions_cache(False, False)

    def cleanup_resources(self):
        """清理资源"""
        try:
            # 恢复系统音量（如果有保存的音量）
            if hasattr(self, 'previous_volume') and self.previous_volume is not None:
                self._set_system_volume(self.previous_volume)
                print("✓ 系统音量已恢复")
            
            # 停止所有线程
            if hasattr(self, 'audio_capture_thread') and self.audio_capture_thread:
                self.audio_capture_thread.stop()
                self.audio_capture_thread.wait()
            
            if hasattr(self, 'transcription_thread') and self.transcription_thread:
                if self.transcription_thread.isRunning():
                    self.transcription_thread.terminate()
                    self.transcription_thread.wait()
            
            # 清理音频资源
            if hasattr(self, 'audio_capture'):
                self.audio_capture.cleanup()
            
            # 清理FunASR引擎资源
            if hasattr(self, 'funasr_engine') and self.funasr_engine:
                self.funasr_engine.cleanup()
            
            # 清理热键管理器资源
            if hasattr(self, 'hotkey_manager') and self.hotkey_manager:
                self.hotkey_manager.cleanup()
            
            # 清理其他资源
            if hasattr(self, 'state_manager'):
                self.state_manager.cleanup()
            
            # 清理多进程资源
            try:
                import multiprocessing
                multiprocessing.current_process()._clean()
            except Exception as e:
                print(f"❌ 清理多进程资源失败: {e}")
            
            print("✓ 资源清理完成")
        except Exception as e:
            print(f"❌ 资源清理失败: {e}")
        finally:
            # 确保关键资源被清理识别到了吗？
            try:
                if hasattr(self, 'app'):
                    self.app.quit()
            except Exception as e:
                print(f"❌ 应用退出失败: {e}")

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
        # 检查必要组件是否已初始化
        if not self.audio_capture_thread:
            print("⚠️ 录音功能尚未就绪，请稍后再试")
            return
            
        if not self.recording:
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
                
                # 从设置中获取录音时长并设置定时器，自动停止录音
                if hasattr(self, 'recording_timer'):
                    self.recording_timer.stop()
                    self.recording_timer.deleteLater()
                
                # 确保定时器在主线程中创建，设置parent为self
                max_duration = self.settings_manager.get_setting('audio.max_recording_duration', 10)
                self.recording_timer = QTimer(self)
                self.recording_timer.setSingleShot(True)
                self.recording_timer.timeout.connect(self._auto_stop_recording)
                self.recording_timer.start(max_duration * 1000)  # 转换为毫秒
                print(f"✓ 录音开始，将在{max_duration}秒后自动停止 (定时器ID: {id(self.recording_timer)})")
                print(f"✓ 定时器状态: active={self.recording_timer.isActive()}, interval={self.recording_timer.interval()}ms")
                
            except Exception as e:
                error_msg = f"开始录音时出错: {str(e)}"
                print(error_msg)
                self.update_ui_signal.emit(f"❌ {error_msg}", "")

    def stop_recording(self):
        """停止录音"""
        if self.recording:
            self.recording = False
            
            # 停止定时器
            if hasattr(self, 'recording_timer') and self.recording_timer.isActive():
                self.recording_timer.stop()
            
            # 检查录音线程是否存在
            if self.audio_capture_thread:
                self.audio_capture_thread.stop()
                self.audio_capture_thread.wait()
            
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
                    if not self.funasr_engine:
                        print("⚠️ 语音识别引擎尚未就绪，无法处理录音")
                        self.update_ui_signal.emit("⚠️ 语音识别引擎尚未就绪，无法处理录音", "")
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
            
            # 清理设置窗口
            if hasattr(self, 'settings_window') and self.settings_window:
                try:
                    # 断开信号连接
                    self.settings_window.settings_saved.disconnect()
                    # 关闭窗口
                    self.settings_window.close()
                    self.settings_window = None
                    print("✓ 设置窗口已清理")
                except Exception as e:
                    print(f"⚠️ 清理设置窗口失败: {e}")
            
            if hasattr(self, 'audio_capture') and self.audio_capture:
                self.audio_capture.clear_recording_data()
                
            if hasattr(self, 'transcription_thread'):
                self.transcription_thread.quit()
                self.transcription_thread.wait()
                
            if hasattr(self, 'hotkey_manager') and self.hotkey_manager:
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
        if self.hotkey_manager:
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
        """退出应用程序"""
        self.cleanup()
        self.app.quit()

    def _restore_window_level(self):
        """恢复窗口正常级别"""
        try:
            if sys.platform == 'darwin':
                from AppKit import NSApplication, NSWindow
                app = NSApplication.sharedApplication()
                window = self.main_window.windowHandle().nativeHandle()
                if window:
                    window.setLevel_(NSWindow.NormalWindowLevel)
            
            # 确保窗口在前台
            self.main_window.raise_()
            self.main_window.activateWindow()
        except Exception as e:
            print(f"恢复窗口级别时出错: {e}")
    
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
                    QTimer.singleShot(100, self._restore_window_level)
                    
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
    
    def _delayed_paste(self):
        """延迟执行粘贴操作"""
        if hasattr(self, '_pending_paste_text') and self._pending_paste_text:
            self._paste_and_reactivate(self._pending_paste_text)
            self._pending_paste_text = None
    
    def _paste_and_reactivate(self, text):
        """执行粘贴操作"""
        try:
            # 检查剪贴板管理器是否已初始化
            if not self.clipboard_manager:
                print("⚠️ 剪贴板管理器尚未就绪，无法执行粘贴操作")
                return
            
            # 清理HTML标签，确保复制纯文本
            clean_text = clean_html_tags(text)
            
            # 确保文本已复制到剪贴板
            self.clipboard_manager.copy_to_clipboard(clean_text)
            
            # 执行粘贴操作
            self.clipboard_manager.paste_to_current_app()
            print(f"✓ 已粘贴文本: {clean_text[:50]}{'...' if len(clean_text) > 50 else ''}")
            
        except Exception as e:
            print(f"❌ 粘贴操作失败: {e}")
            print(traceback.format_exc())
    
    def on_transcription_done(self, text):
        """转写完成的回调"""
        if text and text.strip():
            # 清理HTML标签用于剪贴板复制
            clean_text = clean_html_tags(text)
            
            # 1. 先复制到剪贴板（如果剪贴板管理器已就绪）
            if self.clipboard_manager:
                self.clipboard_manager.copy_to_clipboard(clean_text)
            # 2. 更新UI并添加到历史记录（无论窗口是否可见）
            self.main_window.display_result(text)  # UI显示保留HTML格式
            # 3. 延迟执行粘贴操作
            self._pending_paste_text = clean_text  # 粘贴使用纯文本
            QTimer.singleShot(100, self._delayed_paste)
            # 打印日志
            print(f"✓ {text}")
    
    def on_history_item_clicked(self, text):
        """处理历史记录点击事件"""
        # 清理HTML标签
        clean_text = clean_html_tags(text)
        
        # 1. 先复制到剪贴板（如果剪贴板管理器已就绪）
        if self.clipboard_manager:
            self.clipboard_manager.copy_to_clipboard(clean_text)
        # 2. 更新UI
        self.update_ui_signal.emit("准备粘贴历史记录", clean_text)
        # 3. 延迟执行粘贴操作
        self._pending_paste_text = clean_text
        QTimer.singleShot(100, self._delayed_paste)

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
            # 主窗口已在初始化时显示，这里不需要重复显示
            
            # 启动热键监听（如果热键管理器已初始化）
            if self.hotkey_manager:
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
        try:
            if not hasattr(self, 'settings_window') or self.settings_window is None:
                self.settings_window = SettingsWindow(
                    settings_manager=self.settings_manager,
                    audio_capture=self.audio_capture
                )
                # 使用线程安全的方式连接信号
                self.settings_window.settings_saved.connect(
                    self.apply_settings, 
                    Qt.ConnectionType.QueuedConnection
                )
            
            self.settings_window.show()
            self.settings_window.raise_()
            self.settings_window.activateWindow()
        except Exception as e:
            print(f"❌ 显示设置窗口失败: {e}")
            import traceback
            print(traceback.format_exc())

    def apply_settings(self):
        """应用设置"""
        try:
            print("开始应用设置...")
            
            # 应用热键设置（如果热键管理器已初始化）
            try:
                if self.hotkey_manager:
                    current_hotkey = self.settings_manager.get_hotkey()
                    print(f"应用热键设置: {current_hotkey}")
                    self.hotkey_manager.stop_listening()  # 先停止监听
                    self.hotkey_manager.update_hotkey(current_hotkey)  # 更新热键
                    self.hotkey_manager.start_listening()  # 重新开始监听
                    print("✓ 热键设置已应用")
            except Exception as e:
                print(f"❌ 应用热键设置失败: {e}")
            
            # 应用音频设置
            try:
                if hasattr(self, 'audio_capture') and self.audio_capture:
                    volume_threshold = self.settings_manager.get_setting('audio.volume_threshold')
                    print(f"应用音量阈值: {volume_threshold}")
                    self.audio_capture.set_volume_threshold(volume_threshold)
                    print("✓ 音频设置已应用")
            except Exception as e:
                print(f"❌ 应用音频设置失败: {e}")
            
            # 应用ASR设置（如果语音识别引擎已初始化）
            try:
                if self.funasr_engine:
                    model_path = self.settings_manager.get_setting('asr.model_path')
                    if model_path and hasattr(self.funasr_engine, 'load_model'):
                        print(f"加载ASR模型: {model_path}")
                        self.funasr_engine.load_model(model_path)
                    
                    punc_model_path = self.settings_manager.get_setting('asr.punc_model_path')
                    if punc_model_path and hasattr(self.funasr_engine, 'load_punctuation_model'):
                        print(f"加载标点模型: {punc_model_path}")
                        self.funasr_engine.load_punctuation_model(punc_model_path)
                    print("✓ ASR设置已应用")
            except Exception as e:
                print(f"❌ 应用ASR设置失败: {e}")
            
            print("✓ 所有设置已应用")
        except Exception as e:
            import traceback
            print(f"❌ 应用设置失败: {e}")
            print(traceback.format_exc())

if __name__ == "__main__":
    setup_logging()  # 初始化日志系统
    logging.info("应用程序启动")
    
    try:
        print("正在创建应用程实例...")
        app = Application()
        print("应用程序实例已创建，正在运行...")
        sys.exit(app.run())
    except Exception as e:
        print(f"运行应用程序时出错: {e}")
        print(traceback.format_exc())
        sys.exit(1)