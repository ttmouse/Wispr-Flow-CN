"""
设置管理器包装器
完全兼容原始SettingsManager接口，作为第一步替换
"""

import logging
from settings_manager import SettingsManager as OriginalSettingsManager


class SettingsManagerWrapper:
    """设置管理器包装器 - 第一步模块化替换"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._original_manager = None
        self._initialize()
    
    def _initialize(self):
        """初始化原始设置管理器 - 延迟初始化避免焦点问题"""
        try:
            # 延迟初始化，避免在包装器创建时立即初始化
            self._original_manager = None
            self._initialized = False
            self.logger.info("设置管理器包装器创建成功（延迟初始化）")
        except Exception as e:
            self.logger.error(f"设置管理器包装器创建失败: {e}")
            raise

    def _ensure_initialized(self):
        """确保原始管理器已初始化"""
        if not self._initialized:
            try:
                self._original_manager = OriginalSettingsManager()
                self._initialized = True
                self.logger.info("设置管理器延迟初始化成功")
            except Exception as e:
                self.logger.error(f"设置管理器延迟初始化失败: {e}")
                raise
    
    # 完全委托给原始管理器的所有方法
    def get_setting(self, key, default=None):
        """获取设置值"""
        self._ensure_initialized()
        return self._original_manager.get_setting(key, default)

    def set_setting(self, key, value):
        """设置值"""
        self._ensure_initialized()
        return self._original_manager.set_setting(key, value)
    
    def save_settings(self):
        """保存设置"""
        self._ensure_initialized()
        return self._original_manager.save_settings()

    def load_settings(self):
        """加载设置"""
        self._ensure_initialized()
        return self._original_manager.load_settings()

    def get_hotkey(self):
        """获取热键设置"""
        self._ensure_initialized()
        return self._original_manager.get_hotkey()

    def get_hotkey_scheme(self):
        """获取热键方案"""
        self._ensure_initialized()
        return self._original_manager.get_hotkey_scheme()

    def set_hotkey_scheme(self, scheme):
        """设置热键方案"""
        self._ensure_initialized()
        return self._original_manager.set_hotkey_scheme(scheme)

    def get_audio_settings(self):
        """获取音频设置"""
        self._ensure_initialized()
        return self._original_manager.get_audio_settings()

    def get_ui_settings(self):
        """获取UI设置"""
        self._ensure_initialized()
        return self._original_manager.get_ui_settings()

    def reset_to_defaults(self):
        """重置为默认设置"""
        self._ensure_initialized()
        return self._original_manager.reset_to_defaults()

    def export_settings(self, file_path):
        """导出设置"""
        self._ensure_initialized()
        return self._original_manager.export_settings(file_path)

    def import_settings(self, file_path):
        """导入设置"""
        self._ensure_initialized()
        return self._original_manager.import_settings(file_path)
    
    # 添加任何其他原始管理器可能有的方法
    def __getattr__(self, name):
        """委托所有其他方法调用给原始管理器"""
        self._ensure_initialized()
        if self._original_manager and hasattr(self._original_manager, name):
            return getattr(self._original_manager, name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def show_settings(self, audio_capture=None):
        """显示设置窗口 - 从Application类移过来的方法"""
        self._ensure_initialized()
        try:
            from ui.macos_settings_window import MacOSSettingsWindow
            from PyQt6.QtCore import Qt
            import logging
            import traceback

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
            self.settings_window = MacOSSettingsWindow(
                settings_manager=self._original_manager,
                audio_capture=audio_capture
            )

            # 连接信号 - 需要外部提供apply_settings回调
            if hasattr(self, '_apply_settings_callback'):
                self.settings_window.settings_saved.connect(
                    self._apply_settings_callback,
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
            logging.error(traceback.format_exc())
            # 如果出错，确保清理窗口实例
            self.settings_window = None

    def set_apply_settings_callback(self, callback):
        """设置应用设置的回调函数"""
        self._apply_settings_callback = callback

    def get_status(self):
        """获取管理器状态"""
        return {
            'name': 'SettingsManagerWrapper',
            'initialized': self._initialized,
            'original_manager_type': type(self._original_manager).__name__ if self._initialized and self._original_manager else None
        }
