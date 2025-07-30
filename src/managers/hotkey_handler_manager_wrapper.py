"""
热键处理管理器包装器 - 第9步减法重构
将Application类中的热键处理相关方法迁移到此处
"""
import logging
from functools import wraps
from PyQt6.QtCore import QThread, QMetaObject, Qt, pyqtSlot
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon


def handle_common_exceptions(show_error=True):
    """统一异常处理装饰器 - 从main.py复制过来"""
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
            except Exception as e:
                error_msg = f"操作失败: {e}"
                logging.error(error_msg)
                if show_error and hasattr(self, 'tray_icon') and self.tray_icon:
                    self.tray_icon.showMessage(
                        "操作失败",
                        str(e),
                        QSystemTrayIcon.MessageIcon.Critical,
                        3000
                    )
        return wrapper
    return decorator


class HotkeyHandlerManagerWrapper:
    """热键处理管理器包装器 - 纯粹的方法迁移，不改变任何逻辑"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("热键处理管理器包装器创建成功")
    
    @pyqtSlot()
    def safe_restart_hotkey_manager(self, app_instance):
        """安全的热键管理器重启方法 - 从Application类移过来"""
        try:
            # 确保在主线程中执行
            if QThread.currentThread() != QApplication.instance().thread():
                QMetaObject.invokeMethod(
                    app_instance, "restart_hotkey_manager",
                    Qt.ConnectionType.QueuedConnection
                )
                return
            
            # 调用实际的重启方法
            self.restart_hotkey_manager(app_instance)
            
        except Exception as e:
            logging.error(f"安全重启热键管理器失败: {e}")
            # 显示错误通知
            if hasattr(app_instance, 'tray_icon') and app_instance.tray_icon:
                app_instance.tray_icon.showMessage(
                    "热键功能",
                    "热键功能重启失败，请检查权限设置",
                    QSystemTrayIcon.MessageIcon.Warning,
                    3000
                )
    
    @handle_common_exceptions(show_error=True)
    def restart_hotkey_manager(self, app_instance):
        """重启热键管理器 - 从Application类移过来"""
        logging.debug("开始重启热键管理器")
        
        # 停止现有的热键管理器
        if app_instance.hotkey_manager:
            try:
                app_instance.hotkey_manager.stop_listening()
                if hasattr(app_instance.hotkey_manager, 'cleanup'):
                    app_instance.hotkey_manager.cleanup()
            except Exception as e:
                logging.error(f"停止现有热键管理器失败: {e}")
        
        # 重新创建热键管理器
        try:
            try:
                from src.hotkey_manager_factory import HotkeyManagerFactory
            except ImportError:
                from hotkey_manager_factory import HotkeyManagerFactory
            
            # 获取热键方案设置
            scheme = app_instance.settings_manager.get_hotkey_scheme()
            
            # 使用工厂模式创建热键管理器
            app_instance.hotkey_manager = HotkeyManagerFactory.create_hotkey_manager(scheme, app_instance.settings_manager)
            
            if app_instance.hotkey_manager:
                app_instance.hotkey_manager.set_press_callback(app_instance.on_option_press)
                app_instance.hotkey_manager.set_release_callback(app_instance.on_option_release)
                
                # 应用当前热键设置
                current_hotkey = app_instance.settings_manager.get_hotkey()
                app_instance.hotkey_manager.update_hotkey(current_hotkey)
                app_instance.hotkey_manager.update_delay_settings()
                
                # 启动监听
                app_instance.hotkey_manager.start_listening()
                
                logging.debug(f"热键管理器重启成功，使用方案: {scheme}")
                
                # 显示成功通知
                if hasattr(app_instance, 'tray_icon') and app_instance.tray_icon:
                    app_instance.tray_icon.showMessage(
                        "热键功能",
                        "热键功能已成功重启",
                        QSystemTrayIcon.MessageIcon.Information,
                        3000
                    )
            else:
                logging.error(f"热键管理器创建失败，方案: {scheme}")
                app_instance.hotkey_manager = None
                
        except Exception as e:
            logging.error(f"热键管理器重启失败: {e}")
            app_instance.hotkey_manager = None
    
    def on_option_press(self, app_instance):
        """处理Control键按下事件 - 从Application类移过来"""
        if app_instance._can_start_recording():
            # 使用信号确保在主线程中执行
            app_instance.start_recording_signal.emit()

    def on_option_release(self, app_instance):
        """处理Control键释放事件 - 从Application类移过来，优化防卡死"""
        try:
            # 快速状态检查，避免重复处理
            if not app_instance._can_stop_recording():
                logging.debug("无法停止录音：状态检查失败")
                return

            # 防止重复触发：检查是否已经在处理停止录音
            if hasattr(app_instance, '_stopping_recording') and app_instance._stopping_recording:
                logging.debug("正在停止录音中，忽略重复触发")
                return

            # 设置停止标志
            app_instance._stopping_recording = True

            # 使用信号确保在主线程中执行，并添加超时保护
            try:
                app_instance.stop_recording_signal.emit()
                logging.debug("停止录音信号已发送")
            except Exception as e:
                logging.error(f"发送停止录音信号失败: {e}")
                # 重置停止标志
                app_instance._stopping_recording = False

            # 使用定时器重置停止标志，防止永久锁定
            from PyQt6.QtCore import QTimer
            def reset_stopping_flag():
                if hasattr(app_instance, '_stopping_recording'):
                    app_instance._stopping_recording = False
                    logging.debug("停止录音标志已重置")

            QTimer.singleShot(3000, reset_stopping_flag)  # 3秒后重置标志

        except Exception as e:
            logging.error(f"处理热键释放事件失败: {e}")
            # 确保重置停止标志
            if hasattr(app_instance, '_stopping_recording'):
                app_instance._stopping_recording = False
    
    def get_status(self):
        """获取管理器状态"""
        return {
            'name': 'HotkeyHandlerManagerWrapper',
            'description': '热键处理管理器包装器'
        }
