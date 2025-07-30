"""
状态管理器包装器
完全兼容原始StateManager接口，作为第二步替换
"""

import logging
from state_manager import StateManager as OriginalStateManager


class StateManagerWrapper:
    """状态管理器包装器 - 第二步模块化替换"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._original_manager = None
        self._initialize()
    
    def _initialize(self):
        """初始化原始状态管理器 - 延迟初始化避免焦点问题"""
        try:
            # 延迟初始化，避免在包装器创建时立即初始化音效
            # 这样可以避免线程移动导致的焦点问题
            self._original_manager = None
            self._initialized = False
            self.logger.info("状态管理器包装器创建成功（延迟初始化）")
        except Exception as e:
            self.logger.error(f"状态管理器包装器创建失败: {e}")
            raise

    def _ensure_initialized(self):
        """确保原始管理器已初始化"""
        if not self._initialized:
            try:
                self._original_manager = OriginalStateManager()
                self._initialized = True
                self.logger.info("状态管理器延迟初始化成功")
            except Exception as e:
                self.logger.error(f"状态管理器延迟初始化失败: {e}")
                raise
    
    # 完全委托给原始管理器的所有方法和属性
    def start_recording(self):
        """开始录音"""
        self._ensure_initialized()
        return self._original_manager.start_recording()

    def stop_recording(self):
        """停止录音"""
        self._ensure_initialized()
        return self._original_manager.stop_recording()

    def update_status(self, status):
        """更新状态"""
        self._ensure_initialized()
        return self._original_manager.update_status(status)
    
    def reload_hotwords(self):
        """重新加载热词"""
        self._ensure_initialized()
        return self._original_manager.reload_hotwords()

    def get_hotwords(self):
        """获取热词列表"""
        self._ensure_initialized()
        return self._original_manager.get_hotwords()

    def cleanup(self):
        """清理资源"""
        if self._initialized and self._original_manager and hasattr(self._original_manager, 'cleanup'):
            return self._original_manager.cleanup()
    
    # 属性委托
    @property
    def status(self):
        """状态属性"""
        if self._initialized and self._original_manager:
            return getattr(self._original_manager, 'status', '就绪')
        return '就绪'

    @status.setter
    def status(self, value):
        """设置状态属性"""
        self._ensure_initialized()
        if self._original_manager:
            self._original_manager.status = value

    @property
    def status_changed(self):
        """状态变更信号"""
        self._ensure_initialized()
        return getattr(self._original_manager, 'status_changed', None)

    @property
    def funasr_engine(self):
        """FunASR引擎属性"""
        if self._initialized and self._original_manager:
            return getattr(self._original_manager, 'funasr_engine', None)
        return None

    @funasr_engine.setter
    def funasr_engine(self, value):
        """设置FunASR引擎属性"""
        self._ensure_initialized()
        if self._original_manager:
            self._original_manager.funasr_engine = value
    
    # 委托所有其他方法调用给原始管理器
    def __getattr__(self, name):
        """委托所有其他方法调用给原始管理器"""
        self._ensure_initialized()
        if self._original_manager and hasattr(self._original_manager, name):
            return getattr(self._original_manager, name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def get_status(self):
        """获取管理器状态"""
        return {
            'name': 'StateManagerWrapper',
            'initialized': self._initialized,
            'original_manager_type': type(self._original_manager).__name__ if self._initialized and self._original_manager else None,
            'current_status': self.status
        }
