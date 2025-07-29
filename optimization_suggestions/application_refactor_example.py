#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Application类重构示例
将单一的大类拆分为多个专门的管理器
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

class ComponentManager(ABC):
    """组件管理器基类"""
    
    def __init__(self, app_context):
        self.app_context = app_context
        self.logger = logging.getLogger(self.__class__.__name__)
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """初始化组件"""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """清理资源"""
        pass
    
    @property
    def is_initialized(self) -> bool:
        return self._initialized

class UIManager(ComponentManager):
    """UI管理器 - 专门负责界面相关操作"""
    
    def __init__(self, app_context):
        super().__init__(app_context)
        self.main_window = None
        self.settings_window = None
        self.splash = None
    
    async def initialize(self) -> bool:
        """初始化UI组件"""
        try:
            # 创建主窗口
            from ui.main_window import MainWindow
            self.main_window = MainWindow(app_instance=self.app_context)
            
            # 创建启动界面
            from app_loader import LoadingSplash
            self.splash = LoadingSplash()
            
            self._initialized = True
            self.logger.info("UI管理器初始化完成")
            return True
        except Exception as e:
            self.logger.error(f"UI管理器初始化失败: {e}")
            return False
    
    def show_main_window(self):
        """显示主窗口"""
        if self.main_window:
            self.main_window._show_window_internal()
    
    def hide_splash(self):
        """隐藏启动界面"""
        if self.splash:
            self.splash.close()
    
    def cleanup(self):
        """清理UI资源"""
        if self.settings_window:
            self.settings_window.close()
        if self.main_window:
            self.main_window.close()

class AudioManager(ComponentManager):
    """音频管理器 - 专门负责音频相关操作"""
    
    def __init__(self, app_context):
        super().__init__(app_context)
        self.audio_capture = None
        self.funasr_engine = None
        self.audio_capture_thread = None
    
    async def initialize(self) -> bool:
        """初始化音频组件"""
        try:
            from audio_capture import AudioCapture
            from funasr_engine import FunASREngine
            
            self.audio_capture = AudioCapture()
            self.funasr_engine = FunASREngine()
            
            self._initialized = True
            self.logger.info("音频管理器初始化完成")
            return True
        except Exception as e:
            self.logger.error(f"音频管理器初始化失败: {e}")
            return False
    
    def start_recording(self):
        """开始录音"""
        if self.audio_capture and self._initialized:
            # 录音逻辑
            pass
    
    def stop_recording(self):
        """停止录音"""
        if self.audio_capture and self._initialized:
            # 停止录音逻辑
            pass
    
    def cleanup(self):
        """清理音频资源"""
        if self.audio_capture_thread:
            self.audio_capture_thread.quit()
        if self.audio_capture:
            self.audio_capture.cleanup()
        if self.funasr_engine:
            self.funasr_engine.cleanup()

class HotkeyManager(ComponentManager):
    """热键管理器 - 专门负责热键相关操作"""
    
    def __init__(self, app_context):
        super().__init__(app_context)
        self.hotkey_manager = None
    
    async def initialize(self) -> bool:
        """初始化热键组件"""
        try:
            from hotkey_manager import PythonHotkeyManager
            self.hotkey_manager = PythonHotkeyManager(
                self.app_context.settings_manager
            )
            
            # 设置回调
            self.hotkey_manager.set_press_callback(self._on_hotkey_press)
            self.hotkey_manager.set_release_callback(self._on_hotkey_release)
            
            self._initialized = True
            self.logger.info("热键管理器初始化完成")
            return True
        except Exception as e:
            self.logger.error(f"热键管理器初始化失败: {e}")
            return False
    
    def _on_hotkey_press(self):
        """热键按下回调"""
        self.app_context.audio_manager.start_recording()
    
    def _on_hotkey_release(self):
        """热键释放回调"""
        self.app_context.audio_manager.stop_recording()
    
    def start_listening(self):
        """开始监听热键"""
        if self.hotkey_manager and self._initialized:
            self.hotkey_manager.start_listening()
    
    def cleanup(self):
        """清理热键资源"""
        if self.hotkey_manager:
            self.hotkey_manager.cleanup()

class ApplicationContext:
    """应用程序上下文 - 协调各个管理器"""
    
    def __init__(self):
        self.settings_manager = None
        self.ui_manager = None
        self.audio_manager = None
        self.hotkey_manager = None
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def initialize(self) -> bool:
        """初始化所有管理器"""
        try:
            # 初始化设置管理器
            from settings_manager import SettingsManager
            self.settings_manager = SettingsManager()
            
            # 创建各个管理器
            self.ui_manager = UIManager(self)
            self.audio_manager = AudioManager(self)
            self.hotkey_manager = HotkeyManager(self)
            
            # 按顺序初始化
            managers = [
                self.ui_manager,
                self.audio_manager,
                self.hotkey_manager
            ]
            
            for manager in managers:
                if not await manager.initialize():
                    self.logger.error(f"{manager.__class__.__name__} 初始化失败")
                    return False
            
            self.logger.info("应用程序初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"应用程序初始化失败: {e}")
            return False
    
    def cleanup(self):
        """清理所有资源"""
        managers = [
            self.hotkey_manager,
            self.audio_manager,
            self.ui_manager
        ]
        
        for manager in managers:
            if manager:
                try:
                    manager.cleanup()
                except Exception as e:
                    self.logger.error(f"清理 {manager.__class__.__name__} 失败: {e}")

# 重构后的Application类变得非常简洁
class Application:
    """重构后的Application类 - 只负责协调"""
    
    def __init__(self):
        self.context = ApplicationContext()
    
    async def run(self):
        """运行应用程序"""
        try:
            # 初始化
            if not await self.context.initialize():
                return 1
            
            # 显示界面
            self.context.ui_manager.show_main_window()
            self.context.ui_manager.hide_splash()
            
            # 启动热键监听
            self.context.hotkey_manager.start_listening()
            
            # 运行事件循环
            from PyQt6.QtWidgets import QApplication
            return QApplication.instance().exec()
            
        except Exception as e:
            logging.error(f"应用程序运行失败: {e}")
            return 1
        finally:
            self.context.cleanup()
