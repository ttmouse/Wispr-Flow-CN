#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI管理器
专门负责界面相关操作
"""

import os
import sys
import logging
from typing import Optional, Callable
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtGui import QIcon

from .component_manager import ComponentManager

class UIManager(QObject):
    """UI管理器 - 专门负责界面相关操作"""

    # 信号定义
    window_show_requested = pyqtSignal()
    settings_show_requested = pyqtSignal()
    permissions_check_requested = pyqtSignal()
    hotkey_restart_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self, app_context):
        super().__init__()

        # 使用组合而不是继承
        self.component_manager = ComponentManager(name="UI管理器", app_context=app_context)

        # 添加logger
        self.logger = logging.getLogger(self.__class__.__name__)
        self.app_context = app_context
        
        # UI组件
        self.main_window = None
        self.settings_window = None
        self.splash = None
        self.tray_icon = None
        self.app_icon = None
        
        # 回调函数
        self._show_window_callback: Optional[Callable] = None
        self._show_settings_callback: Optional[Callable] = None
        self._check_permissions_callback: Optional[Callable] = None
        self._restart_hotkey_callback: Optional[Callable] = None
        self._quit_callback: Optional[Callable] = None

    # 委托ComponentManager的方法
    def initialize_sync(self):
        """同步初始化UI管理器"""
        try:
            return self._initialize_internal_sync()
        except Exception as e:
            self.logger.error(f"UI管理器同步初始化失败: {e}")
            return False

    async def initialize(self):
        # 设置内部初始化方法
        self.component_manager._initialize_internal = self._initialize_internal
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
                     show_window: Optional[Callable] = None,
                     show_settings: Optional[Callable] = None,
                     check_permissions: Optional[Callable] = None,
                     restart_hotkey: Optional[Callable] = None,
                     quit_app: Optional[Callable] = None):
        """设置回调函数"""
        self._show_window_callback = show_window
        self._show_settings_callback = show_settings
        self._check_permissions_callback = check_permissions
        self._restart_hotkey_callback = restart_hotkey
        self._quit_callback = quit_app

    def _initialize_internal_sync(self) -> bool:
        """同步初始化UI组件"""
        try:
            # 1. 加载应用图标
            if not self._load_app_icon():
                self.logger.warning("应用图标加载失败，使用默认图标")

            # 2. 创建主窗口
            if not self._create_main_window():
                return False

            # 3. 系统托盘由SystemManager负责创建，这里不再创建
            # 避免重复创建托盘图标
            self.logger.debug("系统托盘由SystemManager负责创建")

            # 4. 创建启动界面
            if not self._create_splash_screen():
                self.logger.warning("启动界面创建失败")

            # 5. 设置macOS特定功能
            if sys.platform == 'darwin':
                self._setup_macos_features()

            self.logger.info("UI组件同步初始化完成")
            return True

        except Exception as e:
            self.logger.error(f"UI组件同步初始化失败: {e}")
            return False

    async def _initialize_internal(self) -> bool:
        """初始化UI组件"""
        try:
            # 1. 加载应用图标
            if not self._load_app_icon():
                self.logger.warning("应用图标加载失败，使用默认图标")
            
            # 2. 创建主窗口
            if not self._create_main_window():
                return False
            
            # 3. 系统托盘由SystemManager负责创建，这里不再创建
            # 避免重复创建托盘图标
            self.logger.debug("系统托盘由SystemManager负责创建")
            
            # 4. 创建启动界面
            if not self._create_splash_screen():
                self.logger.warning("启动界面创建失败")
            
            # 5. 设置macOS特定功能
            if sys.platform == 'darwin':
                self._setup_macos_features()
            
            self.logger.info("UI组件初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"UI组件初始化失败: {e}")
            return False
    
    def _load_app_icon(self) -> bool:
        """加载应用图标"""
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "..", "..", "iconset.icns")
            if os.path.exists(icon_path):
                self.app_icon = QIcon(icon_path)
                
                # 设置应用程序图标
                if self.app_context and hasattr(self.app_context, 'app'):
                    self.app_context.app.setWindowIcon(self.app_icon)
                
                self.logger.debug("应用图标加载成功")
                return True
            else:
                self.logger.warning(f"图标文件不存在: {icon_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"加载应用图标失败: {e}")
            return False
    
    def _create_main_window(self) -> bool:
        """创建主窗口"""
        try:
            from ui.main_window import MainWindow
            
            self.main_window = MainWindow(app_instance=self.app_context)
            
            # 设置状态管理器
            if (self.app_context and 
                hasattr(self.app_context, 'state_manager') and 
                self.app_context.state_manager):
                self.main_window.set_state_manager(self.app_context.state_manager)
            
            # 初始时隐藏主窗口
            self.main_window.hide()
            
            self.logger.debug("主窗口创建成功")
            return True
            
        except Exception as e:
            self.logger.error(f"创建主窗口失败: {e}")
            return False
    
    def _create_system_tray(self) -> bool:
        """创建系统托盘 - 已移至SystemManager，避免重复创建"""
        # 系统托盘现在由SystemManager统一管理
        # 这里保留方法以保持兼容性，但不执行任何操作
        self.logger.debug("系统托盘创建已委托给SystemManager")
        return True
    
    def _create_tray_menu(self):
        """创建托盘菜单 - 已移至SystemManager"""
        # 托盘菜单现在由SystemManager统一管理
        self.logger.debug("托盘菜单创建已委托给SystemManager")
    
    def _create_splash_screen(self) -> bool:
        """创建启动界面"""
        try:
            from app_loader import LoadingSplash
            
            self.splash = LoadingSplash()
            
            self.logger.debug("启动界面创建成功")
            return True
            
        except Exception as e:
            self.logger.error(f"创建启动界面失败: {e}")
            return False
    
    def _setup_macos_features(self):
        """设置macOS特定功能"""
        try:
            if self.app_context and hasattr(self.app_context, 'app'):
                app = self.app_context.app
                
                # 设置应用程序属性
                app.setAttribute(Qt.ApplicationAttribute.AA_DontShowIconsInMenus, False)
                app.setQuitOnLastWindowClosed(False)
                
                # 设置应用程序信息
                app.setApplicationName("Dou-flow")
                app.setApplicationDisplayName("Dou-flow")
                
                # 设置Dock点击处理
                app.setProperty("DOCK_CLICK_HANDLER", True)
                
                self.logger.debug("macOS特性设置完成")
                
        except Exception as e:
            self.logger.error(f"设置macOS特性失败: {e}")
    
    # 公共接口方法
    def show_main_window(self):
        """显示主窗口"""
        if self.main_window:
            self.main_window._show_window_internal()
            self.logger.debug("主窗口显示请求已发送")
    
    def hide_main_window(self):
        """隐藏主窗口"""
        if self.main_window:
            self.main_window.hide()
            self.logger.debug("主窗口已隐藏")
    
    def show_splash(self):
        """显示启动界面"""
        if self.splash:
            self.splash.show()
            self.logger.debug("启动界面已显示")
    
    def hide_splash(self):
        """隐藏启动界面"""
        if self.splash:
            self.splash.close()
            self.splash = None
            self.logger.debug("启动界面已隐藏")
    
    def update_splash_progress(self, message: str, progress: int):
        """更新启动界面进度"""
        if self.splash:
            self.splash.update_progress(message, progress)
    
    # 事件处理方法
    def _on_show_window(self):
        """处理显示窗口请求"""
        if self._show_window_callback:
            self._show_window_callback()
        else:
            self.window_show_requested.emit()
    
    def _on_show_settings(self):
        """处理显示设置请求"""
        if self._show_settings_callback:
            self._show_settings_callback()
        else:
            self.settings_show_requested.emit()
    
    def _on_check_permissions(self):
        """处理检查权限请求"""
        if self._check_permissions_callback:
            self._check_permissions_callback()
        else:
            self.permissions_check_requested.emit()
    
    def _on_restart_hotkey(self):
        """处理重启热键请求"""
        if self._restart_hotkey_callback:
            self._restart_hotkey_callback()
        else:
            self.hotkey_restart_requested.emit()
    
    def _on_quit(self):
        """处理退出请求"""
        if self._quit_callback:
            self._quit_callback()
        else:
            self.quit_requested.emit()
    
    def _cleanup_internal(self):
        """清理UI资源"""
        try:
            # 清理启动界面
            if self.splash:
                self.splash.close()
                self.splash = None
            
            # 清理设置窗口
            if self.settings_window:
                self.settings_window.close()
                self.settings_window = None
            
            # 托盘图标由SystemManager负责清理
            # 这里不再处理托盘图标
            self.logger.debug("托盘图标清理已委托给SystemManager")
            
            # 清理主窗口
            if self.main_window:
                self.main_window.close()
                self.main_window = None
            
            self.logger.debug("UI资源清理完成")
            
        except Exception as e:
            self.logger.error(f"UI资源清理失败: {e}")
