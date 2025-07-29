#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
组件管理器基类
定义统一的组件管理接口
"""

import logging
import threading
from typing import Dict, Any, Optional, Callable
from enum import Enum

class ComponentState(Enum):
    """组件状态"""
    NOT_INITIALIZED = "not_initialized"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"

class ComponentManager:
    """组件管理器基类
    
    所有管理器的基类，提供统一的生命周期管理接口
    """
    
    def __init__(self, name: str, app_context=None):
        self.name = name
        self.app_context = app_context
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        
        # 状态管理
        self._state = ComponentState.NOT_INITIALIZED
        self._state_lock = threading.RLock()
        self._error_message = ""
        
        # 生命周期回调
        self._state_callbacks: Dict[ComponentState, list] = {}
        
        # 初始化统计
        self._init_start_time = None
        self._init_duration = 0
        
        self.logger.debug(f"{self.name} 管理器已创建")
    
    @property
    def state(self) -> ComponentState:
        """获取当前状态"""
        with self._state_lock:
            return self._state
    
    @property
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self.state in [
            ComponentState.INITIALIZED,
            ComponentState.STARTING,
            ComponentState.RUNNING,
            ComponentState.STOPPING
        ]
    
    @property
    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self.state == ComponentState.RUNNING
    
    def add_state_callback(self, state: ComponentState, callback: Callable):
        """添加状态变化回调"""
        if state not in self._state_callbacks:
            self._state_callbacks[state] = []
        self._state_callbacks[state].append(callback)
    
    def _set_state(self, new_state: ComponentState, error_message: str = ""):
        """设置状态"""
        with self._state_lock:
            old_state = self._state
            self._state = new_state
            self._error_message = error_message
            
            if old_state != new_state:
                self.logger.debug(f"{self.name} 状态变化: {old_state.value} -> {new_state.value}")
                
                # 触发状态回调
                if new_state in self._state_callbacks:
                    for callback in self._state_callbacks[new_state]:
                        try:
                            callback(self, old_state, new_state)
                        except Exception as e:
                            self.logger.error(f"状态回调执行失败: {e}")
    
    async def initialize(self) -> bool:
        """初始化组件"""
        if self.is_initialized:
            self.logger.warning(f"{self.name} 已经初始化，跳过重复初始化")
            return True
        
        self._set_state(ComponentState.INITIALIZING)
        
        try:
            import time
            self._init_start_time = time.time()
            
            self.logger.info(f"开始初始化 {self.name}")
            
            # 调用子类的初始化逻辑
            success = await self._initialize_internal()
            
            if success:
                self._init_duration = time.time() - self._init_start_time
                self._set_state(ComponentState.INITIALIZED)
                self.logger.info(f"{self.name} 初始化成功，耗时 {self._init_duration:.2f}s")
                return True
            else:
                self._set_state(ComponentState.ERROR, "初始化失败")
                self.logger.error(f"{self.name} 初始化失败")
                return False
                
        except Exception as e:
            self._set_state(ComponentState.ERROR, str(e))
            self.logger.error(f"{self.name} 初始化异常: {e}")
            return False
    
    def start(self) -> bool:
        """启动组件"""
        if not self.is_initialized:
            self.logger.error(f"{self.name} 未初始化，无法启动")
            return False
        
        if self.is_running:
            self.logger.warning(f"{self.name} 已经在运行")
            return True
        
        self._set_state(ComponentState.STARTING)
        
        try:
            self.logger.info(f"启动 {self.name}")
            
            success = self._start_internal()
            
            if success:
                self._set_state(ComponentState.RUNNING)
                self.logger.info(f"{self.name} 启动成功")
                return True
            else:
                self._set_state(ComponentState.ERROR, "启动失败")
                self.logger.error(f"{self.name} 启动失败")
                return False
                
        except Exception as e:
            self._set_state(ComponentState.ERROR, str(e))
            self.logger.error(f"{self.name} 启动异常: {e}")
            return False
    
    def stop(self) -> bool:
        """停止组件"""
        if not self.is_running:
            self.logger.debug(f"{self.name} 未在运行，无需停止")
            return True
        
        self._set_state(ComponentState.STOPPING)
        
        try:
            self.logger.info(f"停止 {self.name}")
            
            success = self._stop_internal()
            
            if success:
                self._set_state(ComponentState.STOPPED)
                self.logger.info(f"{self.name} 停止成功")
                return True
            else:
                self._set_state(ComponentState.ERROR, "停止失败")
                self.logger.error(f"{self.name} 停止失败")
                return False
                
        except Exception as e:
            self._set_state(ComponentState.ERROR, str(e))
            self.logger.error(f"{self.name} 停止异常: {e}")
            return False
    
    def cleanup(self):
        """清理资源"""
        try:
            self.logger.info(f"清理 {self.name} 资源")
            
            # 先停止组件
            if self.is_running:
                self.stop()
            
            # 调用子类的清理逻辑
            self._cleanup_internal()
            
            self._set_state(ComponentState.STOPPED)
            self.logger.info(f"{self.name} 资源清理完成")
            
        except Exception as e:
            self.logger.error(f"{self.name} 资源清理异常: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取组件状态信息"""
        with self._state_lock:
            return {
                'name': self.name,
                'state': self._state.value,
                'is_initialized': self.is_initialized,
                'is_running': self.is_running,
                'error_message': self._error_message,
                'init_duration': self._init_duration
            }
    
    # 抽象方法 - 子类必须实现
    async def _initialize_internal(self) -> bool:
        """内部初始化逻辑 - 子类实现"""
        raise NotImplementedError("子类必须实现 _initialize_internal 方法")
    
    def _start_internal(self) -> bool:
        """内部启动逻辑 - 子类可选实现"""
        return True
    
    def _stop_internal(self) -> bool:
        """内部停止逻辑 - 子类可选实现"""
        return True
    
    def _cleanup_internal(self):
        """内部清理逻辑 - 子类可选实现"""
        pass
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.name}, {self.state.value})"
    
    def __repr__(self) -> str:
        return self.__str__()
