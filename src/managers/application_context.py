#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用程序上下文
协调各个管理器的工作
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal

from .ui_manager import UIManager
from .audio_manager import AudioManager
from .hotkey_manager_wrapper import HotkeyManagerWrapper

class ApplicationContext(QObject):
    """应用程序上下文 - 协调各个管理器"""

    # 信号定义
    initialization_progress = pyqtSignal(str, int)  # message, progress
    initialization_completed = pyqtSignal()
    initialization_failed = pyqtSignal(str)

    # 录音控制信号（与原始代码保持一致）
    start_recording_signal = pyqtSignal()
    stop_recording_signal = pyqtSignal()
    
    def __init__(self, qt_app: QApplication):
        super().__init__()
        
        self.app = qt_app
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 核心组件
        self.settings_manager = None
        self.state_manager = None
        
        # 管理器
        self.ui_manager: Optional[UIManager] = None
        self.audio_manager: Optional[AudioManager] = None
        self.hotkey_manager: Optional[HotkeyManagerWrapper] = None
        
        # 初始化状态
        self._initialized = False
        self._initialization_order = [
            'settings_manager',
            'state_manager', 
            'ui_manager',
            'audio_manager',
            'hotkey_manager'
        ]
        
        self.logger.info("应用程序上下文已创建")

    def initialize_sync(self) -> bool:
        """同步初始化所有管理器（在主线程中）"""
        if self._initialized:
            self.logger.warning("应用程序上下文已经初始化")
            return True

        try:
            self.logger.info("开始同步初始化应用程序上下文")

            # 1. 初始化核心组件
            if not self._initialize_core_components_sync():
                return False

            # 2. 创建管理器
            if not self._create_managers():
                return False

            # 3. 按顺序初始化管理器
            if not self._initialize_managers_sync():
                return False

            # 4. 设置管理器之间的连接
            self._setup_manager_connections()

            # 5. 启动管理器
            if not self._start_managers():
                return False

            self._initialized = True
            self.initialization_completed.emit()
            self.logger.info("应用程序上下文同步初始化完成")
            return True

        except Exception as e:
            error_msg = f"应用程序上下文同步初始化失败: {e}"
            self.logger.error(error_msg)
            self.initialization_failed.emit(error_msg)
            return False

    async def initialize(self) -> bool:
        """初始化所有管理器"""
        if self._initialized:
            self.logger.warning("应用程序上下文已经初始化")
            return True
        
        try:
            self.logger.info("开始初始化应用程序上下文")
            
            # 1. 初始化核心组件
            if not await self._initialize_core_components():
                return False
            
            # 2. 创建管理器
            if not self._create_managers():
                return False
            
            # 3. 按顺序初始化管理器
            if not await self._initialize_managers():
                return False
            
            # 4. 设置管理器之间的连接
            self._setup_manager_connections()
            
            # 5. 启动管理器
            if not self._start_managers():
                return False
            
            self._initialized = True
            self.initialization_completed.emit()
            self.logger.info("应用程序上下文初始化完成")
            return True
            
        except Exception as e:
            error_msg = f"应用程序上下文初始化失败: {e}"
            self.logger.error(error_msg)
            self.initialization_failed.emit(error_msg)
            return False

    def _initialize_core_components_sync(self) -> bool:
        """同步初始化核心组件"""
        try:
            self.initialization_progress.emit("初始化设置管理器...", 10)

            # 初始化设置管理器
            import sys
            import os
            # 添加父目录到路径以便导入
            parent_dir = os.path.dirname(os.path.dirname(__file__))
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)

            from settings_manager import SettingsManager
            self.settings_manager = SettingsManager()

            self.initialization_progress.emit("初始化状态管理器...", 20)

            # 初始化状态管理器
            from state_manager import StateManager
            self.state_manager = StateManager()

            self.logger.debug("核心组件同步初始化完成")
            return True

        except Exception as e:
            self.logger.error(f"核心组件同步初始化失败: {e}")
            return False

    async def _initialize_core_components(self) -> bool:
        """初始化核心组件"""
        try:
            self.initialization_progress.emit("初始化设置管理器...", 10)
            
            # 初始化设置管理器
            import sys
            import os
            # 添加父目录到路径以便导入
            parent_dir = os.path.dirname(os.path.dirname(__file__))
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            
            from settings_manager import SettingsManager
            self.settings_manager = SettingsManager()
            
            self.initialization_progress.emit("初始化状态管理器...", 20)
            
            # 初始化状态管理器
            from state_manager import StateManager
            self.state_manager = StateManager()
            
            self.logger.debug("核心组件初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"核心组件初始化失败: {e}")
            return False
    
    def _create_managers(self) -> bool:
        """创建管理器"""
        try:
            self.initialization_progress.emit("创建UI管理器...", 30)
            self.logger.debug("开始创建UI管理器")
            self.ui_manager = UIManager(self)
            self.logger.debug("UI管理器创建成功")

            self.initialization_progress.emit("创建音频管理器...", 40)
            self.logger.debug("开始创建音频管理器")
            self.audio_manager = AudioManager(self)
            self.logger.debug("音频管理器创建成功")

            self.initialization_progress.emit("创建热键管理器...", 50)
            self.logger.debug("开始创建热键管理器")
            self.hotkey_manager = HotkeyManagerWrapper(self)
            self.logger.debug("热键管理器创建成功")

            self.logger.debug("管理器创建完成")
            return True

        except Exception as e:
            import traceback
            self.logger.error(f"管理器创建失败: {e}")
            self.logger.error(f"错误详情: {traceback.format_exc()}")
            return False

    def _initialize_managers_sync(self) -> bool:
        """同步按顺序初始化管理器"""
        try:
            managers = [
                (self.ui_manager, "UI管理器", 60),
                (self.audio_manager, "音频管理器", 75),
                (self.hotkey_manager, "热键管理器", 90)
            ]

            for manager, name, progress in managers:
                if manager:
                    self.initialization_progress.emit(f"初始化{name}...", progress)

                    # 同步初始化
                    if hasattr(manager, 'initialize_sync'):
                        success = manager.initialize_sync()
                    else:
                        # 如果没有同步方法，使用异步方法的同步版本
                        import asyncio
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        success = loop.run_until_complete(manager.initialize())
                        loop.close()

                    if not success:
                        self.logger.error(f"{name}初始化失败")
                        return False

                    self.logger.debug(f"{name}初始化成功")

            return True

        except Exception as e:
            self.logger.error(f"管理器同步初始化失败: {e}")
            return False

    async def _initialize_managers(self) -> bool:
        """按顺序初始化管理器"""
        try:
            managers = [
                (self.ui_manager, "UI管理器", 60),
                (self.audio_manager, "音频管理器", 75),
                (self.hotkey_manager, "热键管理器", 90)
            ]
            
            for manager, name, progress in managers:
                if manager:
                    self.initialization_progress.emit(f"初始化{name}...", progress)
                    
                    success = await manager.initialize()
                    if not success:
                        self.logger.error(f"{name}初始化失败")
                        return False
                    
                    self.logger.debug(f"{name}初始化成功")
            
            return True
            
        except Exception as e:
            self.logger.error(f"管理器初始化失败: {e}")
            return False
    
    def _setup_manager_connections(self):
        """设置管理器之间的连接"""
        try:
            # UI管理器回调设置
            if self.ui_manager:
                self.ui_manager.set_callbacks(
                    show_window=self._on_show_window_requested,
                    show_settings=self._on_show_settings_requested,
                    check_permissions=self._on_check_permissions_requested,
                    restart_hotkey=self._on_restart_hotkey_requested,
                    quit_app=self._on_quit_requested
                )

                # 连接主窗口信号（关键修复）
                if self.ui_manager.main_window:
                    self.ui_manager.main_window.record_button_clicked.connect(self._on_toggle_recording)
                    self.ui_manager.main_window.history_item_clicked.connect(self._on_history_item_clicked)

            # 音频管理器回调设置
            if self.audio_manager:
                self.audio_manager.set_callbacks(
                    transcription_callback=self._on_transcription_completed,
                    error_callback=self._on_audio_error
                )

            # 热键管理器回调设置
            if self.hotkey_manager:
                self.hotkey_manager.set_callbacks(
                    press_callback=self._on_hotkey_press,
                    release_callback=self._on_hotkey_release,
                    permission_error_callback=self._on_hotkey_permission_error
                )

            # 状态管理器信号连接（关键修复）
            if self.state_manager and self.ui_manager and self.ui_manager.main_window:
                self.state_manager.status_changed.connect(self.ui_manager.main_window.update_status)

            # 录音信号连接（与原始代码保持一致）
            self.start_recording_signal.connect(self._start_recording_internal)
            self.stop_recording_signal.connect(self._stop_recording_internal)

            self.logger.debug("管理器连接设置完成")

        except Exception as e:
            self.logger.error(f"设置管理器连接失败: {e}")
    
    def _start_managers(self) -> bool:
        """启动管理器（与原始代码一致）"""
        try:
            self.initialization_progress.emit("启动管理器...", 95)

            # 启动热键管理器（与原始代码一致：失败不阻塞应用启动）
            if self.hotkey_manager:
                try:
                    if self.hotkey_manager.start():
                        self.logger.info("热键管理器启动成功")
                    else:
                        self.logger.warning("热键管理器启动失败，但应用继续运行")
                except Exception as e:
                    self.logger.error(f"热键管理器启动异常: {e}")
                    # 与原始代码一致：热键失败不影响应用启动
            else:
                self.logger.warning("热键管理器未初始化，跳过启动")

            self.initialization_progress.emit("初始化完成", 100)
            self.logger.debug("管理器启动完成")
            return True

        except Exception as e:
            self.logger.error(f"启动管理器失败: {e}")
            # 与原始代码一致：即使启动失败也返回True，让应用继续运行
            return True
    
    # 事件处理方法
    def _on_show_window_requested(self):
        """处理显示窗口请求"""
        if self.ui_manager:
            self.ui_manager.show_main_window()
    
    def _on_show_settings_requested(self):
        """处理显示设置请求"""
        # 这里可以实现设置窗口显示逻辑
        self.logger.info("显示设置窗口请求")
    
    def _on_check_permissions_requested(self):
        """处理检查权限请求"""
        if self.hotkey_manager:
            permissions_ok = self.hotkey_manager.check_permissions()
            self.logger.info(f"权限检查结果: {permissions_ok}")
    
    def _on_restart_hotkey_requested(self):
        """处理重启热键请求"""
        if self.hotkey_manager:
            success = self.hotkey_manager.restart_hotkey_manager()
            self.logger.info(f"热键管理器重启结果: {success}")
    
    def _on_quit_requested(self):
        """处理退出请求"""
        self.logger.info("收到退出请求")
        self.cleanup()
        if self.app:
            self.app.quit()
    
    def _on_hotkey_press(self):
        """处理热键按下（与原始代码保持一致）"""
        if self._can_start_recording():
            # 使用信号确保在主线程中执行（与原始代码一致）
            self.start_recording_signal.emit()

    def _on_hotkey_release(self):
        """处理热键释放（与原始代码保持一致）"""
        if self._can_stop_recording():
            # 使用信号确保在主线程中执行（与原始代码一致）
            self.stop_recording_signal.emit()

    def _can_start_recording(self):
        """统一的录音开始条件检查（与原始代码一致）"""
        return (self.audio_manager and
                not self.audio_manager.is_recording())

    def _can_stop_recording(self):
        """统一的录音停止条件检查（与原始代码一致）"""
        return (self.audio_manager and
                self.audio_manager.is_recording())

    def _start_recording_internal(self):
        """内部录音启动方法（信号槽）"""
        try:
            if self.audio_manager:
                self.audio_manager.start_recording()
        except Exception as e:
            self.logger.error(f"启动录音失败: {e}")

    def _stop_recording_internal(self):
        """内部录音停止方法（信号槽）"""
        try:
            if self.audio_manager:
                self.audio_manager.stop_recording()
        except Exception as e:
            self.logger.error(f"停止录音失败: {e}")

    def _on_hotkey_permission_error(self, error_message: str):
        """处理热键权限错误"""
        self.logger.error(f"热键权限错误: {error_message}")
        # 这里可以显示权限错误对话框
    
    def _on_toggle_recording(self):
        """处理录音按钮点击（与原始代码toggle_recording完全一致）"""
        try:
            if self._can_start_recording():
                # 使用信号确保在主线程中执行（与原始代码一致）
                self.start_recording_signal.emit()
            elif self._can_stop_recording():
                # 使用信号确保在主线程中执行（与原始代码一致）
                self.stop_recording_signal.emit()
        except Exception as e:
            self.logger.error(f"切换录音状态失败: {e}")

    def _on_history_item_clicked(self, text: str):
        """处理历史记录点击事件"""
        try:
            self.logger.info(f"历史记录点击: {text[:50]}...")

            # 检查文本是否有效
            if not text or not text.strip():
                if self.ui_manager and self.ui_manager.main_window:
                    self.ui_manager.main_window.update_status("点击失败")
                return

            # 更新状态
            if self.ui_manager and self.ui_manager.main_window:
                self.ui_manager.main_window.update_status("正在处理历史记录点击...")

            # 这里可以添加剪贴板操作逻辑
            # 暂时只更新状态
            if self.ui_manager and self.ui_manager.main_window:
                self.ui_manager.main_window.update_status("历史记录已处理")

        except Exception as e:
            self.logger.error(f"处理历史记录点击失败: {e}")
            if self.ui_manager and self.ui_manager.main_window:
                self.ui_manager.main_window.update_status("点击处理出错")

    def _on_transcription_completed(self, text: str, language: str = None):
        """处理转写完成"""
        try:
            self.logger.info(f"转写完成: {text[:50]}...")

            # 更新UI显示
            if self.ui_manager and self.ui_manager.main_window:
                self.ui_manager.main_window.display_result(text)
                self.ui_manager.main_window.update_status("转写完成")

        except Exception as e:
            self.logger.error(f"处理转写完成失败: {e}")

    def _on_audio_error(self, error_message: str):
        """处理音频错误"""
        self.logger.error(f"音频错误: {error_message}")

        # 更新UI显示错误
        if self.ui_manager and self.ui_manager.main_window:
            self.ui_manager.main_window.update_status(f"❌ {error_message}")
    
    # 公共接口方法
    def show_main_window(self):
        """显示主窗口"""
        if self.ui_manager:
            self.ui_manager.show_main_window()
    
    def hide_main_window(self):
        """隐藏主窗口"""
        if self.ui_manager:
            self.ui_manager.hide_main_window()
    
    def show_splash(self):
        """显示启动界面"""
        if self.ui_manager:
            self.ui_manager.show_splash()
    
    def hide_splash(self):
        """隐藏启动界面"""
        if self.ui_manager:
            self.ui_manager.hide_splash()
    
    def update_splash_progress(self, message: str, progress: int):
        """更新启动界面进度"""
        if self.ui_manager:
            self.ui_manager.update_splash_progress(message, progress)
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        status = {
            'initialized': self._initialized,
            'managers': {}
        }
        
        if self.ui_manager:
            status['managers']['ui'] = self.ui_manager.get_status()
        
        if self.audio_manager:
            status['managers']['audio'] = self.audio_manager.get_status()
        
        if self.hotkey_manager:
            status['managers']['hotkey'] = self.hotkey_manager.get_hotkey_status()
        
        return status
    
    def cleanup(self):
        """清理所有资源"""
        try:
            self.logger.info("开始清理应用程序上下文")
            
            # 首先停止所有正在进行的录音
            if self.audio_manager:
                try:
                    self.logger.debug("停止正在进行的录音...")
                    if self.audio_manager.is_recording():
                        self.audio_manager.stop_recording()
                    self.logger.debug("录音停止完成")
                except Exception as e:
                    self.logger.error(f"停止录音失败: {e}")
            
            # 按相反顺序清理管理器
            managers = [
                ('hotkey_manager', self.hotkey_manager),
                ('audio_manager', self.audio_manager),
                ('ui_manager', self.ui_manager)
            ]
            
            for name, manager in managers:
                if manager:
                    try:
                        self.logger.debug(f"正在清理{name}...")
                        manager.cleanup()
                        self.logger.debug(f"{name}清理完成")
                    except Exception as e:
                        self.logger.error(f"清理{name}失败: {e}")
            
            # 清理核心组件
            if self.state_manager:
                try:
                    self.logger.debug("正在清理状态管理器...")
                    self.state_manager.cleanup()
                    self.logger.debug("状态管理器清理完成")
                except Exception as e:
                    self.logger.error(f"清理状态管理器失败: {e}")
            
            # 重置初始化状态
            self._initialized = False
            
            self.logger.info("应用程序上下文清理完成")
            
        except Exception as e:
            self.logger.error(f"应用程序上下文清理失败: {e}")
    
    @property
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._initialized
