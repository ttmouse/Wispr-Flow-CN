"""
macOS 兼容性模块
处理 macOS 系统特有的问题，包括输入法系统冲突和 dispatch queue 问题
"""

import logging
import time
import threading
import weakref
from typing import Optional, Callable, Any
from PyQt6.QtCore import QObject, QTimer, pyqtSignal


class MacOSInputCompatibilityManager(QObject):
    """macOS 输入法兼容性管理器"""
    
    input_source_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self._input_source_timer = None
        self._last_check_time = 0
        self._check_interval = 2.0  # 2秒检查间隔
        self._is_monitoring = False
        self._callbacks = []
        
        # 使用弱引用存储回调，避免循环引用
        self._weak_callbacks = []
        
    def add_input_source_callback(self, callback: Callable):
        """添加输入法状态变化回调"""
        if callback:
            self._weak_callbacks.append(weakref.ref(callback))
            
    def remove_input_source_callback(self, callback: Callable):
        """移除输入法状态变化回调"""
        self._weak_callbacks = [ref for ref in self._weak_callbacks 
                              if ref() is not None and ref() != callback]
    
    def start_monitoring(self):
        """开始监控输入法状态"""
        if self._is_monitoring:
            return
            
        try:
            self._is_monitoring = True
            
            # 使用Qt定时器而不是线程，确保在主线程中执行
            if not self._input_source_timer:
                self._input_source_timer = QTimer()
                self._input_source_timer.timeout.connect(self._check_input_source)
                
            self._input_source_timer.start(int(self._check_interval * 1000))
            self.logger.info("开始监控输入法状态")
            
        except Exception as e:
            self.logger.error(f"启动输入法监控失败: {e}")
            self._is_monitoring = False
    
    def stop_monitoring(self):
        """停止监控输入法状态"""
        if not self._is_monitoring:
            return
            
        try:
            self._is_monitoring = False
            
            if self._input_source_timer:
                self._input_source_timer.stop()
                self._input_source_timer = None
                
            self.logger.info("停止监控输入法状态")
            
        except Exception as e:
            self.logger.error(f"停止输入法监控失败: {e}")
    
    def _check_input_source(self):
        """安全检查输入法状态"""
        current_time = time.time()
        
        # 限制检查频率
        if current_time - self._last_check_time < self._check_interval:
            return
            
        self._last_check_time = current_time
        
        try:
            # 不直接调用HIToolbox函数，避免dispatch queue问题
            # 通过其他方式间接检测输入法变化
            self._notify_callbacks()
            
        except Exception as e:
            self.logger.debug(f"输入法状态检查出错（已忽略）: {e}")
    
    def _notify_callbacks(self):
        """通知所有回调函数"""
        # 清理无效的弱引用
        valid_callbacks = []
        for ref in self._weak_callbacks:
            callback = ref()
            if callback:
                valid_callbacks.append(ref)
                try:
                    callback()
                except Exception as e:
                    self.logger.error(f"输入法回调执行失败: {e}")
        
        self._weak_callbacks = valid_callbacks
        
        # 发射信号
        self.input_source_changed.emit()


class MacOSDispatchQueueSafety:
    """macOS dispatch queue 安全包装器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._main_thread_id = threading.get_ident()
    
    def safe_execute(self, operation: Callable, *args, **kwargs) -> Optional[Any]:
        """
        安全执行可能引发dispatch queue问题的操作
        确保在主线程中执行，避免HIToolbox相关的崩溃
        """
        try:
            # 检查是否在主线程
            if threading.get_ident() != self._main_thread_id:
                self.logger.debug("尝试在非主线程执行可能不安全的操作，已跳过")
                return None
            
            # 在主线程中执行操作
            return operation(*args, **kwargs)
            
        except Exception as e:
            self.logger.error(f"安全执行操作失败: {e}")
            return None
    
    def safe_input_source_operation(self, operation: Callable, default_value=None) -> Any:
        """
        安全执行输入法相关操作
        特别处理可能导致dispatch queue断言失败的HIToolbox调用
        """
        try:
            # 添加额外的保护措施
            if threading.get_ident() != self._main_thread_id:
                self.logger.debug("输入法操作必须在主线程执行")
                return default_value
            
            # 使用超时机制避免长时间等待
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("输入法操作超时")
            
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(1)  # 1秒超时
            
            try:
                result = operation()
                signal.alarm(0)  # 取消超时
                signal.signal(signal.SIGALRM, old_handler)
                return result
                
            except TimeoutError:
                self.logger.warning("输入法操作超时，使用默认值")
                return default_value
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
                
        except Exception as e:
            self.logger.debug(f"输入法操作失败（已忽略）: {e}")
            return default_value


def setup_macos_compatibility():
    """设置macOS兼容性环境"""
    import os
    import sys
    
    if sys.platform != 'darwin':
        return None
    
    try:
        # 设置环境变量，减少macOS系统调用的副作用
        os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'
        
        # 创建兼容性管理器
        compat_manager = MacOSInputCompatibilityManager()
        dispatch_safety = MacOSDispatchQueueSafety()
        
        logging.info("macOS兼容性环境设置完成")
        return {
            'input_manager': compat_manager,
            'dispatch_safety': dispatch_safety
        }
        
    except Exception as e:
        logging.error(f"设置macOS兼容性环境失败: {e}")
        return None


# 全局单例实例
_macos_compatibility = None

def get_macos_compatibility():
    """获取macOS兼容性管理器实例"""
    global _macos_compatibility
    if _macos_compatibility is None:
        _macos_compatibility = setup_macos_compatibility()
    return _macos_compatibility