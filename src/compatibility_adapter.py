#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
兼容性适配器
确保原有的Application类接口在新架构中正常工作
"""

import logging
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication

from managers.application_context import ApplicationContext
from managers.event_bus import EventType, get_event_bus

class ApplicationAdapter(QObject):
    """Application类的兼容性适配器
    
    提供与原始Application类相同的接口，
    但内部使用重构后的管理器架构
    """
    
    # 保持与原始Application类相同的信号
    update_ui_signal = pyqtSignal(str, str)
    show_window_signal = pyqtSignal()
    start_recording_signal = pyqtSignal()
    stop_recording_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 创建Qt应用程序
        self.app = QApplication.instance()
        if not self.app:
            self.app = QApplication([])
        
        # 创建应用程序上下文
        self.context = ApplicationContext(self.app)
        
        # 获取事件总线
        self.event_bus = get_event_bus()
        
        # 兼容性属性映射
        self._setup_compatibility_attributes()
        
        # 连接信号
        self._setup_signal_connections()
        
        self.logger.info("兼容性适配器已初始化")
    
    def _setup_compatibility_attributes(self):
        """设置兼容性属性，映射到新架构的组件"""
        # 这些属性将在初始化完成后可用
        self._main_window = None
        self._state_manager = None
        self._audio_capture = None
        self._funasr_engine = None
        self._hotkey_manager = None
        self._clipboard_manager = None
        self._recording = False
    
    def _setup_signal_connections(self):
        """设置信号连接"""
        # 连接上下文信号
        self.context.initialization_completed.connect(self._on_initialization_completed)
        
        # 连接内部信号到外部信号
        self.show_window_signal.connect(self._show_window_internal)
        self.start_recording_signal.connect(self._start_recording_internal)
        self.stop_recording_signal.connect(self._stop_recording_internal)
    
    async def initialize(self):
        """异步初始化（兼容原有接口）"""
        try:
            success = await self.context.initialize()
            if success:
                self._update_compatibility_attributes()
            return success
        except Exception as e:
            self.logger.error(f"初始化失败: {e}")
            return False
    
    def _on_initialization_completed(self):
        """初始化完成回调"""
        self._update_compatibility_attributes()
        self.logger.info("兼容性适配器初始化完成")
    
    def _update_compatibility_attributes(self):
        """更新兼容性属性映射"""
        try:
            # 映射UI组件
            if self.context.ui_manager:
                self._main_window = self.context.ui_manager.main_window
            
            # 映射状态管理器
            self._state_manager = self.context.state_manager
            
            # 映射录音管理器的组件
            if self.context.recording_manager:
                self._audio_capture = self.context.recording_manager.audio_capture
                self._funasr_engine = self.context.recording_manager.funasr_engine
            
            # 映射热键管理器
            if self.context.hotkey_manager:
                self._hotkey_manager = self.context.hotkey_manager
            
            # 映射剪贴板管理器（如果存在）
            # self._clipboard_manager = ...
            
        except Exception as e:
            self.logger.error(f"更新兼容性属性失败: {e}")
    
    # 兼容性属性访问器
    @property
    def main_window(self):
        """主窗口属性（兼容性）"""
        return self._main_window
    
    @property
    def state_manager(self):
        """状态管理器属性（兼容性）"""
        return self._state_manager
    
    @property
    def audio_capture(self):
        """音频捕获属性（兼容性）"""
        return self._audio_capture
    
    @property
    def funasr_engine(self):
        """FunASR引擎属性（兼容性）"""
        return self._funasr_engine
    
    @property
    def hotkey_manager(self):
        """热键管理器属性（兼容性）"""
        return self._hotkey_manager
    
    @property
    def clipboard_manager(self):
        """剪贴板管理器属性（兼容性）"""
        return self._clipboard_manager
    
    @property
    def recording(self):
        """录音状态属性（兼容性）"""
        if self.context.recording_manager:
            return self.context.recording_manager.is_recording()
        return self._recording
    
    @recording.setter
    def recording(self, value):
        """设置录音状态（兼容性）"""
        self._recording = value
    
    # 兼容性方法
    def start_recording(self):
        """开始录音（兼容性方法）"""
        if self.context.recording_manager:
            return self.context.recording_manager.start_recording()
        return False
    
    def stop_recording(self):
        """停止录音（兼容性方法）"""
        if self.context.recording_manager:
            return self.context.recording_manager.stop_recording()
        return False
    
    def toggle_recording(self):
        """切换录音状态（兼容性方法）"""
        if self.context.recording_manager:
            self.context.recording_manager.toggle_recording()
    
    def show_window(self):
        """显示窗口（兼容性方法）"""
        self.show_window_signal.emit()
    
    def _show_window_internal(self):
        """内部显示窗口方法"""
        if self.context.ui_manager:
            self.context.ui_manager.show_main_window()
    
    def _start_recording_internal(self):
        """内部开始录音方法"""
        self.start_recording()
    
    def _stop_recording_internal(self):
        """内部停止录音方法"""
        self.stop_recording()
    
    def is_ready_for_recording(self):
        """检查是否准备好录音（兼容性方法）"""
        if self.context.recording_manager:
            return self.context.recording_manager.is_ready_for_recording()
        return False
    
    def update_ui(self, status, result):
        """更新UI（兼容性方法）"""
        self.update_ui_signal.emit(status, result)
        
        # 如果有主窗口，直接更新
        if self._main_window:
            try:
                self._main_window.update_status(status)
                if result and result.strip():
                    self._main_window.display_result(result)
            except Exception as e:
                self.logger.error(f"更新UI失败: {e}")
    
    def on_option_press(self):
        """处理热键按下（兼容性方法）"""
        if self.is_ready_for_recording():
            self.start_recording_signal.emit()
    
    def on_option_release(self):
        """处理热键释放（兼容性方法）"""
        if self.recording:
            self.stop_recording_signal.emit()
    
    def quit_application(self):
        """退出应用程序（兼容性方法）"""
        try:
            self.cleanup()
            if self.app:
                self.app.quit()
        except Exception as e:
            self.logger.error(f"退出应用程序失败: {e}")
    
    def cleanup(self):
        """清理资源（兼容性方法）"""
        try:
            if self.context:
                self.context.cleanup()
        except Exception as e:
            self.logger.error(f"清理资源失败: {e}")
    
    def run(self):
        """运行应用程序（兼容性方法）"""
        try:
            import asyncio
            
            # 创建异步事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 异步初始化
            init_success = loop.run_until_complete(self.initialize())
            
            if not init_success:
                self.logger.error("应用程序初始化失败")
                return 1
            
            # 运行Qt事件循环
            return self.app.exec()
            
        except Exception as e:
            self.logger.error(f"运行应用程序失败: {e}")
            return 1
        finally:
            self.cleanup()

# 为了完全兼容，创建一个Application别名
Application = ApplicationAdapter
