import sys
import traceback
import os

# 添加项目根目录到Python路径，解决导入问题
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from functools import wraps
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox, QDialog
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, QMetaObject, Qt, Q_ARG, QObject, pyqtSlot
from PyQt6.QtGui import QIcon
# 第三步模块化替换：使用UI管理器包装器
from managers.ui_manager_wrapper import UIManagerWrapper

# 第四步模块化替换：使用音频管理器包装器
from managers.audio_manager_wrapper import AudioManagerWrapper
from funasr_engine import FunASREngine
from clipboard_manager import ClipboardManager
# 第二步模块化替换：使用状态管理器包装器
from managers.state_manager_wrapper import StateManagerWrapper
from context_manager import Context
from audio_threads import AudioCaptureThread, TranscriptionThread
from global_hotkey import GlobalHotkeyManager
import time
import re
import subprocess
import threading
from audio_manager import AudioManager
from config import APP_VERSION  # 从config导入版本号
from utils.text_utils import clean_html_tags
from utils.error_handler import handle_exceptions
import atexit
import multiprocessing
import logging
from datetime import datetime
from ui.settings_window import MacOSSettingsWindow
# 第一步模块化替换：使用设置管理器包装器
from managers.settings_manager_wrapper import SettingsManagerWrapper
# 第七步模块化替换：使用清理管理器包装器
from managers.cleanup_manager_wrapper import CleanupManagerWrapper
# 第八步模块化替换：使用转写管理器包装器
from managers.transcription_manager_wrapper import TranscriptionManagerWrapper
# 第九步模块化替换：使用权限管理器包装器
from managers.permission_manager_wrapper import PermissionManagerWrapper

# 在文件开头添加日志配置
def setup_logging():
    """配置日志系统"""
    # 创建logs目录（如果不存在）
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 生成日志文件名（使用当前时间）
    log_filename = f"logs/app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # 创建文件处理器（保留详细日志）
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # 创建控制台处理器（只显示警告和错误）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()  # 清除现有处理器
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    print(f"✓ 日志系统已初始化，日志文件: {log_filename}")
    # 只记录到文件，不输出到控制台
    file_handler.emit(logging.LogRecord(
        name='root', level=logging.INFO, pathname='', lineno=0,
        msg=f"日志文件: {log_filename}", args=(), exc_info=None
    ))

# 应用信息
APP_NAME = "Dou-flow"  # 统一应用名称
APP_AUTHOR = "ttmouse"

# 环境检查和提示
def check_environment():
    """检查当前Python环境并给出提示"""
    import sys
    python_path = sys.executable
    
    # 检查是否为本地打包版本
    if getattr(sys, 'frozen', False) or 'Dou-flow.app' in python_path:
        print("✅ 本地打包版本，跳过环境检查")
        return True

    # 检查是否在正确的conda环境中
    if 'funasr_env' in python_path:
        print("✅ 当前使用conda funasr_env环境 (推荐)")
        return True
    elif 'venv' in python_path:
        print("⚠️  当前使用项目venv环境")
        print("💡 建议使用: conda activate funasr_env && python src/main.py")
        return False
    else:
        print(f"❌ 当前环境: {python_path}")
        print("💡 建议使用: conda activate funasr_env && python src/main.py")
        return False
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

