"""
应用程序生命周期管理器包装器 - 第11步减法重构
将Application类中的应用程序生命周期管理相关方法迁移到此处
"""
import sys
import logging
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt


class ApplicationLifecycleManagerWrapper:
    """应用程序生命周期管理器包装器 - 纯粹的方法迁移，不改变任何逻辑"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("应用程序生命周期管理器包装器创建成功")
    
    def setup_mac_event_handling(self, app_instance):
        """设置macOS事件处理 - 从Application类移过来"""
        try:
            # 安装事件过滤器来处理dock图标点击
            app_instance.app.installEventFilter(app_instance)
            
            # 创建dock菜单
            self.setup_dock_menu(app_instance)
            
            pass  # macOS事件处理器已安装
        except Exception as e:
            logging.error(f"设置macOS事件处理失败: {e}")
    
    def setup_dock_menu(self, app_instance):
        """设置macOS Dock图标菜单（通过系统托盘实现） - 从Application类移过来"""
        try:
            # 在macOS上，dock菜单实际上是通过系统托盘图标的右键菜单实现的
            # 由于PyQt6没有直接的setDockMenu方法，我们使用系统托盘图标来提供类似功能
            # 系统托盘菜单已经在初始化时创建，这里只是确认功能可用
            if not (hasattr(app_instance, 'tray_icon') and app_instance.tray_icon.isVisible()):
                pass  # 静默处理托盘图标问题
            
        except Exception as e:
            logging.error(f"设置Dock菜单失败: {e}")
    
    def event_filter(self, app_instance, obj, event):
        """优化的事件过滤器，减少处理时间 - 从Application类移过来"""
        try:
            # 快速检查：只处理应用程序对象的特定事件
            if obj == app_instance.app and event.type() == 121:  # QEvent.Type.ApplicationActivate
                # 使用信号异步处理，避免阻塞事件循环
                app_instance.show_window_signal.emit()
                return False  # 继续传递事件
            
            # 对于其他事件，直接返回，减少处理时间
            return False
        except Exception:
            return False
    
    def quit_application(self, app_instance):
        """退出应用程序 - 从Application类移过来"""
        try:
            
            # 2. 停止热键监听，避免在清理过程中触发新的操作
            if hasattr(app_instance, 'hotkey_manager') and app_instance.hotkey_manager:
                try:
                    app_instance.hotkey_manager.stop_listening()
                except Exception as e:
                    logging.error(f"停止热键监听失败: {e}")
            
            # 3. 快速清理资源，避免长时间等待
            app_instance._quick_cleanup()
            
            # 4. 强制退出应用
            if hasattr(app_instance, 'app') and app_instance.app:
                app_instance.app.quit()
                
        except Exception as e:
            logging.error(f"退出应用程序时出错: {e}")
            # 强制退出
            import os
            os._exit(0)
    
    def restore_window_level(self, app_instance):
        """恢复窗口正常级别 - 从Application类移过来"""
        try:
            # 简化实现，只使用Qt方法确保窗口在前台
            app_instance.main_window.raise_()
            app_instance.main_window.activateWindow()
        except Exception as e:
            logging.error(f"恢复窗口级别时出错: {e}")
    
    def show_window_internal(self, app_instance):
        """在主线程中显示窗口 - 从Application类移过来"""
        try:
            # 在 macOS 上使用 NSWindow 来激活窗口
            if sys.platform == 'darwin':
                try:
                    from AppKit import NSApplication, NSWindow
                    from PyQt6.QtGui import QWindow

                    # 获取应用
                    app = NSApplication.sharedApplication()

                    # 显示窗口
                    if not app_instance.main_window.isVisible():
                        app_instance.main_window.show()

                    # 获取窗口句柄
                    window_handle = app_instance.main_window.windowHandle()
                    if window_handle:
                        # 在PyQt6中使用winId()获取原生窗口ID
                        window_id = app_instance.main_window.winId()
                        if window_id:
                            # 激活应用程序
                            app.activateIgnoringOtherApps_(True)

                            # 使用Qt方法激活窗口
                            app_instance.main_window.raise_()
                            app_instance.main_window.activateWindow()
                            app_instance.main_window.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
                        else:
                            # 如果无法获取窗口ID，使用基本方法
                            app.activateIgnoringOtherApps_(True)
                            app_instance.main_window.raise_()
                            app_instance.main_window.activateWindow()
                    else:
                        # 如果无法获取窗口句柄，使用基本方法
                        app.activateIgnoringOtherApps_(True)
                        app_instance.main_window.raise_()
                        app_instance.main_window.activateWindow()

                except Exception as e:
                    logging.error(f"激活窗口时出错: {e}")
                    # 如果原生方法失败，使用 Qt 方法
                    app_instance.main_window.show()
                    app_instance.main_window.raise_()
                    app_instance.main_window.activateWindow()
            else:
                # 非 macOS 系统的处理
                if not app_instance.main_window.isVisible():
                    app_instance.main_window.show()
                app_instance.main_window.raise_()
                app_instance.main_window.activateWindow()

            pass  # 窗口已显示
        except Exception as e:
            logging.error(f"显示窗口失败: {e}")
    
    def get_status(self):
        """获取管理器状态"""
        return {
            'name': 'ApplicationLifecycleManagerWrapper',
            'description': '应用程序生命周期管理器包装器'
        }
