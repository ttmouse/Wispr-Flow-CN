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
        """初始化原始加载器 - 立即初始化splash避免启动问题"""
        try:
            # 立即初始化splash，因为启动时就需要显示
            self._original_loader = OriginalAppLoader(self._app_instance, self._settings_manager)
            self._original_splash = OriginalLoadingSplash()
            self._initialized = True
            self.logger.info("加载管理器包装器初始化成功")
        except Exception as e:
            self.logger.error(f"加载管理器包装器初始化失败: {e}")
            raise
    
    def _ensure_initialized(self):
        """确保原始加载器已初始化"""
        # 已经在_initialize中初始化了，这里只是检查
        if not self._initialized:
            raise RuntimeError("加载管理器未正确初始化")
    
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

    def start_async_loading(self, app_instance):
        """启动异步加载任务 - 从Application类移过来"""
        from PyQt6.QtCore import QTimer

        # 延迟启动加载，让UI先显示
        self._load_timer = QTimer()
        self._load_timer.setSingleShot(True)
        self._load_timer.timeout.connect(self._original_loader.start_loading)
        self._load_timer.start(500)  # 500ms后开始加载

    def handle_component_loaded(self, app_instance, component_name, component):
        """处理组件加载完成 - 从Application类移过来"""
        from PyQt6.QtCore import QThread, QMetaObject, Qt, Q_ARG
        from PyQt6.QtWidgets import QApplication
        import logging

        try:
            # 确保在主线程中执行setattr操作，避免SIGTRAP崩溃
            if QThread.currentThread() != QApplication.instance().thread():
                # 使用QMetaObject.invokeMethod确保在主线程中执行
                QMetaObject.invokeMethod(
                    app_instance, "_set_component_in_main_thread",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(str, component_name),
                    Q_ARG(object, component)
                )
                return

            # 在主线程中安全地设置组件属性
            self.set_component_safely(app_instance, component_name, component)

        except Exception as e:
            logging.error(f"组件 {component_name} 加载后处理失败: {e}")

    def set_component_safely(self, app_instance, component_name, component):
        """安全地设置组件属性和连接 - 从Application类移过来"""
        import logging
        try:
            # 将组件赋值给应用实例
            setattr(app_instance, component_name, component)

            # 特殊处理某些组件
            if component_name == 'funasr_engine' and component:
                # 关联到状态管理器
                if hasattr(app_instance, 'state_manager') and app_instance.state_manager:
                    app_instance.state_manager.funasr_engine = component

            elif component_name == 'hotkey_manager' and component:
                # 设置热键回调
                component.set_press_callback(app_instance.on_option_press)
                component.set_release_callback(app_instance.on_option_release)

            elif component_name == 'audio_capture_thread' and component:
                # 连接音频捕获信号
                component.audio_captured.connect(app_instance.on_audio_captured)
                component.recording_stopped.connect(app_instance.stop_recording)

        except Exception as e:
            logging.error(f"安全设置组件 {component_name} 失败: {e}")

    def handle_loading_completed(self, app_instance):
        """处理加载完成 - 从Application类移过来"""
        import logging
        try:
            # 隐藏启动界面
            if hasattr(self, '_original_splash') and self._original_splash:
                self._original_splash.close()

            # 显示主窗口并置顶
            app_instance.main_window.show_window_internal()

            # 完成最终初始化
            self.finalize_initialization(app_instance)

            # 标记初始化完成
            self.mark_initialization_complete(app_instance)

        except Exception as e:
            logging.error(f"加载完成处理失败: {e}")

    def handle_loading_failed(self, app_instance, error_message):
        """处理加载失败 - 从Application类移过来"""
        import logging
        logging.error(f"组件加载失败: {error_message}")

        # 隐藏启动界面
        if hasattr(self, '_original_splash') and self._original_splash:
            self._original_splash.close()

        # 显示主窗口并置顶（即使部分组件失败）
        app_instance.main_window.show_window_internal()

        # 显示错误信息
        app_instance.update_ui_signal.emit("⚠️ 部分组件初始化失败", error_message)

    def finalize_initialization(self, app_instance):
        """完成初始化设置 - 从Application类移过来"""
        import logging
        try:
            # 设置连接
            app_instance.setup_connections()

            # 应用设置
            app_instance.apply_settings()

            logging.debug("最终初始化完成")
        except Exception as e:
            logging.error(f"初始化设置失败: {e}")

    def mark_initialization_complete(self, app_instance):
        """标记初始化完成 - 从Application类移过来"""
        import logging
        try:
            # 标记主窗口初始化完成
            if hasattr(app_instance.main_window, '_initialization_complete'):
                app_instance.main_window._initialization_complete = True

            # 通知初始化完成
            app_instance.update_ui_signal.emit("✓ 应用初始化完成", "")
        except Exception as e:
            logging.error(f"标记初始化完成失败: {e}")

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