def handle_common_exceptions(show_error=True):
    """统一异常处理装饰器
    
    Args:
        show_error: 是否显示错误信息给用户
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except PermissionError as e:
                error_msg = f"权限错误: {e}"
                logging.error(error_msg)
                if show_error and hasattr(self, 'tray_icon') and self.tray_icon:
                    self.tray_icon.showMessage(
                        "权限错误",
                        "请检查麦克风和辅助功能权限设置",
                        QSystemTrayIcon.MessageIcon.Warning,
                        3000
                    )
            except FileNotFoundError as e:
                error_msg = f"文件未找到: {e}"
                logging.error(error_msg)
                if show_error:
                    logging.error(error_msg)
            except Exception as e:
                error_msg = f"操作失败: {e}"
                logging.error(error_msg)
                if show_error:
                    logging.error(error_msg)
                # 记录详细的错误堆栈
                logging.debug(traceback.format_exc())
        return wrapper
    return decorator

class Application(QObject):
    update_ui_signal = pyqtSignal(str, str)
    show_window_signal = pyqtSignal()
    start_recording_signal = pyqtSignal()
    stop_recording_signal = pyqtSignal()

    def __init__(self):
        # 先创建QApplication实例，确保在主线程中
        self.app = QApplication(sys.argv)
        
        # 然后调用父类初始化
        super().__init__()
        
        # 初始化资源清理
        atexit.register(self.cleanup_resources)
        
        # 添加应用级别的线程锁
        self._app_lock = threading.RLock()
        
        try:
            
            # 设置Qt应用程序的异常处理
            self.app.setAttribute(Qt.ApplicationAttribute.AA_DontShowIconsInMenus, False)
            
            # 初始化设置管理器（第一步模块化替换 - 真正的减法重构）
            self.settings_manager = SettingsManagerWrapper()
            self.settings_manager.set_apply_settings_callback(self.apply_settings)
            
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
                # 创建自定义QApplication子类来处理事件
                self._setup_mac_event_handling()
            
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
            

            
            # 重启热键功能
            restart_hotkey_action = tray_menu.addAction("重启热键功能")
            restart_hotkey_action.triggered.connect(self._safe_restart_hotkey_manager)
            
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
            
            # 确认系统托盘图标设置成功
            if not self.tray_icon.isVisible():
                pass  # 静默处理托盘图标设置失败
            
            # 初始化基础组件（第三步模块化替换 - 真正的减法重构）
            self.state_manager = StateManagerWrapper()
            self.main_window = UIManagerWrapper(app_instance=self)
            self.main_window.set_state_manager(self.state_manager)
            # 设置UI管理器的信号连接
            self.main_window.set_show_window_signal(self.show_window_signal)
            

            
            # 初始化基础音频组件（第四步模块化替换）
            self.audio_capture = AudioManagerWrapper()
            # 第七步模块化替换：使用清理管理器包装器
            self.cleanup_manager = CleanupManagerWrapper()
            # 第八步模块化替换：使用转写管理器包装器
            self.transcription_manager = TranscriptionManagerWrapper()
            # 第九步模块化替换：使用权限管理器包装器
            self.permission_manager = PermissionManagerWrapper()
            
            # 初始化状态变量
            self.recording = False
            self.previous_volume = None
            self.funasr_engine = None  # 延迟初始化
            self.hotkey_manager = None  # 延迟初始化
            self.clipboard_manager = None  # 延迟初始化
            self.context = None  # 延迟初始化
            self.audio_manager = None  # 延迟初始化
            self.audio_capture_thread = None  # 延迟初始化
            
            # 连接信号
            self.show_window_signal.connect(self._show_window_internal)
            
            # 创建并显示启动加载界面
            try:
                from src.app_loader import LoadingSplash, AppLoader
            except ImportError:
                from app_loader import LoadingSplash, AppLoader
            self.splash = LoadingSplash()
            self.splash.show()

            # 创建异步加载器
            self.app_loader = AppLoader(self, self.settings_manager)

            # 确保主窗口在初始化完成前不显示
            self.main_window.hide()

            # 连接加载器信号
            self.app_loader.progress_updated.connect(self.splash.update_progress)
            self.app_loader.component_loaded.connect(self.on_component_loaded)
            self.app_loader.loading_completed.connect(self.on_loading_completed)
            self.app_loader.loading_failed.connect(self.on_loading_failed)
            
            pass  # 基础界面已启动
            
            # 临时恢复原有加载方式，确保程序能启动
            self._start_async_loading()

        except Exception as e:
            logging.error(f"初始化失败: {e}")
            logging.error(traceback.format_exc())
            sys.exit(1)
    




    def _setup_mac_event_handling(self):
        """设置macOS事件处理"""
        try:
            # 安装事件过滤器来处理dock图标点击
            self.app.installEventFilter(self)
            
            # 创建dock菜单
            self._setup_dock_menu()
            
            pass  # macOS事件处理器已安装
        except Exception as e:
            logging.error(f"设置macOS事件处理失败: {e}")
    
    def _setup_dock_menu(self):
        """设置macOS Dock图标菜单（通过系统托盘实现）"""
        try:
            # 在macOS上，dock菜单实际上是通过系统托盘图标的右键菜单实现的
            # 由于PyQt6没有直接的setDockMenu方法，我们使用系统托盘图标来提供类似功能
            # 系统托盘菜单已经在初始化时创建，这里只是确认功能可用
            if not (hasattr(self, 'tray_icon') and self.tray_icon.isVisible()):
                pass  # 静默处理托盘图标问题
            
        except Exception as e:
            logging.error(f"设置Dock菜单失败: {e}")
    
    def eventFilter(self, obj, event):
        """优化的事件过滤器，减少处理时间"""
        try:
            # 快速检查：只处理应用程序对象的特定事件
            if obj == self.app and event.type() == 121:  # QEvent.Type.ApplicationActivate
                # 使用信号异步处理，避免阻塞事件循环
                self.show_window_signal.emit()
                return False  # 继续传递事件
            
            # 对于其他事件，直接返回，减少处理时间
            return False
        except Exception:

            return False
    
    def _start_async_loading(self):
        """启动异步加载任务"""
        from PyQt6.QtCore import QTimer

        # 延迟启动加载，让UI先显示
        self._load_timer = QTimer()
        self._load_timer.setSingleShot(True)
        self._load_timer.timeout.connect(self.app_loader.start_loading)
        self._load_timer.start(500)  # 500ms后开始加载
    
    def on_component_loaded(self, component_name, component):
        """当组件加载完成时的回调"""
        try:
            # 将组件赋值给应用实例
            setattr(self, component_name, component)

            # 特殊处理某些组件
            if component_name == 'funasr_engine' and component:
                if hasattr(self, 'state_manager') and self.state_manager:
                    self.state_manager.funasr_engine = component

            elif component_name == 'hotkey_manager' and component:
                component.set_press_callback(self.on_option_press)
                component.set_release_callback(self.on_option_release)

            elif component_name == 'audio_capture_thread' and component:
                component.audio_captured.connect(self.on_audio_captured)
                component.recording_stopped.connect(self.stop_recording)

        except Exception as e:
            logging.error(f"组件 {component_name} 加载失败: {e}")
    
    @pyqtSlot(str, object)
    def _set_component_in_main_thread(self, component_name, component):
        """在主线程中设置组件"""
        self.on_component_loaded(component_name, component)
    
    def on_loading_completed(self):
        """当所有组件加载完成时的回调"""
        try:
            # 隐藏启动界面
            if hasattr(self, 'splash'):
                self.splash.close()

            # 显示主窗口并置顶
            self.main_window._show_window_internal()

            # 完成最终初始化
            self._finalize_initialization()

            # 标记初始化完成
            self._mark_initialization_complete()

            pass  # 应用程序启动完成

        except Exception as e:
            logging.error(f"加载完成处理失败: {e}")

    def on_loading_failed(self, error_message):
        """当加载失败时的回调"""
        logging.error(f"组件加载失败: {error_message}")

        # 隐藏启动界面
        if hasattr(self, 'splash') and self.splash:
            self.splash.close()

        # 显示主窗口并置顶（即使部分组件失败）
        self.main_window._show_window_internal()

        # 显示错误信息
        self.update_ui_signal.emit("⚠️ 部分组件初始化失败", error_message)
    
    # 原有的同步初始化方法已被异步加载器替代
    # 保留权限检查方法供加载器使用
    
    def _finalize_initialization(self):
        """完成初始化设置"""
        try:
            # 设置连接
            self.setup_connections()

            # 应用设置
            self.apply_settings()

            logging.debug("最终初始化完成")
        except Exception as e:
            logging.error(f"初始化设置失败: {e}")

    def _mark_initialization_complete(self):
        """标记初始化完成"""
        try:
            # 标记主窗口初始化完成
            if hasattr(self.main_window, '_initialization_complete'):
                self.main_window._initialization_complete = True

            # 通知初始化完成
            self.update_ui_signal.emit("✓ 应用初始化完成", "")
        except Exception as e:
            logging.error(f"标记初始化完成失败: {e}")
    




    def _check_development_permissions(self):
        """检查开发环境权限 - 委托给权限管理器"""
        self.permission_manager.check_development_permissions(self)

    @pyqtSlot()
    def _safe_restart_hotkey_manager(self):
        """安全的热键管理器重启方法 - 简化版本"""
        try:
            # 确保在主线程中执行
            if QThread.currentThread() != QApplication.instance().thread():
                QMetaObject.invokeMethod(
                    self, "restart_hotkey_manager",
                    Qt.ConnectionType.QueuedConnection
                )
                return
            
            # 调用实际的重启方法
            self.restart_hotkey_manager()
            
        except Exception as e:
            logging.error(f"安全重启热键管理器失败: {e}")
            # 显示错误通知
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.showMessage(
                    "热键功能",
                    "热键功能重启失败，请检查权限设置",
                    QSystemTrayIcon.MessageIcon.Warning,
                    3000
                )
    
    @handle_common_exceptions(show_error=True)
    def restart_hotkey_manager(self):
        """重启热键管理器 - 简化版本，仅用于手动重启和方案切换"""
        logging.debug("开始重启热键管理器")
        
        # 停止现有的热键管理器
        if self.hotkey_manager:
            try:
                self.hotkey_manager.stop_listening()
                if hasattr(self.hotkey_manager, 'cleanup'):
                    self.hotkey_manager.cleanup()
            except Exception as e:
                logging.error(f"停止现有热键管理器失败: {e}")
        
        # 重新创建热键管理器
        try:
            try:
                from src.hotkey_manager_factory import HotkeyManagerFactory
            except ImportError:
                from hotkey_manager_factory import HotkeyManagerFactory
            
            # 获取热键方案设置
            scheme = self.settings_manager.get_hotkey_scheme()
            
            # 使用工厂模式创建热键管理器
            self.hotkey_manager = HotkeyManagerFactory.create_hotkey_manager(scheme, self.settings_manager)
            
            if self.hotkey_manager:
                self.hotkey_manager.set_press_callback(self.on_option_press)
                self.hotkey_manager.set_release_callback(self.on_option_release)
                
                # 应用当前热键设置
                current_hotkey = self.settings_manager.get_hotkey()
                self.hotkey_manager.update_hotkey(current_hotkey)
                self.hotkey_manager.update_delay_settings()
                
                # 启动监听
                self.hotkey_manager.start_listening()
                
                logging.debug(f"热键管理器重启成功，使用方案: {scheme}")
                
                # 显示成功通知
                if hasattr(self, 'tray_icon') and self.tray_icon:
                    self.tray_icon.showMessage(
                        "热键功能",
                        "热键功能已成功重启",
                        QSystemTrayIcon.MessageIcon.Information,
                        3000
                    )
            else:
                logging.error(f"热键管理器创建失败，方案: {scheme}")
                self.hotkey_manager = None
                
        except Exception as e:
            logging.error(f"热键管理器重启失败: {e}")
            self.hotkey_manager = None
    

    
    def is_component_ready(self, component_name, check_method=None):
        """统一的组件状态检查方法 - 委托给清理管理器"""
        return self.cleanup_manager.is_component_ready(self, component_name, check_method)
    
    def is_ready_for_recording(self):
        """检查是否准备好录音 - 委托给清理管理器"""
        return self.cleanup_manager.is_ready_for_recording(self)
    
    def cleanup_component(self, component_name, cleanup_method='cleanup', timeout=200):
        """统一的组件清理方法 - 委托给清理管理器"""
        return self.cleanup_manager.cleanup_component(self, component_name, cleanup_method, timeout)
    
    def cleanup_resources(self):
        """清理资源 - 使用统一的清理方法"""
        try:
            # 恢复系统音量（如果有保存的音量）
            if hasattr(self, 'previous_volume') and self.previous_volume is not None:
                self._set_system_volume(self.previous_volume)
                pass  # 系统音量已恢复
            

            
            # 使用统一方法清理所有组件
            components_to_cleanup = [
                ('audio_capture_thread', 'stop'),
                ('transcription_thread', 'terminate'),
                ('audio_capture', 'cleanup'),
                ('funasr_engine', 'cleanup'),
                ('hotkey_manager', 'cleanup'),
                ('state_manager', 'cleanup')
            ]
            
            for component_name, method in components_to_cleanup:
                self.cleanup_component(component_name, method)
            
            # 清理多进程资源
            try:
                import multiprocessing
                import gc
                
                # 强制垃圾回收
                gc.collect()
                
                # 清理当前进程资源
                current_process = multiprocessing.current_process()
                if hasattr(current_process, '_clean'):
                    current_process._clean()
                
                # 清理资源跟踪器
                try:
                    from multiprocessing import resource_tracker
                    if hasattr(resource_tracker, '_resource_tracker'):
                        tracker = resource_tracker._resource_tracker
                        if tracker and hasattr(tracker, '_stop'):
                            tracker._stop()
                except Exception as tracker_e:
                    logging.error(f"清理资源跟踪器失败: {tracker_e}")
                    
            except Exception as e:
                logging.error(f"清理多进程资源失败: {e}")
            
            pass  # 资源清理完成
        except Exception as e:
            logging.error(f"资源清理失败: {e}")
        finally:
            # 确保关键资源被清理
            try:
                if hasattr(self, 'app'):
                    self.app.quit()
            except Exception as e:
                logging.error(f"应用退出失败: {e}")
    
    def _quick_cleanup(self):
        """快速清理关键资源，避免长时间等待导致卡死 - 简化版本"""
        pass  # 开始快速清理资源
        try:

            
            # 1. 立即停止录音相关操作
            self.recording = False
            
            # 2. 停止定时器
            if hasattr(self, 'recording_timer') and self.recording_timer:
                try:
                    self.recording_timer.stop()
                except Exception as e:
                    logging.error(f"停止录音定时器失败: {e}")
            
            # 3. 快速终止线程，不等待
            if hasattr(self, 'audio_capture_thread') and self.audio_capture_thread:
                try:
                    if self.audio_capture_thread.isRunning():
                        self.audio_capture_thread.terminate()  # 直接终止，不等待
                except Exception as e:
                    logging.error(f"终止音频捕获线程失败: {e}")
            
            if hasattr(self, 'transcription_thread') and self.transcription_thread:
                try:
                    if self.transcription_thread.isRunning():
                        self.transcription_thread.terminate()  # 直接终止，不等待
                except Exception as e:
                    logging.error(f"终止转写线程失败: {e}")
            
            # 4. 快速清理音频资源
            if hasattr(self, 'audio_capture') and self.audio_capture:
                try:
                    # 不调用完整的cleanup，只做关键清理
                    if hasattr(self.audio_capture, 'stream') and self.audio_capture.stream:
                        self.audio_capture.stream.stop_stream()
                        self.audio_capture.stream.close()
                except Exception as e:
                    logging.error(f"关闭音频流失败: {e}")
            
            # 5. 恢复系统音量
            if hasattr(self, 'previous_volume') and self.previous_volume is not None:
                try:
                    self._set_system_volume(self.previous_volume)
                except Exception as e:
                    logging.error(f"恢复系统音量失败: {e}")
            
            # 6. 清理热键管理器（快速版本）
            if hasattr(self, 'hotkey_manager') and self.hotkey_manager:
                try:
                    # 调用停止监听方法，但不等待清理完成
                    self.hotkey_manager.stop_listening()
                except Exception as e:
                    logging.error(f"快速清理热键管理器失败: {e}")
            
            # 7. 关闭主窗口
            if hasattr(self, 'main_window') and self.main_window:
                try:
                    self.main_window.close()
                except Exception as e:
                    logging.error(f"关闭主窗口失败: {e}")
            
            # 8. 隐藏系统托盘图标
            if hasattr(self, 'tray_icon') and self.tray_icon:
                try:
                    self.tray_icon.hide()
                except Exception as e:
                    logging.error(f"隐藏系统托盘图标失败: {e}")
            
        except Exception as e:
            logging.error(f"快速清理失败: {e}")
            import traceback
            logging.error(traceback.format_exc())



    def _set_system_volume(self, volume):
        """设置系统音量 - 委托给音频管理器"""
        self.audio_capture.set_system_volume(volume)

    def _get_system_volume(self):
        """获取当前系统音量 - 委托给音频管理器"""
        return self.audio_capture.get_system_volume()

    def _restore_volume_async(self, volume):
        """异步恢复音量 - 委托给音频管理器"""
        self.audio_capture.restore_volume_async(volume)

    @handle_common_exceptions(show_error=True)
    def start_recording(self):
        """开始录音 - 委托给音频管理器"""
        with self._app_lock:
            try:
                # 使用统一的状态检查方法
                if not self.is_ready_for_recording():
                    return

                if not self.recording:
                    self.recording = True

                    try:
                        # 设置录音定时器回调
                        def setup_timer(duration_ms):
                            if hasattr(self, 'recording_timer'):
                                self.recording_timer.stop()
                                self.recording_timer.deleteLater()
                            self.recording_timer = QTimer(self)
                            self.recording_timer.setSingleShot(True)
                            self.recording_timer.timeout.connect(self._auto_stop_recording)
                            self.recording_timer.start(duration_ms)

                        # 委托给音频管理器处理录音流程
                        self.previous_volume, self.audio_capture_thread = self.audio_capture.start_recording_process(
                            self.state_manager,
                            self.audio_capture_thread,
                            self.settings_manager,
                            setup_timer
                        )

                        # 重新连接信号（如果线程被重新创建）
                        if self.audio_capture_thread:
                            self.audio_capture_thread.audio_captured.connect(self.on_audio_captured)
                            self.audio_capture_thread.recording_stopped.connect(self.stop_recording)

                    except Exception as e:
                        error_msg = f"开始录音时出错: {str(e)}"
                        logging.error(error_msg)
                        self.update_ui_signal.emit(f"❌ {error_msg}", "")

            except Exception as e:
                import traceback
                error_msg = f"start_recording线程安全异常: {str(e)}"
                logging.error(f"{error_msg}")
                logging.error(f"当前线程: {threading.current_thread().name}")
                logging.error(f"详细堆栈: {traceback.format_exc()}")
                self.update_ui_signal.emit(f"❌ {error_msg}", "")

    def stop_recording(self):
        """停止录音 - 委托给音频管理器"""
        if self._can_stop_recording():
            self.recording = False

            # 停止定时器
            if hasattr(self, 'recording_timer') and self.recording_timer.isActive():
                self.recording_timer.stop()

            try:
                # 设置音量恢复回调
                def setup_volume_timer(volume, delay_ms):
                    if hasattr(self, 'volume_timer'):
                        self.volume_timer.stop()
                        self.volume_timer.deleteLater()
                    self.volume_timer = QTimer(self)
                    self.volume_timer.setSingleShot(True)
                    self.volume_timer.timeout.connect(lambda: self._restore_volume_async(volume))
                    self.volume_timer.start(delay_ms)

                # 委托给音频管理器处理停止录音流程
                audio_data = self.audio_capture.stop_recording_process(
                    self.state_manager,
                    self.audio_capture_thread,
                    self.previous_volume,
                    setup_volume_timer
                )

                # 重置 previous_volume
                self.previous_volume = None

                if len(audio_data) > 0:
                    # 使用统一的状态检查方法
                    if not self.is_component_ready('funasr_engine', 'is_ready'):
                        self.update_ui_signal.emit("⚠️ 语音识别引擎尚未就绪，无法处理录音", "")
                        return

                    self.transcription_thread = TranscriptionThread(audio_data, self.funasr_engine)
                    self.transcription_thread.transcription_done.connect(self.on_transcription_done)
                    self.transcription_thread.start()
                else:
                    self.update_ui_signal.emit("❌ 未检测到声音", "")
            except Exception as e:
                logging.error(f"录音失败: {e}")
                self.update_ui_signal.emit(f"❌ 录音失败: {e}", "")
    
    def _auto_stop_recording(self):
        """定时器触发的自动停止录音"""
        try:
            # 在打包后的应用中，避免在定时器回调中直接使用print
            # 使用信号来安全地更新UI或记录日志
            if self._can_stop_recording():
                # 发送信号到主线程进行UI更新
                self.update_ui_signal.emit("⏰ 录音时间达到最大时长，自动停止录音", "")
                self.stop_recording()
            # 不在录音状态时不需要特别处理
        except Exception as e:
            # 静默处理异常，避免在定时器回调中抛出异常
            pass

    def cleanup(self):
        """清理资源"""
        try:
            # 停止录音定时器
            if hasattr(self, 'recording_timer') and self.recording_timer.isActive():
                self.recording_timer.stop()
            
            # 停止音量恢复定时器
            if hasattr(self, 'volume_timer') and self.volume_timer.isActive():
                self.volume_timer.stop()
                self.volume_timer.deleteLater()
            
            # 清理设置窗口
            if hasattr(self, 'settings_window') and self.settings_window:
                try:
                    # 断开信号连接
                    self.settings_window.settings_saved.disconnect()
                    # 关闭窗口
                    self.settings_window.close()
                    self.settings_window = None
                except Exception as e:
                    logging.error(f"清理设置窗口失败: {e}")
            
            if hasattr(self, 'audio_capture') and self.audio_capture:
                self.audio_capture.clear_recording_data()
                
            if hasattr(self, 'transcription_thread'):
                self.transcription_thread.quit()
                self.transcription_thread.wait()
                
            if hasattr(self, 'hotkey_manager') and self.hotkey_manager:
                self.hotkey_manager.stop_listening()
        except Exception as e:
            logging.error(f"清理资源失败: {e}")

    @pyqtSlot()
    def show_window(self):
        """显示主窗口（可以从其他线程调用）- 委托给UI管理器"""
        self.main_window.show_window_safe()

    def setup_connections(self):
        """设置信号连接"""
        if self.hotkey_manager:
            self.hotkey_manager.set_press_callback(self.on_option_press)
            self.hotkey_manager.set_release_callback(self.on_option_release)
            # 热键回调函数已设置
            
        self.update_ui_signal.connect(self.update_ui)
        self.main_window.record_button_clicked.connect(self.toggle_recording)
        self.main_window.history_item_clicked.connect(self.on_history_item_clicked)
        self.state_manager.status_changed.connect(self.main_window.update_status)
        # 连接窗口显示信号
        self.show_window_signal.connect(self._show_window_internal)
        # 连接录音信号，确保在主线程中执行
        self.start_recording_signal.connect(self.start_recording)
        self.stop_recording_signal.connect(self.stop_recording)

    def _can_start_recording(self):
        """统一的录音开始条件检查 - 委托给状态管理器"""
        return self.state_manager.can_start_recording(self.recording)

    def _can_stop_recording(self):
        """统一的录音停止条件检查 - 委托给状态管理器"""
        return self.state_manager.can_stop_recording(self.recording)

    def toggle_recording(self):
        """切换录音状态 - 委托给状态管理器"""
        self.state_manager.toggle_recording_state(
            self.recording,
            self.start_recording,
            self.stop_recording
        )

    def on_option_press(self):
        """处理Control键按下事件"""
        if self._can_start_recording():
            # 使用信号确保在主线程中执行
            self.start_recording_signal.emit()

    def on_option_release(self):
        """处理Control键释放事件"""
        if self._can_stop_recording():
            # 使用信号确保在主线程中执行
            self.stop_recording_signal.emit()

    def on_audio_captured(self, data):
        """音频数据捕获回调"""
        # 录音过程中不需要频繁更新状态，因为状态已经在start_recording时设置了
        pass

    def quit_application(self):
        """退出应用程序 - 简化版本"""
        try:

            
            # 2. 停止热键监听，避免在清理过程中触发新的操作
            if hasattr(self, 'hotkey_manager') and self.hotkey_manager:
                try:
                    self.hotkey_manager.stop_listening()
                except Exception as e:
                    logging.error(f"停止热键监听失败: {e}")
            
            # 3. 快速清理资源，避免长时间等待
            self._quick_cleanup()
            
            # 4. 强制退出应用
            if hasattr(self, 'app') and self.app:
                self.app.quit()
                
        except Exception as e:
            logging.error(f"退出应用程序时出错: {e}")
            # 强制退出
            import os
            os._exit(0)

    def _restore_window_level(self):
        """恢复窗口正常级别"""
        try:
            # 简化实现，只使用Qt方法确保窗口在前台
            self.main_window.raise_()
            self.main_window.activateWindow()
        except Exception as e:
            logging.error(f"恢复窗口级别时出错: {e}")
    
    def _show_window_internal(self):
        """在主线程中显示窗口"""
        try:
            # 在 macOS 上使用 NSWindow 来激活窗口
            if sys.platform == 'darwin':
                try:
                    from AppKit import NSApplication, NSWindow
                    from PyQt6.QtGui import QWindow

                    # 获取应用
                    app = NSApplication.sharedApplication()

                    # 显示窗口
                    if not self.main_window.isVisible():
                        self.main_window.show()

                    # 获取窗口句柄
                    window_handle = self.main_window.windowHandle()
                    if window_handle:
                        # 在PyQt6中使用winId()获取原生窗口ID
                        window_id = self.main_window.winId()
                        if window_id:
                            # 激活应用程序
                            app.activateIgnoringOtherApps_(True)

                            # 使用Qt方法激活窗口
                            self.main_window.raise_()
                            self.main_window.activateWindow()
                            self.main_window.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
                        else:
                            # 如果无法获取窗口ID，使用基本方法
                            app.activateIgnoringOtherApps_(True)
                            self.main_window.raise_()
                            self.main_window.activateWindow()
                    else:
                        # 如果无法获取窗口句柄，使用基本方法
                        app.activateIgnoringOtherApps_(True)
                        self.main_window.raise_()
                        self.main_window.activateWindow()

                except Exception as e:
                    logging.error(f"激活窗口时出错: {e}")
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

            pass  # 窗口已显示
        except Exception as e:
            logging.error(f"显示窗口失败: {e}")
    

    
    def _paste_and_reactivate(self, text):
        """执行粘贴操作 - 委托给转写管理器"""
        self.transcription_manager.paste_and_reactivate(self, text)
    
    def _paste_and_reactivate_with_feedback(self, text):
        """执行粘贴操作并返回成功状态 - 委托给转写管理器"""
        return self.transcription_manager.paste_and_reactivate_with_feedback(self, text)
    
    def on_transcription_done(self, text):
        """转写完成的回调 - 委托给转写管理器"""
        self.transcription_manager.on_transcription_done(self, text)
    
    def on_history_item_clicked(self, text):
        """处理历史记录点击事件 - 委托给转写管理器"""
        self.transcription_manager.on_history_item_clicked(self, text)

    def update_ui(self, status, result):
        """更新界面显示 - 委托给状态管理器"""
        self.state_manager.update_ui_display(self.main_window, status, result)

    def run(self):
        """运行应用程序"""
        try:
            print("✓ 应用程序正在启动...")
            logging.info("应用程序启动")
            
            # 主窗口已在初始化时显示，这里不需要重复显示
            
            # 启动热键监听（如果热键管理器已初始化）
            if self.hotkey_manager:
                try:
                    print("✓ 启动热键监听...")
                    self.hotkey_manager.start_listening()
                    logging.info("热键监听已启动")
                except Exception as e:
                    logging.error(f"启动热键监听失败: {e}")
                    logging.error(f"详细错误信息: {traceback.format_exc()}")
                    # 尝试重新初始化热键管理器
                    try:
                        self.hotkey_manager = HotkeyManager(self.settings_manager)
                        self.hotkey_manager.set_press_callback(self.on_option_press)
                        self.hotkey_manager.set_release_callback(self.on_option_release)
                        self.hotkey_manager.start_listening()
                    except Exception as e2:
                        logging.error(f"重新初始化热键管理器失败: {e2}")
                        self.hotkey_manager = None


            else:
                try:
                    print("✓ 初始化热键管理器...")
                    try:
                        from src.hotkey_manager_factory import HotkeyManagerFactory
                    except ImportError:
                        from hotkey_manager_factory import HotkeyManagerFactory
                    scheme = self.settings_manager.get_hotkey_scheme()
                    self.hotkey_manager = HotkeyManagerFactory.create_hotkey_manager(scheme, self.settings_manager)
                    if self.hotkey_manager:
                        self.hotkey_manager.set_press_callback(self.on_option_press)
                        self.hotkey_manager.set_release_callback(self.on_option_release)
                        self.hotkey_manager.start_listening()
                        logging.debug("热键管理器初始化完成")
                    else:
                        logging.error("热键管理器创建失败")
                except Exception as e:
                    logging.error(f"重新创建热键管理器失败: {e}")
                    logging.error(f"详细错误信息: {traceback.format_exc()}")
            
            print("✓ 进入主事件循环")
            logging.debug("进入Qt主事件循环")
            # 运行应用程序主循环
            return self.app.exec()
        except Exception as e:
            logging.error(f"运行应用程序时出错: {e}")
            logging.error(traceback.format_exc())
            return 1
        finally:
            # 使用快速清理避免卡死
            self._quick_cleanup()

    def check_permissions(self):
        """检查应用权限状态 - 委托给权限管理器"""
        self.permission_manager.check_permissions(self)

    # handle_mac_events方法已被eventFilter替代

    def show_settings(self):
        """显示设置窗口 - 委托给设置管理器"""
        self.settings_manager.show_settings(self.audio_capture)
    


    def apply_settings(self):
        """应用设置"""
        try:
            # 应用热键设置（如果热键管理器已初始化）
            try:
                current_scheme = self.settings_manager.get_hotkey_scheme()
                current_hotkey = self.settings_manager.get_hotkey()
                
                # 检查是否需要重新创建热键管理器（方案变化）
                need_recreate = False
                if self.hotkey_manager:
                    # 检查当前热键管理器的类型是否与设置中的方案匹配
                    current_manager_type = type(self.hotkey_manager).__name__.lower()
                    if current_scheme == 'hammerspoon' and 'hammerspoon' not in current_manager_type:
                        need_recreate = True
                        logging.info(f"热键方案从 python 切换到 {current_scheme}，需要重新创建热键管理器")
                    elif current_scheme == 'python' and 'hammerspoon' in current_manager_type:
                        need_recreate = True
                        logging.info(f"热键方案从 hammerspoon 切换到 {current_scheme}，需要重新创建热键管理器")
                
                if need_recreate or not self.hotkey_manager:
                    # 停止并清理现有的热键管理器
                    if self.hotkey_manager:
                        try:
                            self.hotkey_manager.stop_listening()
                            if hasattr(self.hotkey_manager, 'cleanup'):
                                self.hotkey_manager.cleanup()
                        except Exception as e:
                            logging.error(f"停止现有热键管理器失败: {e}")
                    
                    # 创建新的热键管理器
                    try:
                        try:
                            from src.hotkey_manager_factory import HotkeyManagerFactory
                        except ImportError:
                            from hotkey_manager_factory import HotkeyManagerFactory
                        self.hotkey_manager = HotkeyManagerFactory.create_hotkey_manager(current_scheme, self.settings_manager)
                        if self.hotkey_manager:
                            self.hotkey_manager.set_press_callback(self.on_option_press)
                            self.hotkey_manager.set_release_callback(self.on_option_release)
                            self.hotkey_manager.update_hotkey(current_hotkey)
                            self.hotkey_manager.update_delay_settings()
                            self.hotkey_manager.start_listening()
                            logging.debug(f"热键管理器已重新创建，使用方案: {current_scheme}")
                        else:
                            logging.error("热键管理器创建失败")
                    except Exception as e2:
                        logging.error(f"重新创建热键管理器失败: {e2}")
                        logging.error(f"详细错误信息: {traceback.format_exc()}")
                else:
                    # 只需要更新现有热键管理器的设置
                    self.hotkey_manager.stop_listening()
                    self.hotkey_manager.update_hotkey(current_hotkey)
                    self.hotkey_manager.update_delay_settings()
                    self.hotkey_manager.start_listening()
                    logging.debug(f"热键设置已更新，热键: {current_hotkey}")
                    
            except Exception as e:
                logging.error(f"应用热键设置失败: {e}")
                logging.error(f"详细错误信息: {traceback.format_exc()}")
            
            # 应用音频设置
            try:
                if hasattr(self, 'audio_capture') and self.audio_capture:
                    volume_threshold = self.settings_manager.get_setting('audio.volume_threshold')
                    self.audio_capture.set_volume_threshold(volume_threshold)
            except Exception as e:
                logging.error(f"应用音频设置失败: {e}")
            
            # 应用ASR设置（如果语音识别引擎已初始化）
            try:
                if self.funasr_engine:
                    model_path = self.settings_manager.get_setting('asr.model_path')
                    if model_path and hasattr(self.funasr_engine, 'load_model'):
                        self.funasr_engine.load_model(model_path)
                    
                    punc_model_path = self.settings_manager.get_setting('asr.punc_model_path')
                    if punc_model_path and hasattr(self.funasr_engine, 'load_punctuation_model'):
                        self.funasr_engine.load_punctuation_model(punc_model_path)
                    
                    # 重新加载热词
                    if hasattr(self.funasr_engine, 'reload_hotwords'):
                        self.funasr_engine.reload_hotwords()
                    
                    # 确保state_manager有funasr_engine的引用
                    if hasattr(self, 'state_manager') and self.state_manager:
                        self.state_manager.funasr_engine = self.funasr_engine
            except Exception as e:
                logging.error(f"应用ASR设置失败: {e}")
            
        except Exception as e:
            logging.error(f"应用设置失败: {e}")
            logging.error(traceback.format_exc())

def global_exception_handler(exc_type, exc_value, exc_traceback):
    """全局异常处理器，防止应用程序闪退"""
    if issubclass(exc_type, KeyboardInterrupt):
        # 允许 Ctrl+C 正常退出
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    # 记录异常到日志
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logging.error(f"未捕获的异常: {error_msg}")
    
    # 对于UI相关的异常，尝试继续运行而不是崩溃
    if 'Qt' in str(exc_type) or 'PyQt' in str(exc_type):
        return
    
    # 对于其他严重异常，调用默认处理器
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

if __name__ == "__main__":
    setup_logging()  # 初始化日志系统
    print("🔥 [减法重构] 开始真正的模块化 - 移除Application类冗余代码...")
    logging.info("🔥 [减法重构] 最终版：一比一还原原始逻辑，简化冗余代码")

    # 检查环境
    check_environment()

    # 设置全局异常处理器
    sys.excepthook = global_exception_handler
    
    try:
        app = Application()
        sys.exit(app.run())
    except Exception as e:
        logging.error(f"运行应用程序时出错: {e}")
        logging.error(traceback.format_exc())
        sys.exit(1)