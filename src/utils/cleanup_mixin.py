"""清理资源的基础接口"""

import logging

class CleanupMixin:
    """清理资源的基础混入类
    
    提供统一的资源清理接口，所有需要清理资源的类都应该继承此类
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_cleaned_up = False
        self._cleanup_callbacks = []
    
    def _cleanup_resources(self):
        """子类应该重写的资源清理方法"""
        pass
    
    def add_cleanup_callback(self, callback):
        """添加清理回调函数"""
        if callable(callback):
            self._cleanup_callbacks.append(callback)
    
    def cleanup(self):
        """统一的清理方法"""
        if self._is_cleaned_up:
            return
        
        try:
            # 执行子类的清理逻辑
            self._cleanup_resources()
            
            # 执行注册的清理回调
            for callback in self._cleanup_callbacks:
                try:
                    callback()
                except Exception as e:
                    logging.warning(f"清理回调执行失败: {e}")
            
            self._is_cleaned_up = True
            logging.info(f"{self.__class__.__name__} 资源清理完成")
            
        except Exception as e:
            logging.error(f"{self.__class__.__name__} 资源清理失败: {e}")
            raise
    
    def __del__(self):
        """析构函数，确保资源被清理"""
        try:
            self.cleanup()
        except Exception:
            # 析构函数中不应该抛出异常
            pass
    
    @property
    def is_cleaned_up(self):
        """检查是否已经清理"""
        return self._is_cleaned_up


class ResourceManager:
    """资源管理器，用于批量管理需要清理的资源"""
    
    def __init__(self):
        self._resources = []
    
    def register(self, resource):
        """注册需要清理的资源"""
        if hasattr(resource, 'cleanup'):
            self._resources.append(resource)
        else:
            raise ValueError(f"资源 {resource} 必须实现 cleanup 方法")
    
    def cleanup_all(self):
        """清理所有注册的资源"""
        errors = []
        
        for resource in self._resources:
            try:
                resource.cleanup()
            except Exception as e:
                errors.append(f"{resource.__class__.__name__}: {e}")
        
        self._resources.clear()
        
        if errors:
            raise Exception(f"部分资源清理失败: {'; '.join(errors)}")
    
    def __del__(self):
        """析构时清理所有资源"""
        try:
            self.cleanup_all()
        except Exception:
            pass