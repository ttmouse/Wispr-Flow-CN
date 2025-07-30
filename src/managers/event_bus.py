#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件总线系统
用于管理器之间的解耦通信
"""

import logging
from typing import Dict, List, Callable, Any, Optional
from enum import Enum
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal

class EventType(Enum):
    """事件类型枚举"""
    # 录音相关事件
    RECORDING_STARTED = "recording_started"
    RECORDING_STOPPED = "recording_stopped"
    TRANSCRIPTION_COMPLETED = "transcription_completed"
    RECORDING_ERROR = "recording_error"
    
    # UI相关事件
    WINDOW_SHOW_REQUESTED = "window_show_requested"
    WINDOW_HIDE_REQUESTED = "window_hide_requested"
    SETTINGS_SHOW_REQUESTED = "settings_show_requested"
    
    # 系统相关事件
    PERMISSIONS_CHECK_REQUESTED = "permissions_check_requested"
    PERMISSIONS_STATUS_CHANGED = "permissions_status_changed"
    HOTKEY_RESTART_REQUESTED = "hotkey_restart_requested"
    QUIT_REQUESTED = "quit_requested"
    
    # 热键相关事件
    HOTKEY_PRESSED = "hotkey_pressed"
    HOTKEY_RELEASED = "hotkey_released"
    HOTKEY_STATUS_CHANGED = "hotkey_status_changed"
    
    # 音频相关事件
    AUDIO_CAPTURED = "audio_captured"
    VOLUME_CHANGED = "volume_changed"
    
    # 应用程序生命周期事件
    APP_INITIALIZING = "app_initializing"
    APP_INITIALIZED = "app_initialized"
    APP_SHUTTING_DOWN = "app_shutting_down"

@dataclass
class Event:
    """事件数据类"""
    type: EventType
    data: Any = None
    source: Optional[str] = None
    timestamp: Optional[float] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            import time
            self.timestamp = time.time()

class EventBus(QObject):
    """事件总线 - 管理器间的通信中心"""
    
    # Qt信号用于跨线程通信
    event_emitted = pyqtSignal(object)  # Event对象
    
    def __init__(self):
        super().__init__()
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 事件监听器字典 {EventType: [callback_functions]}
        self._listeners: Dict[EventType, List[Callable]] = {}
        
        # 事件历史记录（用于调试）
        self._event_history: List[Event] = []
        self._max_history_size = 100
        
        # 连接Qt信号
        self.event_emitted.connect(self._handle_qt_event)
        
        self.logger.info("事件总线已初始化")
    
    def subscribe(self, event_type: EventType, callback: Callable[[Event], None], source: str = None):
        """订阅事件
        
        Args:
            event_type: 事件类型
            callback: 回调函数，接收Event对象作为参数
            source: 订阅者标识（用于调试）
        """
        try:
            if event_type not in self._listeners:
                self._listeners[event_type] = []
            
            self._listeners[event_type].append(callback)
            
            self.logger.debug(f"事件订阅成功: {event_type.value} <- {source or 'Unknown'}")
            
        except Exception as e:
            self.logger.error(f"事件订阅失败: {e}")
    
    def unsubscribe(self, event_type: EventType, callback: Callable, source: str = None):
        """取消订阅事件
        
        Args:
            event_type: 事件类型
            callback: 要移除的回调函数
            source: 订阅者标识（用于调试）
        """
        try:
            if event_type in self._listeners:
                if callback in self._listeners[event_type]:
                    self._listeners[event_type].remove(callback)
                    self.logger.debug(f"事件取消订阅成功: {event_type.value} <- {source or 'Unknown'}")
                    
                    # 如果没有监听器了，删除该事件类型
                    if not self._listeners[event_type]:
                        del self._listeners[event_type]
                        
        except Exception as e:
            self.logger.error(f"取消事件订阅失败: {e}")
    
    def emit(self, event_type: EventType, data: Any = None, source: str = None):
        """发射事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
            source: 事件源标识
        """
        try:
            event = Event(type=event_type, data=data, source=source)
            
            # 添加到历史记录
            self._add_to_history(event)
            
            # 使用Qt信号发射事件（支持跨线程）
            self.event_emitted.emit(event)
            
            self.logger.debug(f"事件发射: {event_type.value} from {source or 'Unknown'}")
            
        except Exception as e:
            self.logger.error(f"事件发射失败: {e}")
    
    def _handle_qt_event(self, event: Event):
        """处理Qt信号传递的事件"""
        try:
            if event.type in self._listeners:
                for callback in self._listeners[event.type]:
                    try:
                        callback(event)
                    except Exception as e:
                        self.logger.error(f"事件处理回调失败: {e}")
                        
        except Exception as e:
            self.logger.error(f"Qt事件处理失败: {e}")
    
    def _add_to_history(self, event: Event):
        """添加事件到历史记录"""
        try:
            self._event_history.append(event)
            
            # 限制历史记录大小
            if len(self._event_history) > self._max_history_size:
                self._event_history = self._event_history[-self._max_history_size:]
                
        except Exception as e:
            self.logger.error(f"添加事件历史记录失败: {e}")
    
    def get_event_history(self, event_type: EventType = None, limit: int = 10) -> List[Event]:
        """获取事件历史记录
        
        Args:
            event_type: 过滤的事件类型，None表示所有事件
            limit: 返回的最大事件数量
            
        Returns:
            事件列表，按时间倒序
        """
        try:
            history = self._event_history
            
            # 按事件类型过滤
            if event_type:
                history = [e for e in history if e.type == event_type]
            
            # 按时间倒序排列并限制数量
            history = sorted(history, key=lambda e: e.timestamp, reverse=True)
            return history[:limit]
            
        except Exception as e:
            self.logger.error(f"获取事件历史记录失败: {e}")
            return []
    
    def get_listener_count(self, event_type: EventType = None) -> int:
        """获取监听器数量
        
        Args:
            event_type: 事件类型，None表示所有事件
            
        Returns:
            监听器数量
        """
        try:
            if event_type:
                return len(self._listeners.get(event_type, []))
            else:
                return sum(len(listeners) for listeners in self._listeners.values())
                
        except Exception as e:
            self.logger.error(f"获取监听器数量失败: {e}")
            return 0
    
    def clear_listeners(self, event_type: EventType = None):
        """清除监听器
        
        Args:
            event_type: 事件类型，None表示清除所有监听器
        """
        try:
            if event_type:
                if event_type in self._listeners:
                    del self._listeners[event_type]
                    self.logger.debug(f"已清除事件监听器: {event_type.value}")
            else:
                self._listeners.clear()
                self.logger.debug("已清除所有事件监听器")
                
        except Exception as e:
            self.logger.error(f"清除监听器失败: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取事件总线统计信息"""
        try:
            stats = {
                'total_listeners': self.get_listener_count(),
                'event_types_count': len(self._listeners),
                'history_size': len(self._event_history),
                'listeners_by_type': {
                    event_type.value: len(listeners) 
                    for event_type, listeners in self._listeners.items()
                }
            }
            return stats
            
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def cleanup(self):
        """清理事件总线"""
        try:
            self.clear_listeners()
            self._event_history.clear()
            self.logger.info("事件总线已清理")
            
        except Exception as e:
            self.logger.error(f"事件总线清理失败: {e}")

# 全局事件总线实例
_global_event_bus: Optional[EventBus] = None

def get_event_bus() -> EventBus:
    """获取全局事件总线实例"""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus

def cleanup_event_bus():
    """清理全局事件总线"""
    global _global_event_bus
    if _global_event_bus:
        _global_event_bus.cleanup()
        _global_event_bus = None
