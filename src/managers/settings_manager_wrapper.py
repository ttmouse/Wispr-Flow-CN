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
    
    def get_status(self):
        """获取管理器状态"""
        return {
            'name': 'SettingsManagerWrapper',
            'initialized': self._initialized,
            'original_manager_type': type(self._original_manager).__name__ if self._initialized and self._original_manager else None
        }
