from abc import ABC, abstractmethod
from typing import Callable, Optional, Dict, Any
import logging

class HotkeyManagerBase(ABC):
    """热键管理器基类，定义统一的接口"""
    
    def __init__(self, settings_manager=None):
        self.settings_manager = settings_manager
        self.press_callback: Optional[Callable] = None
        self.release_callback: Optional[Callable] = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.hotkey_type = 'fn'  # 默认热键类型
        self.is_active = False
    
    def set_press_callback(self, callback: Callable) -> None:
        """设置按键按下回调函数"""
        self.press_callback = callback
    
    def set_release_callback(self, callback: Callable) -> None:
        """设置按键释放回调函数"""
        self.release_callback = callback
    
    @abstractmethod
    def start_listening(self) -> bool:
        """启动热键监听
        
        Returns:
            bool: 启动是否成功
        """
        pass
    
    @abstractmethod
    def stop_listening(self) -> None:
        """停止热键监听"""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """清理资源"""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """获取热键管理器状态
        
        Returns:
            Dict[str, Any]: 包含以下键的状态字典
                - active: bool, 是否活跃
                - scheme: str, 方案名称
                - hotkey_type: str, 热键类型
                - error_count: int, 错误计数
                - last_error: str, 最后一个错误信息
        """
        pass
    
    @abstractmethod
    def update_hotkey(self, hotkey_type: str) -> bool:
        """更新热键类型
        
        Args:
            hotkey_type: 新的热键类型
            
        Returns:
            bool: 更新是否成功
        """
        pass
    
    @abstractmethod
    def update_delay_settings(self) -> None:
        """更新延迟设置"""
        pass
    
    @abstractmethod
    def reset_state(self) -> None:
        """重置状态"""
        pass
    
    @abstractmethod
    def force_reset(self) -> None:
        """强制重置"""
        pass
    
    def get_scheme_name(self) -> str:
        """获取方案名称"""
        return self.__class__.__name__.replace('HotkeyManager', '').lower()