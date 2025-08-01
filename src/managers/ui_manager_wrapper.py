"""
UI管理器包装器
完全兼容原始MainWindow接口，作为第三步替换
"""

import logging
from ui.main_window import MainWindow as OriginalMainWindow


class UIManagerWrapper:
    """UI管理器包装器 - 第三步模块化替换"""
    
    def __init__(self, app_instance=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._original_window = None
        self._app_instance = app_instance
        self._initialized = False
        self._initialize()
    
    def _initialize(self):
        """初始化原始主窗口 - 延迟初始化避免焦点问题"""
        try:
            # 延迟初始化，避免在包装器创建时立即初始化UI
            self._original_window = None
            self._initialized = False
            self.logger.info("UI管理器包装器创建成功（延迟初始化）")
        except Exception as e:
            self.logger.error(f"UI管理器包装器创建失败: {e}")
            raise
    
    def _ensure_initialized(self):
        """确保原始主窗口已初始化"""
        if not self._initialized:
            try:
                self._original_window = OriginalMainWindow(app_instance=self._app_instance)
                self._initialized = True
                self.logger.info("UI管理器延迟初始化成功")
            except Exception as e:
                self.logger.error(f"UI管理器延迟初始化失败: {e}")
                raise
    
    # 完全委托给原始主窗口的所有方法
    def set_state_manager(self, state_manager):
        """设置状态管理器"""
        self._ensure_initialized()
        return self._original_window.set_state_manager(state_manager)
    
    def update_status(self, status):
        """更新状态显示"""
        self._ensure_initialized()
        return self._original_window.update_status(status)
    
    def display_result(self, text, skip_history=False):
        """显示识别结果"""
        self._ensure_initialized()
        return self._original_window.display_result(text, skip_history)
    
    def _show_window_internal(self):
        """在主线程中显示窗口"""
        self._ensure_initialized()
        return self._original_window._show_window_internal()
    
    def hide(self):
        """隐藏窗口"""
        if self._initialized and self._original_window:
            return self._original_window.hide()
    
    def show(self):
        """显示窗口"""
        self._ensure_initialized()
        return self._original_window.show()
    
    def close(self):
        """关闭窗口"""
        if self._initialized and self._original_window:
            return self._original_window.close()
    
    def raise_(self):
        """将窗口置于前台"""
        self._ensure_initialized()
        return self._original_window.raise_()
    
    def activateWindow(self):
        """激活窗口"""
        self._ensure_initialized()
        return self._original_window.activateWindow()
    
    def setFocus(self, reason):
        """设置焦点"""
        self._ensure_initialized()
        return self._original_window.setFocus(reason)
    
    def isVisible(self):
        """检查窗口是否可见"""
        if self._initialized and self._original_window:
            return self._original_window.isVisible()
        return False
    
    def windowHandle(self):
        """获取窗口句柄"""
        self._ensure_initialized()
        return self._original_window.windowHandle()
    
    def winId(self):
        """获取窗口ID"""
        self._ensure_initialized()
        return self._original_window.winId()
    
    # 属性委托
    @property
    def record_button_clicked(self):
        """录音按钮点击信号"""
        self._ensure_initialized()
        return getattr(self._original_window, 'record_button_clicked', None)
    
    @property
    def history_item_clicked(self):
        """历史记录项点击信号"""
        self._ensure_initialized()
        return getattr(self._original_window, 'history_item_clicked', None)
    
    @property
    def _initialization_complete(self):
        """初始化完成标志"""
        if self._initialized and self._original_window:
            return getattr(self._original_window, '_initialization_complete', False)
        return False
    
    @_initialization_complete.setter
    def _initialization_complete(self, value):
        """设置初始化完成标志"""
        self._ensure_initialized()
        if self._original_window:
            self._original_window._initialization_complete = value
    
    # 委托所有其他方法调用给原始主窗口
    def __getattr__(self, name):
        """委托所有其他方法调用给原始主窗口"""
        self._ensure_initialized()
        if self._original_window and hasattr(self._original_window, name):
            return getattr(self._original_window, name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def show_window_safe(self):
        """显示主窗口（可以从其他线程调用）- 从Application类移过来"""
        from PyQt6.QtCore import QThread
        from PyQt6.QtWidgets import QApplication

        # 如果在主线程中，直接调用
        if QThread.currentThread() == QApplication.instance().thread():
            self.show_window_internal()
        else:
            # 在其他线程中，需要通过信号机制
            # 这里需要外部提供信号发射机制
            if hasattr(self, '_show_window_signal'):
                self._show_window_signal.emit()

    def set_show_window_signal(self, signal):
        """设置显示窗口的信号"""
        self._show_window_signal = signal

    def set_app_instance(self, app_instance):
        """设置应用实例"""
        self._ensure_initialized()
        if hasattr(self._original_window, 'set_app_instance'):
            return self._original_window.set_app_instance(app_instance)
        # 如果原始窗口没有这个方法，就存储在包装器中
        self._app_instance = app_instance

    def apply_settings(self):
        """应用设置"""
        self._ensure_initialized()
        if hasattr(self._original_window, 'apply_settings'):
            return self._original_window.apply_settings()
        # 如果原始窗口没有这个方法，就静默处理
        pass

    def show_window_internal(self):
        """在主线程中显示窗口 - 从Application类移过来"""
        import sys
        import logging
        from PyQt6.QtCore import Qt

        try:
            # 在 macOS 上使用 NSWindow 来激活窗口
            if sys.platform == 'darwin':
                try:
                    from AppKit import NSApplication, NSWindow
                    from PyQt6.QtGui import QWindow

                    # 获取应用
                    app = NSApplication.sharedApplication()

                    # 显示窗口
                    self._ensure_initialized()
                    if not self._original_window.isVisible():
                        self._original_window.show()

                    # 获取窗口句柄
                    window_handle = self._original_window.windowHandle()
                    if window_handle:
                        # 在PyQt6中使用winId()获取原生窗口ID
                        window_id = self._original_window.winId()
                        if window_id:
                            # 激活应用程序
                            app.activateIgnoringOtherApps_(True)

                            # 使用Qt方法激活窗口
                            self._original_window.raise_()
                            self._original_window.activateWindow()
                            self._original_window.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
                        else:
                            # 如果无法获取窗口ID，使用基本方法
                            app.activateIgnoringOtherApps_(True)
                            self._original_window.raise_()
                            self._original_window.activateWindow()
                    else:
                        # 如果无法获取窗口句柄，使用基本方法
                        app.activateIgnoringOtherApps_(True)
                        self._original_window.raise_()
                        self._original_window.activateWindow()

                except Exception as e:
                    logging.error(f"激活窗口时出错: {e}")
                    # 如果原生方法失败，使用 Qt 方法
                    self._original_window.show()
                    self._original_window.raise_()
                    self._original_window.activateWindow()
            else:
                # 非 macOS 系统的处理
                self._ensure_initialized()
                if not self._original_window.isVisible():
                    self._original_window.show()
                self._original_window.raise_()
                self._original_window.activateWindow()

        except Exception as e:
            logging.error(f"显示窗口失败: {e}")

    def get_status(self):
        """获取管理器状态"""
        return {
            'name': 'UIManagerWrapper',
            'initialized': self._initialized,
            'original_window_type': type(self._original_window).__name__ if self._initialized and self._original_window else None,
            'window_visible': self.isVisible() if self._initialized else False
        }
