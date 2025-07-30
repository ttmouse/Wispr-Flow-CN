#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热键管理器包装器
将热键相关功能包装到统一的管理器中
"""

import logging
from typing import Optional, Callable
from PyQt6.QtCore import QObject, pyqtSignal

from .component_manager import ComponentManager

class HotkeyManagerWrapper(QObject):
    """热键管理器包装器 - 专门负责热键相关操作"""

    # 信号定义
    hotkey_pressed = pyqtSignal()
    hotkey_released = pyqtSignal()
    permission_error = pyqtSignal(str)
    hotkey_error = pyqtSignal(str)

    def __init__(self, app_context):
        super().__init__()

        # 使用组合而不是继承
        self.component_manager = ComponentManager(name="热键管理器", app_context=app_context)

        # 添加logger
        self.logger = logging.getLogger(self.__class__.__name__)
        self.app_context = app_context
        
        # 热键管理器实例
        self.hotkey_manager = None
        
        # 回调函数
        self._press_callback: Optional[Callable] = None
        self._release_callback: Optional[Callable] = None
        self._permission_error_callback: Optional[Callable] = None
        
        # 状态
        self._listening = False

    # 委托ComponentManager的方法
    def initialize_sync(self):
        """同步初始化热键管理器"""
        try:
            # 通过ComponentManager确保状态正确设置
            if self.component_manager.is_initialized:
                self.logger.warning("热键管理器已经初始化，跳过重复初始化")
                return True

            # 设置初始化状态
            from .component_manager import ComponentState
            self.component_manager._set_state(ComponentState.INITIALIZING)

            import time
            init_start_time = time.time()

            # 执行同步初始化
            success = self._initialize_internal_sync()

            if success:
                # 设置成功状态
                init_duration = time.time() - init_start_time
                self.component_manager._init_duration = init_duration
                self.component_manager._set_state(ComponentState.INITIALIZED)
                self.logger.info(f"热键管理器同步初始化成功，耗时 {init_duration:.2f}s")
                return True
            else:
                # 设置错误状态
                self.component_manager._set_state(ComponentState.ERROR, "同步初始化失败")
                self.logger.error("热键管理器同步初始化失败")
                return False

        except Exception as e:
            # 设置异常状态
            self.component_manager._set_state(ComponentState.ERROR, str(e))
            self.logger.error(f"热键管理器同步初始化异常: {e}")
            return False

    async def initialize(self):
        # 设置内部初始化方法
        self.component_manager._initialize_internal = self._initialize_internal
        self.component_manager._start_internal = self._start_internal
        self.component_manager._stop_internal = self._stop_internal
        self.component_manager._cleanup_internal = self._cleanup_internal
        return await self.component_manager.initialize()

    def start(self):
        return self.component_manager.start()

    def stop(self):
        return self.component_manager.stop()

    def cleanup(self):
        return self.component_manager.cleanup()

    def get_status(self):
        return self.component_manager.get_status()

    @property
    def state(self):
        return self.component_manager.state

    @property
    def is_initialized(self):
        return self.component_manager.is_initialized

    @property
    def is_running(self):
        return self.component_manager.is_running
    
    def set_callbacks(self,
                     press_callback: Optional[Callable] = None,
                     release_callback: Optional[Callable] = None,
                     permission_error_callback: Optional[Callable] = None):
        """设置回调函数"""
        self._press_callback = press_callback
        self._release_callback = release_callback
        self._permission_error_callback = permission_error_callback

    def _initialize_internal_sync(self) -> bool:
        """同步初始化热键管理器"""
        try:
            # 获取设置管理器
            settings_manager = None
            if (self.app_context and
                hasattr(self.app_context, 'settings_manager')):
                settings_manager = self.app_context.settings_manager

            # 创建热键管理器实例
            if not self._create_hotkey_manager(settings_manager):
                return False

            # 设置回调
            self._setup_hotkey_callbacks()

            self.logger.info("热键管理器同步初始化完成")
            return True

        except Exception as e:
            self.logger.error(f"热键管理器同步初始化失败: {e}")
            return False

    async def _initialize_internal(self) -> bool:
        """初始化热键管理器"""
        try:
            # 获取设置管理器
            settings_manager = None
            if (self.app_context and 
                hasattr(self.app_context, 'settings_manager')):
                settings_manager = self.app_context.settings_manager
            
            # 创建热键管理器实例
            if not self._create_hotkey_manager(settings_manager):
                return False
            
            # 设置回调
            self._setup_hotkey_callbacks()
            
            self.logger.info("热键管理器初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"热键管理器初始化失败: {e}")
            return False
    
    def _create_hotkey_manager(self, settings_manager) -> bool:
        """创建热键管理器实例（与原始代码一致）"""
        try:
            # 使用工厂模式创建热键管理器（与原始代码一致）
            try:
                from src.hotkey_manager_factory import HotkeyManagerFactory
            except ImportError:
                from hotkey_manager_factory import HotkeyManagerFactory

            if not settings_manager:
                self.logger.error("设置管理器未提供，无法创建热键管理器")
                return False

            scheme = settings_manager.get_hotkey_scheme()
            self.hotkey_manager = HotkeyManagerFactory.create_hotkey_manager(scheme, settings_manager)

            if self.hotkey_manager:
                self.logger.debug(f"热键管理器实例创建成功，使用方案: {scheme}")
                return True
            else:
                self.logger.error("热键管理器创建失败")
                return False

        except Exception as e:
            self.logger.error(f"创建热键管理器实例失败: {e}")
            return False
    
    def _setup_hotkey_callbacks(self):
        """设置热键回调"""
        try:
            if self.hotkey_manager:
                # 设置按下和释放回调
                self.hotkey_manager.set_press_callback(self._on_hotkey_press)
                self.hotkey_manager.set_release_callback(self._on_hotkey_release)
                
                # 设置权限错误回调
                if hasattr(self.hotkey_manager, 'set_permission_error_callback'):
                    self.hotkey_manager.set_permission_error_callback(self._on_permission_error)
                
                self.logger.debug("热键回调设置完成")
            
        except Exception as e:
            self.logger.error(f"设置热键回调失败: {e}")
    
    def _start_internal(self) -> bool:
        """启动热键监听"""
        try:
            if not self.hotkey_manager:
                self.logger.error("热键管理器未初始化")
                return False

            # PythonHotkeyManager的start_listening方法没有返回值
            # 我们需要检查是否成功启动
            self.hotkey_manager.start_listening()

            # 检查状态来确认是否启动成功
            status = self.hotkey_manager.get_status()
            if status.get('active', False):
                self._listening = True
                self.logger.info("热键监听启动成功")
                return True
            else:
                self.logger.warning("热键监听可能启动失败，但继续运行")
                self._listening = True  # 假设启动成功，避免阻塞应用启动
                return True

        except Exception as e:
            self.logger.error(f"启动热键监听异常: {e}")
            # 不让热键启动失败阻塞整个应用
            self.logger.warning("热键启动失败，但应用将继续运行")
            return True
    
    def _stop_internal(self) -> bool:
        """停止热键监听"""
        try:
            if self.hotkey_manager and self._listening:
                self.hotkey_manager.stop_listening()
                self._listening = False
                self.logger.info("热键监听停止成功")
            
            return True
            
        except Exception as e:
            self.logger.error(f"停止热键监听异常: {e}")
            return False
    
    # 公共接口方法
    def restart_hotkey_manager(self) -> bool:
        """重启热键管理器"""
        try:
            self.logger.info("重启热键管理器")
            
            # 停止当前监听
            if self._listening:
                self.stop()
            
            # 重新启动
            success = self.start()
            
            if success:
                self.logger.info("热键管理器重启成功")
            else:
                self.logger.error("热键管理器重启失败")
            
            return success
            
        except Exception as e:
            self.logger.error(f"重启热键管理器异常: {e}")
            return False
    
    def check_permissions(self) -> bool:
        """检查热键权限"""
        try:
            if self.hotkey_manager:
                return self.hotkey_manager.check_permissions()
            return False
            
        except Exception as e:
            self.logger.error(f"检查热键权限异常: {e}")
            return False
    
    def get_hotkey_status(self) -> dict:
        """获取热键状态"""
        try:
            base_status = self.get_status()
            
            if self.hotkey_manager:
                hotkey_status = self.hotkey_manager.get_status()
                base_status.update({
                    'listening': self._listening,
                    'hotkey_type': hotkey_status.get('hotkey_type', 'unknown'),
                    'permissions_ok': hotkey_status.get('permissions_ok', False),
                    'last_error': hotkey_status.get('last_error', '')
                })
            else:
                base_status.update({
                    'listening': False,
                    'hotkey_type': 'unknown',
                    'permissions_ok': False,
                    'last_error': '热键管理器未初始化'
                })
            
            return base_status
            
        except Exception as e:
            self.logger.error(f"获取热键状态异常: {e}")
            return {'error': str(e)}
    
    def set_hotkey_type(self, hotkey_type: str) -> bool:
        """设置热键类型"""
        try:
            if self.hotkey_manager:
                success = self.hotkey_manager.set_hotkey_type(hotkey_type)
                if success:
                    self.logger.info(f"热键类型已设置为: {hotkey_type}")
                else:
                    self.logger.error(f"设置热键类型失败: {hotkey_type}")
                return success
            return False
            
        except Exception as e:
            self.logger.error(f"设置热键类型异常: {e}")
            return False
    
    # 事件处理方法
    def _on_hotkey_press(self):
        """处理热键按下事件"""
        try:
            self.logger.debug("热键按下")
            
            # 发送信号
            self.hotkey_pressed.emit()
            
            # 调用回调
            if self._press_callback:
                self._press_callback()
                
        except Exception as e:
            self.logger.error(f"处理热键按下事件失败: {e}")
            self._handle_hotkey_error(f"处理热键按下事件失败: {e}")
    
    def _on_hotkey_release(self):
        """处理热键释放事件"""
        try:
            self.logger.debug("热键释放")
            
            # 发送信号
            self.hotkey_released.emit()
            
            # 调用回调
            if self._release_callback:
                self._release_callback()
                
        except Exception as e:
            self.logger.error(f"处理热键释放事件失败: {e}")
            self._handle_hotkey_error(f"处理热键释放事件失败: {e}")
    
    def _on_permission_error(self, error_message: str):
        """处理权限错误"""
        try:
            self.logger.error(f"热键权限错误: {error_message}")
            
            # 发送信号
            self.permission_error.emit(error_message)
            
            # 调用回调
            if self._permission_error_callback:
                self._permission_error_callback(error_message)
                
        except Exception as e:
            self.logger.error(f"处理权限错误失败: {e}")
    
    def _handle_hotkey_error(self, error_message: str):
        """处理热键错误"""
        self.hotkey_error.emit(error_message)
    
    def _cleanup_internal(self):
        """清理热键资源"""
        try:
            # 停止监听
            if self._listening:
                self.stop()
            
            # 清理热键管理器
            if self.hotkey_manager:
                self.hotkey_manager.cleanup()
                self.hotkey_manager = None
            
            self.logger.debug("热键资源清理完成")
            
        except Exception as e:
            self.logger.error(f"热键资源清理失败: {e}")
    
    @property
    def is_listening(self) -> bool:
        """检查是否正在监听热键"""
        return self._listening
