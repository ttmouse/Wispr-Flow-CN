"""
加载管理器包装器
完全兼容原始AppLoader和LoadingSplash接口，作为第五步替换
"""

import logging
from app_loader import AppLoader as OriginalAppLoader, LoadingSplash as OriginalLoadingSplash


class LoadingManagerWrapper:
    """加载管理器包装器 - 第五步模块化替换"""
    
    def __init__(self, app_instance, settings_manager):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._original_loader = None
        self._original_splash = None
        self._app_instance = app_instance
        self._settings_manager = settings_manager
        self._initialized = False
        self._initialize()
    
    def _initialize(self):
        """初始化原始加载器 - 延迟初始化避免焦点问题"""
        try:
            # 延迟初始化，避免在包装器创建时立即初始化加载器
            self._original_loader = None
            self._original_splash = None
            self._initialized = False
            self.logger.info("加载管理器包装器创建成功（延迟初始化）")
        except Exception as e:
            self.logger.error(f"加载管理器包装器创建失败: {e}")
            raise
    
    def _ensure_initialized(self):
        """确保原始加载器已初始化"""
        if not self._initialized:
            try:
                self._original_loader = OriginalAppLoader(self._app_instance, self._settings_manager)
                self._original_splash = OriginalLoadingSplash()
                self._initialized = True
                self.logger.info("加载管理器延迟初始化成功")
            except Exception as e:
                self.logger.error(f"加载管理器延迟初始化失败: {e}")
                raise
    
    # AppLoader方法委托
    def start_loading(self):
        """开始异步加载"""
        self._ensure_initialized()
        return self._original_loader.start_loading()
    
    def stop_loading(self):
        """停止加载"""
        if self._initialized and self._original_loader:
            return self._original_loader.stop_loading()
    
    # LoadingSplash方法委托
    def show_splash(self):
        """显示启动画面"""
        self._ensure_initialized()
        return self._original_splash.show()
    
    def hide_splash(self):
        """隐藏启动画面"""
        if self._initialized and self._original_splash:
            return self._original_splash.hide()
    
    def update_progress(self, progress, message):
        """更新进度"""
        if self._initialized and self._original_splash:
            return self._original_splash.update_progress(progress, message)
    
    # 信号属性委托
    @property
    def progress_updated(self):
        """进度更新信号"""
        self._ensure_initialized()
        return getattr(self._original_loader, 'progress_updated', None)
    
    @property
    def component_loaded(self):
        """组件加载信号"""
        self._ensure_initialized()
        return getattr(self._original_loader, 'component_loaded', None)
    
    @property
    def loading_completed(self):
        """加载完成信号"""
        self._ensure_initialized()
        return getattr(self._original_loader, 'loading_completed', None)
    
    @property
    def loading_failed(self):
        """加载失败信号"""
        self._ensure_initialized()
        return getattr(self._original_loader, 'loading_failed', None)
    
    # 属性委托
    @property
    def splash(self):
        """启动画面对象"""
        if self._initialized:
            return self._original_splash
        return None
    
    @property
    def app_loader(self):
        """应用加载器对象"""
        if self._initialized:
            return self._original_loader
        return None
    
    @property
    def is_loading(self):
        """是否正在加载"""
        if self._initialized and self._original_loader:
            return getattr(self._original_loader, 'is_loading', False)
        return False
    
    @property
    def components(self):
        """组件字典"""
        if self._initialized and self._original_loader:
            return getattr(self._original_loader, 'components', {})
        return {}
    
    # 委托所有其他方法调用给原始加载器
    def __getattr__(self, name):
        """委托所有其他方法调用给原始加载器"""
        self._ensure_initialized()
        
        # 优先从loader获取属性
        if self._original_loader and hasattr(self._original_loader, name):
            return getattr(self._original_loader, name)
        
        # 然后从splash获取属性
        if self._original_splash and hasattr(self._original_splash, name):
            return getattr(self._original_splash, name)
        
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def get_status(self):
        """获取管理器状态"""
        return {
            'name': 'LoadingManagerWrapper',
            'initialized': self._initialized,
            'original_loader_type': type(self._original_loader).__name__ if self._initialized and self._original_loader else None,
            'original_splash_type': type(self._original_splash).__name__ if self._initialized and self._original_splash else None,
            'is_loading': self.is_loading,
            'components_count': len(self.components) if self._initialized else 0
        }
