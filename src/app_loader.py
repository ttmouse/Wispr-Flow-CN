import threading
import time
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QSplashScreen, QLabel, QProgressBar, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont
import os

class AppLoader(QObject):
    """应用程序异步加载器"""
    
    # 定义信号
    progress_updated = pyqtSignal(int, str)  # 进度值, 状态文本
    component_loaded = pyqtSignal(str, object)  # 组件名, 组件对象
    loading_completed = pyqtSignal()
    loading_failed = pyqtSignal(str)  # 错误信息
    
    def __init__(self, app_instance, settings_manager):
        super().__init__()
        self.app_instance = app_instance
        self.settings_manager = settings_manager
        self.loading_thread = None
        self.is_loading = False
        
        # 组件加载状态
        self.components = {
            'funasr_engine': None,
            'hotkey_manager': None,
            'clipboard_manager': None,
            'context_manager': None,
            'audio_manager': None,
            'audio_capture_thread': None
        }
        
    def start_loading(self):
        """开始异步加载"""
        if self.is_loading:
            return
            
        self.is_loading = True
        self.loading_thread = threading.Thread(target=self._load_components, daemon=True)
        self.loading_thread.start()
        
    def _load_components(self):
        """在后台线程中加载组件"""
        try:
            total_steps = 6
            current_step = 0
            
            # 1. 检查权限（快速）
            current_step += 1
            self.progress_updated.emit(int(current_step/total_steps*100), "检查系统权限...")
            self._check_permissions_async()
            time.sleep(0.1)  # 给UI更新时间
            
            # 2. 初始化FunASR引擎（最耗时）
            current_step += 1
            self.progress_updated.emit(int(current_step/total_steps*100), "加载语音识别模型...")
            self._load_funasr_engine()
            
            # 3. 初始化热键管理器
            current_step += 1
            self.progress_updated.emit(int(current_step/total_steps*100), "初始化热键管理器...")
            self._load_hotkey_manager()
            
            # 4. 初始化剪贴板管理器
            current_step += 1
            self.progress_updated.emit(int(current_step/total_steps*100), "初始化剪贴板管理器...")
            self._load_clipboard_manager()
            
            # 5. 初始化其他组件
            current_step += 1
            self.progress_updated.emit(int(current_step/total_steps*100), "初始化其他组件...")
            self._load_other_components()
            
            # 6. 完成初始化
            current_step += 1
            self.progress_updated.emit(100, "初始化完成")
            time.sleep(0.2)  # 让用户看到完成状态
            
            self.loading_completed.emit()
            
        except Exception as e:
            self.loading_failed.emit(str(e))
        finally:
            self.is_loading = False
            
    def _check_permissions_async(self):
        """异步检查权限"""
        try:
            if hasattr(self.app_instance, '_check_development_permissions'):
                self.app_instance._check_development_permissions()
        except Exception as e:
            import logging
            logging.error(f"权限检查失败: {e}")
            
    def _load_funasr_engine(self):
        """加载FunASR引擎"""
        try:
            from src.funasr_engine import FunASREngine
            engine = FunASREngine(self.settings_manager)
            self.components['funasr_engine'] = engine
            self.component_loaded.emit('funasr_engine', engine)
            
            # 批量更新模型缓存和路径，避免重复保存
            if engine.is_ready:
                model_paths = engine.get_model_paths()
                asr_available = bool(model_paths.get('asr_model_path'))
                punc_available = bool(model_paths.get('punc_model_path'))
                
                # 批量更新所有设置，只保存一次
                from datetime import datetime
                now = datetime.now().isoformat()
                settings_to_update = {
                    'cache.models.last_check': now,
                    'cache.models.asr_available': asr_available,
                    'cache.models.punc_available': punc_available
                }
                
                # 添加模型路径设置
                if 'asr_model_path' in model_paths:
                    settings_to_update['asr.model_path'] = model_paths['asr_model_path']
                if 'punc_model_path' in model_paths:
                    settings_to_update['asr.punc_model_path'] = model_paths['punc_model_path']
                
                # 一次性保存所有设置
                self.settings_manager.set_multiple_settings(settings_to_update)
            else:
                self.settings_manager.update_models_cache(False, False)
                
        except Exception as e:
            import logging
            logging.error(f"FunASR引擎加载失败: {e}")
            self.components['funasr_engine'] = None
            
    def _load_hotkey_manager(self):
        """加载热键管理器"""
        try:
            from src.hotkey_manager import HotkeyManager
            manager = HotkeyManager(self.settings_manager)
            self.components['hotkey_manager'] = manager
            self.component_loaded.emit('hotkey_manager', manager)
        except Exception as e:
            import logging
            logging.error(f"热键管理器加载失败: {e}")
            self.components['hotkey_manager'] = None
            
    def _load_clipboard_manager(self):
        """加载剪贴板管理器"""
        try:
            from src.clipboard_manager import ClipboardManager
            # 启用调试模式以获取详细日志
            debug_mode = self.settings_manager.get_setting('clipboard_debug', True)  # 默认启用调试
            manager = ClipboardManager(debug_mode=debug_mode)
            self.components['clipboard_manager'] = manager
            self.component_loaded.emit('clipboard_manager', manager)
            pass  # 剪贴板管理器已加载
        except Exception as e:
            import logging
            logging.error(f"剪贴板管理器加载失败: {e}")
            self.components['clipboard_manager'] = None
            
    def _load_other_components(self):
        """加载其他组件"""
        try:
            # 上下文管理器
            from src.context_manager import Context
            context = Context()
            self.components['context_manager'] = context
            self.component_loaded.emit('context_manager', context)
            
            # 音频管理器 - 不传入parent避免线程问题
            from src.audio_manager import AudioManager
            audio_manager = AudioManager()
            self.components['audio_manager'] = audio_manager
            self.component_loaded.emit('audio_manager', audio_manager)
            
            # 音频捕获线程
            from src.audio_threads import AudioCaptureThread
            audio_capture_thread = AudioCaptureThread(self.app_instance.audio_capture)
            self.components['audio_capture_thread'] = audio_capture_thread
            self.component_loaded.emit('audio_capture_thread', audio_capture_thread)
            
        except Exception as e:
            import logging
            logging.error(f"其他组件加载失败: {e}")
            
    def get_component(self, name):
        """获取已加载的组件"""
        return self.components.get(name)
        
    def is_component_ready(self, name):
        """检查组件是否已就绪"""
        component = self.components.get(name)
        if not component:
            return False
            
        # 特殊检查FunASR引擎
        if name == 'funasr_engine':
            return hasattr(component, 'is_ready') and component.is_ready
            
        return True


