import sys
import traceback
import os
from functools import wraps
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox, QDialog
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, QMetaObject, Qt, Q_ARG, QObject, pyqtSlot
from PyQt6.QtGui import QIcon
from ui.main_window import MainWindow

from audio_capture import AudioCapture
from funasr_engine import FunASREngine
from clipboard_manager import ClipboardManager
from state_manager import StateManager
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
        level=logging.INFO,  # 改为INFO级别，减少调试信息
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ],
        force=True  # 强制重新配置日志
    )
    
    print(f"✓ 日志系统已初始化，日志文件: {log_filename}")
    logging.info(f"日志文件: {log_filename}")
    logging.info("应用程序日志系统启动成功")

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
            
            # 初始化基础组件
            self.state_manager = StateManager()
            self.main_window = MainWindow(app_instance=self)
            self.main_window.set_state_manager(self.state_manager)
            

            
            # 初始化基础音频组件
            self.audio_capture = AudioCapture()
            
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
            from src.app_loader import LoadingSplash, AppLoader
            self.splash = LoadingSplash()
            self.splash.show()
            
            # 创建异步加载器
            self.app_loader = AppLoader(self, self.settings_manager)
            self.app_loader.progress_updated.connect(self.splash.update_progress)
            self.app_loader.component_loaded.connect(self.on_component_loaded)
            self.app_loader.loading_completed.connect(self.on_loading_completed)
            self.app_loader.loading_failed.connect(self.on_loading_failed)
            
            pass  # 基础界面已启动
            
            # 启动异步加载
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
        """事件过滤器，处理应用程序级别的事件"""
        try:
            # 只处理应用程序对象的事件
            if obj == self.app:
                # 处理 Dock 图标点击事件
                if event.type() == 121:  # QEvent.Type.ApplicationActivate
                    # 确保在主线程中执行窗口显示
                    if QThread.currentThread() == QApplication.instance().thread():
                        self._show_window_internal()
                    else:
                        self.show_window_signal.emit()
                    return False  # 继续传递事件
            
            # 对于其他事件，继续正常处理
            return False
        except Exception as e:
            logging.error(f"事件过滤器处理失败: {e}")
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
                # 关联到状态管理器
                self.state_manager.funasr_engine = component
                pass  # FunASR引擎已关联到状态管理器
                
            elif component_name == 'hotkey_manager' and component:
                # 设置热键回调
                component.set_press_callback(self.on_option_press)
                component.set_release_callback(self.on_option_release)
                
            elif component_name == 'audio_capture_thread' and component:
                # 连接音频捕获信号
                component.audio_captured.connect(self.on_audio_captured)
                component.recording_stopped.connect(self.stop_recording)
                
            pass  # 组件加载完成
            
        except Exception as e:
            logging.error(f"组件 {component_name} 加载后处理失败: {e}")
    
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
        if hasattr(self, 'splash'):
            self.splash.close()
            
        # 显示主窗口并置顶（即使部分组件失败）
        self.main_window._show_window_internal()
        
        # 显示错误信息
        self.update_ui_signal.emit("⚠️ 部分组件初始化失败", error_message)
    
    # 原有的同步初始化方法已被异步加载器替代
    # 保留权限检查方法供加载器使用
    
    def _finalize_initialization(self):
        """完成初始化设置 - 简化版本"""
        try:
            # 设置连接
            self.setup_connections()
            
            # 应用设置
            self.apply_settings()
            
            # 移除自动监控启动 - 简化架构
            # self.start_hotkey_monitor()  # 已移除
            
            logging.info("最终初始化完成")
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
    
    # 旧的复杂异步初始化方法已被简化的initialize_components方法替代



    def _check_development_permissions(self):
        """检查开发环境权限"""
        try:
            pass  # 检查开发环境权限
            
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
                pass  # 缺少权限
                pass
                pass
                pass
                pass  # 权限设置说明
                
                # 尝试打开系统设置
                try:
                    subprocess.run(['open', 'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'], check=False)
                    pass  # 已尝试打开系统设置页面
                except:
                    pass
                
                pass  # 提示信息
                
                # 给用户一些时间查看信息
                import time
                time.sleep(3)
            else:
                pass  # 权限检查通过
            
            # 更新权限缓存
            self.settings_manager.update_permissions_cache(has_accessibility, has_mic_access)
                
        except Exception as e:
            logging.error(f"权限检查失败: {e}")
            # 权限检查失败时也更新缓存，避免重复检查
            self.settings_manager.update_permissions_cache(False, False)

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
        logging.info("开始重启热键管理器")
        
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
            from src.hotkey_manager_factory import HotkeyManagerFactory
            
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
                
                logging.info(f"热键管理器重启成功，使用方案: {scheme}")
                
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
    
    # 移除自动监控功能 - 根据奥卡姆剃刀原理简化架构
    # def start_hotkey_monitor(self):
    #     """已移除：自动热键状态监控功能"""
    #     pass
    
    def is_component_ready(self, component_name, check_method=None):
        """统一的组件状态检查方法
        
        Args:
            component_name: 组件属性名
            check_method: 可选的检查方法名，如'is_ready'、'isRunning'等
        
        Returns:
            bool: 组件是否就绪
        """
        try:
            component = getattr(self, component_name, None)
            if not component:
                return False
            
            # 如果指定了检查方法，调用该方法
            if check_method and hasattr(component, check_method):
                check_attr = getattr(component, check_method)
                # 如果是方法，调用它；如果是属性，直接返回
                if callable(check_attr):
                    return check_attr()
                else:
                    return bool(check_attr)
            
            # 默认检查：组件存在且不为None
            return True
        except Exception as e:
            logging.error(f"检查组件 {component_name} 状态失败: {e}")
            return False
    
    def is_ready_for_recording(self):
        """检查是否准备好录音"""
        return (self.audio_capture_thread is not None and 
                self.funasr_engine is not None and 
                hasattr(self.funasr_engine, 'is_ready') and self.funasr_engine.is_ready and
                self.state_manager is not None and
                not self.recording)
    
    def cleanup_component(self, component_name, cleanup_method='cleanup', timeout=200):
        """统一的组件清理方法
        
        Args:
            component_name: 组件属性名
            cleanup_method: 清理方法名，默认为'cleanup'
            timeout: 超时时间（毫秒），仅对线程有效
        """
        try:
            component = getattr(self, component_name, None)
            if not component:
                return True
                
            # 处理线程类型的组件
            if hasattr(component, 'isRunning'):
                if component.isRunning():
                    # 尝试优雅停止
                    if hasattr(component, 'stop'):
                        component.stop()
                    
                    # 等待线程结束
                    if not component.wait(timeout):
                        logging.warning(f"{component_name}未能及时结束，强制终止")
                        component.terminate()
                        component.wait(100)  # 再等100ms
                        
                setattr(self, component_name, None)
                pass  # 组件已清理
                return True
            
            # 处理普通组件
            if hasattr(component, cleanup_method):
                getattr(component, cleanup_method)()
                pass  # 组件已清理
                return True
            else:
                pass  # 组件没有清理方法
                return False
                
        except Exception as e:
            logging.error(f"清理{component_name}失败: {e}")
            return False
    
    def cleanup_resources(self):
        """清理资源 - 使用统一的清理方法"""
        try:
            # 恢复系统音量（如果有保存的音量）
            if hasattr(self, 'previous_volume') and self.previous_volume is not None:
                self._set_system_volume(self.previous_volume)
                pass  # 系统音量已恢复
            
            # 移除监控线程相关代码 - 简化架构
            # if hasattr(self, '_monitor_should_stop'):
            #     self._monitor_should_stop = True
            
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
            # 0. 已移除：热键状态监控线程相关逻辑
            # if hasattr(self, '_monitor_should_stop'):
            #     self._monitor_should_stop = True
            
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

    # closeEvent方法已移除，因为Application类继承自QObject，不是QWidget
    # 窗口关闭事件应该在MainWindow中处理

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
                pass
            else:
                # 设置音量并取消静音
                volume = max(0, min(100, volume))  # 确保音量在 0-100 范围内
                subprocess.run([
                    'osascript',
                    '-e', f'set volume output volume {volume}',
                    '-e', 'set volume output muted false'
                ], check=True)
        except subprocess.CalledProcessError as e:
            logging.error(f"设置系统音量失败: {e}")
        except Exception as e:
            logging.error(f"设置系统音量时发生错误: {e}")

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
                return 0
            
            volume = int(volume_str)
            return volume
        except subprocess.CalledProcessError as e:
            logging.error(f"获取系统音量失败: {e}")
            return None
        except Exception as e:
            logging.error(f"获取系统音量时发生错误: {e}")
            return None
    
    def _restore_volume_async(self, volume):
        """异步恢复音量"""
        try:
            self._set_system_volume(volume)
        except Exception as e:
            logging.error(f"异步恢复音量失败: {e}")

    @handle_common_exceptions(show_error=True)
    def start_recording(self):
        """开始录音"""
        with self._app_lock:
            try:
                # 使用统一的状态检查方法
                if not self.is_ready_for_recording():
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
                        # 录音已开始
                        
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
            
            # 播放停止音效（先播放音效，再恢复音量）
            self.state_manager.stop_recording()
            
            # 异步恢复音量，避免阻塞主线程
            if self.previous_volume is not None:
                # 使用QTimer延迟恢复音量，确保音效播放完成
                # 将定时器保存为实例变量，避免被垃圾回收
                if hasattr(self, 'volume_timer'):
                    self.volume_timer.stop()
                    self.volume_timer.deleteLater()
                
                # 保存音量值，避免在定时器回调前被重置
                volume_to_restore = self.previous_volume
                self.volume_timer = QTimer(self)
                self.volume_timer.setSingleShot(True)
                self.volume_timer.timeout.connect(lambda: self._restore_volume_async(volume_to_restore))
                self.volume_timer.start(150)  # 150ms后恢复音量
                
                # 重置 previous_volume
                self.previous_volume = None
            
            try:
                audio_data = self.audio_capture.get_audio_data()
                
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
            if self.recording:
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

    def toggle_recording(self):
        """切换录音状态"""
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()

    def on_option_press(self):
        """处理Control键按下事件"""
        if not self.recording:
            # 使用信号确保在主线程中执行
            self.start_recording_signal.emit()

    def on_option_release(self):
        """处理Control键释放事件"""
        if self.recording:
            # 使用信号确保在主线程中执行
            self.stop_recording_signal.emit()

    def on_audio_captured(self, data):
        """音频数据捕获回调"""
        # 录音过程中不需要频繁更新状态，因为状态已经在start_recording时设置了
        pass

    def quit_application(self):
        """退出应用程序 - 简化版本"""
        try:
            # 1. 已移除：热键状态监控线程相关逻辑
            # if hasattr(self, '_monitor_should_stop'):
            #     self._monitor_should_stop = True
            
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
    
    # _delayed_paste 方法已移除，现在使用 lambda 函数直接处理延迟粘贴
    
    def _paste_and_reactivate(self, text):
        """执行粘贴操作 - 确保完全替换剪贴板内容"""
        try:
            # 检查剪贴板管理器是否已初始化
            if not self.clipboard_manager:
                return
            
            # 使用安全的复制粘贴方法，确保完全替换剪贴板内容
            success = self.clipboard_manager.safe_copy_and_paste(text)
            if not success:
                logging.warning("安全粘贴操作失败")
            
        except Exception as e:
            logging.error(f"粘贴操作失败: {e}")
            logging.error(traceback.format_exc())
    
    def _paste_and_reactivate_with_feedback(self, text):
        """执行粘贴操作并返回成功状态"""
        try:
            # 检查剪贴板管理器是否已初始化
            if not self.clipboard_manager:
                return False
            
            # 检查文本是否有效
            if not text or not text.strip():
                return False
            
            # 使用安全的复制粘贴方法，确保完全替换剪贴板内容
            success = self.clipboard_manager.safe_copy_and_paste(text)
            return success
            
        except Exception as e:
            logging.error(f"粘贴操作异常: {e}")
            logging.error(traceback.format_exc())
            return False
    
    def on_transcription_done(self, text):
        """转写完成的回调 - 优化剪贴板替换逻辑"""
        if text and text.strip():
            # 调试模式：显示转录完成信息
            # 调试信息已移除
            
            # 1. 更新UI并添加到历史记录（无论窗口是否可见）
            self.main_window.display_result(text)  # UI显示保留HTML格式
            
            # 2. 使用可配置的延迟时间，用lambda函数捕获当前文本
            delay = self.settings_manager.get_setting('paste.transcription_delay', 30)
            QTimer.singleShot(delay, lambda: self._paste_and_reactivate(text))
            
            # 转录完成
    
    def on_history_item_clicked(self, text):
        """处理历史记录点击事件"""
        try:
            # 检查文本是否有效
            if not text or not text.strip():
                # 只更新状态，不传递文本内容避免添加到历史记录
                self.main_window.update_status("点击失败")
                return
            
            # 1. 立即更新UI反馈（只更新状态，不传递文本）
            self.main_window.update_status("正在处理历史记录点击...")
            
            # 2. 检查剪贴板管理器是否可用
            if not self.clipboard_manager:
                self.main_window.update_status("点击失败")
                return
            
            # 3. 检查是否启用自动粘贴
            auto_paste_enabled = self.settings_manager.get_setting('paste.auto_paste_enabled', True)
            
            if auto_paste_enabled:
                # 使用极短延迟或立即执行粘贴（_paste_and_reactivate内部会处理复制）
                delay = self.settings_manager.get_setting('paste.history_click_delay', 0)  # 默认无延迟
                if delay <= 0:
                    # 立即执行粘贴
                    success = self._paste_and_reactivate_with_feedback(text)
                    if success:
                        self.main_window.update_status("历史记录已粘贴")
                    else:
                        self.main_window.update_status("粘贴失败")
                else:
                    # 使用lambda函数捕获当前文本，避免变量覆盖问题
                    QTimer.singleShot(delay, lambda: self._paste_and_reactivate_with_feedback(text))
            else:
                # 如果不自动粘贴，只复制到剪贴板
                success = self.clipboard_manager.copy_to_clipboard(text)
                if success:
                    self.main_window.update_status("历史记录已复制")
                else:
                    self.main_window.update_status("复制失败")
            
        except Exception as e:
            logging.error(f"处理历史记录点击事件失败: {e}")
            import traceback
            logging.error(traceback.format_exc())
            self.main_window.update_status("点击处理出错")

    def update_ui(self, status, result):
        """更新界面显示"""
        self.main_window.update_status(status)
        if result and result.strip():
            # 只有在不是历史记录相关操作的情况下才添加到历史记录
            history_related_statuses = [
                "准备粘贴历史记录", 
                "历史记录已复制", 
                "正在处理点击...",
                "正在处理历史记录点击...",
                "历史记录已粘贴",
                "粘贴失败",
                "复制失败",
                "点击失败",
                "点击处理出错"
            ]
            if status not in history_related_statuses:
                self.main_window.display_result(result, skip_history=False)
            else:
                # 对于历史记录相关操作，显示结果但不添加到历史记录
                self.main_window.display_result(result, skip_history=True)

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
                    # 已移除：启动热键状态监控
                    # self.start_hotkey_monitor()
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
                        # 已移除：启动热键状态监控
                        # self.start_hotkey_monitor()
                    except Exception as e2:
                        logging.error(f"重新初始化热键管理器失败: {e2}")
                        self.hotkey_manager = None
            else:
                try:
                    print("✓ 初始化热键管理器...")
                    from src.hotkey_manager_factory import HotkeyManagerFactory
                    scheme = self.settings_manager.get_hotkey_scheme()
                    self.hotkey_manager = HotkeyManagerFactory.create_hotkey_manager(scheme, self.settings_manager)
                    if self.hotkey_manager:
                        self.hotkey_manager.set_press_callback(self.on_option_press)
                        self.hotkey_manager.set_release_callback(self.on_option_release)
                        self.hotkey_manager.start_listening()
                        # 已移除：启动热键状态监控
                        # self.start_hotkey_monitor()
                        logging.info("热键管理器初始化完成")
                    else:
                        logging.error("热键管理器创建失败")
                except Exception as e:
                    logging.error(f"重新创建热键管理器失败: {e}")
                    logging.error(f"详细错误信息: {traceback.format_exc()}")
            
            print("✓ 进入主事件循环")
            logging.info("进入Qt主事件循环")
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

    # handle_mac_events方法已被eventFilter替代

    def show_settings(self):
        """显示设置窗口"""
        try:
            # 检查现有窗口是否存在且可见
            if hasattr(self, 'settings_window') and self.settings_window is not None:
                if self.settings_window.isVisible():
                    # 如果窗口已经打开，只需要激活它
                    self.settings_window.raise_()
                    self.settings_window.activateWindow()
                    return
                else:
                    # 如果窗口存在但不可见（已关闭），清理旧实例
                    self.settings_window = None
            
            # 创建新的设置窗口
            self.settings_window = SettingsWindow(
                settings_manager=self.settings_manager,
                audio_capture=self.audio_capture
            )
            
            # 连接信号
            self.settings_window.settings_saved.connect(
                self.apply_settings, 
                Qt.ConnectionType.QueuedConnection
            )
            
            # 连接窗口关闭信号，确保实例被清理
            self.settings_window.finished.connect(
                lambda: setattr(self, 'settings_window', None)
            )
            
            self.settings_window.show()
            self.settings_window.raise_()
            self.settings_window.activateWindow()
            
        except Exception as e:
            logging.error(f"显示设置窗口失败: {e}")
            import traceback
            logging.error(traceback.format_exc())
            # 如果出错，确保清理窗口实例
            self.settings_window = None
    


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
                        from src.hotkey_manager_factory import HotkeyManagerFactory
                        self.hotkey_manager = HotkeyManagerFactory.create_hotkey_manager(current_scheme, self.settings_manager)
                        if self.hotkey_manager:
                            self.hotkey_manager.set_press_callback(self.on_option_press)
                            self.hotkey_manager.set_release_callback(self.on_option_release)
                            self.hotkey_manager.update_hotkey(current_hotkey)
                            self.hotkey_manager.update_delay_settings()
                            self.hotkey_manager.start_listening()
                            logging.info(f"热键管理器已重新创建，使用方案: {current_scheme}")
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
                    logging.info(f"热键设置已更新，热键: {current_hotkey}")
                    
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
            import traceback
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
    logging.info("应用程序启动")
    
    # 设置全局异常处理器
    sys.excepthook = global_exception_handler
    
    try:
        app = Application()
        sys.exit(app.run())
    except Exception as e:
        logging.error(f"运行应用程序时出错: {e}")
        logging.error(traceback.format_exc())
        sys.exit(1)