class LoadingSplash(QSplashScreen):
    """启动加载界面"""
    
    def __init__(self):
        # 创建一个简单的启动图片或使用纯色背景
        pixmap = QPixmap(400, 300)
        pixmap.fill(Qt.GlobalColor.white)
        super().__init__(pixmap)
        
        self.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)
        
        # 创建布局
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # 应用标题
        title_label = QLabel("Dou-flow")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 状态文本
        self.status_label = QLabel("正在启动...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # 设置样式
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                color: #333;
            }
            QProgressBar {
                border: 2px solid #ddd;
                border-radius: 5px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        
        # 应用布局
        widget.setLayout(layout)
        self.setFixedSize(400, 300)
        
        # 居中显示
        self.center_on_screen()
        
    def center_on_screen(self):
        """将窗口居中显示"""
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
    def update_progress(self, value, text=""):
        """更新进度条"""
        try:
            if hasattr(self, 'progress_bar') and self.progress_bar and not self.progress_bar.isHidden():
                self.progress_bar.setValue(value)
            if text and hasattr(self, 'status_label') and self.status_label:
                self.status_label.setText(text)
            from PyQt6.QtWidgets import QApplication
            QApplication.processEvents()
        except RuntimeError as e:
            # 忽略Qt对象已被删除的错误
            if "has been deleted" in str(e):
                pass
            else:
                import logging
                logging.error(f"更新进度失败: {e}")
        except Exception as e:
            import logging
            logging.error(f"更新进度失败: {e}")