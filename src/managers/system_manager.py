#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统集成管理器
专门负责系统级功能：托盘、权限检查、系统设置等
"""

import os
import sys
import logging
import subprocess
from typing import Optional, Callable
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon

from .component_manager import ComponentManager

class SystemManager(QObject):
    """系统集成管理器 - 专门负责系统级功能"""

    # 信号定义
    show_window_requested = pyqtSignal()
    show_settings_requested = pyqtSignal()
    permissions_check_requested = pyqtSignal()
    hotkey_restart_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    permissions_status_changed = pyqtSignal(bool, bool)  # accessibility, microphone

    def __init__(self, app_context):
        super().__init__()

        # 使用组合而不是继承
        self.component_manager = ComponentManager(name="系统集成管理器", app_context=app_context)

        # 添加logger
        self.logger = logging.getLogger(self.__class__.__name__)
        self.app_context = app_context
        
        # 系统组件
        self.tray_icon = None
        self.app_icon = None
        
        # 权限状态缓存
        self._accessibility_permission = False
        self._microphone_permission = False
        self._permissions_checked = False
        
        # 回调函数
        self._show_window_callback: Optional[Callable] = None
        self._show_settings_callback: Optional[Callable] = None
        self._check_permissions_callback: Optional[Callable] = None
        self._restart_hotkey_callback: Optional[Callable] = None
        self._quit_callback: Optional[Callable] = None

    # 委托ComponentManager的方法
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
    
    async def _initialize_internal(self) -> bool:
        """初始化系统组件"""
        try:
            # 1. 加载应用图标
            if not self._load_app_icon():
                self.logger.warning("应用图标加载失败，使用默认图标")
            
            # 2. 创建系统托盘
            if not self._create_system_tray():
                self.logger.warning("系统托盘创建失败")
            
            # 3. 设置macOS特定功能
            if sys.platform == 'darwin':
                self._setup_macos_features()
            
            # 4. 检查系统权限
            await self._check_system_permissions()
            
            self.logger.info("系统组件初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"系统组件初始化失败: {e}")
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
    
    def _create_system_tray(self) -> bool:
        """创建系统托盘"""
        try:
            if not QSystemTrayIcon.isSystemTrayAvailable():
                self.logger.warning("系统托盘不可用")
                return False
            
            # 创建托盘图标
            icon = self.app_icon if self.app_icon else QIcon()
            self.tray_icon = QSystemTrayIcon(icon)
            self.tray_icon.setToolTip("Dou-flow")
            
            # 创建托盘菜单
            self._create_tray_menu()
            
            # 显示托盘图标
            self.tray_icon.show()
            
            if not self.tray_icon.isVisible():
                self.logger.warning("托盘图标显示失败")
                return False
            
            self.logger.debug("系统托盘创建成功")
            return True
            
        except Exception as e:
            self.logger.error(f"创建系统托盘失败: {e}")
            return False
    
    def _create_tray_menu(self):
        """创建托盘菜单"""
        tray_menu = QMenu()
        
        # 显示窗口
        show_action = tray_menu.addAction("显示窗口")
        show_action.triggered.connect(self._on_show_window)
        
        # 设置
        settings_action = tray_menu.addAction("快捷键设置...")
        settings_action.triggered.connect(self._on_show_settings)
        
        # 重启热键功能
        restart_hotkey_action = tray_menu.addAction("重启热键功能")
        restart_hotkey_action.triggered.connect(self._on_restart_hotkey)
        
        # 检查权限
        check_permissions_action = tray_menu.addAction("检查权限")
        check_permissions_action.triggered.connect(self._on_check_permissions)
        
        # 分隔线
        tray_menu.addSeparator()
        
        # 退出
        quit_action = tray_menu.addAction("退出")
        quit_action.triggered.connect(self._on_quit)
        
        # 设置菜单
        self.tray_icon.setContextMenu(tray_menu)
    
    def _setup_macos_features(self):
        """设置macOS特定功能"""
        try:
            if self.app_context and hasattr(self.app_context, 'app'):
                app = self.app_context.app
                
                # 设置应用程序属性
                from PyQt6.QtCore import Qt
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
    
    async def _check_system_permissions(self):
        """检查系统权限"""
        try:
            if sys.platform != 'darwin':
                self.logger.debug("非macOS系统，跳过权限检查")
                return
            
            # 检查辅助功能权限
            accessibility_result = subprocess.run([
                'osascript',
                '-e', 'tell application "System Events"',
                '-e', 'set isEnabled to UI elements enabled',
                '-e', 'return isEnabled',
                '-e', 'end tell'
            ], capture_output=True, text=True)
            
            self._accessibility_permission = 'true' in accessibility_result.stdout.lower()
            
            # 检查麦克风权限（简化检查）
            mic_result = subprocess.run([
                'osascript',
                '-e', 'tell application "System Events"',
                '-e', 'return "mic_check"',
                '-e', 'end tell'
            ], capture_output=True, text=True)
            
            self._microphone_permission = 'mic_check' in mic_result.stdout
            
            self._permissions_checked = True
            
            # 发送权限状态信号
            self.permissions_status_changed.emit(
                self._accessibility_permission, 
                self._microphone_permission
            )
            
            # 更新设置管理器中的权限缓存
            if (self.app_context and 
                hasattr(self.app_context, 'settings_manager') and 
                self.app_context.settings_manager):
                self.app_context.settings_manager.update_permissions_cache(
                    self._accessibility_permission, 
                    self._microphone_permission
                )
            
            self.logger.info(f"权限检查完成 - 辅助功能: {self._accessibility_permission}, 麦克风: {self._microphone_permission}")
            
        except Exception as e:
            self.logger.error(f"权限检查失败: {e}")
            self._permissions_checked = False
    
    # 公共接口方法
    def show_tray_message(self, title: str, message: str, icon=QSystemTrayIcon.MessageIcon.Information, timeout=3000):
        """显示托盘通知"""
        if self.tray_icon and self.tray_icon.isVisible():
            self.tray_icon.showMessage(title, message, icon, timeout)
    
    def hide_tray_icon(self):
        """隐藏托盘图标"""
        if self.tray_icon:
            self.tray_icon.hide()
    
    def show_tray_icon(self):
        """显示托盘图标"""
        if self.tray_icon:
            self.tray_icon.show()
    
    def get_permissions_status(self) -> tuple:
        """获取权限状态"""
        return self._accessibility_permission, self._microphone_permission
    
    def open_system_preferences(self, preference_pane: str = None):
        """打开系统偏好设置"""
        try:
            if sys.platform == 'darwin':
                if preference_pane:
                    subprocess.run(['open', f'x-apple.systempreferences:{preference_pane}'], check=False)
                else:
                    subprocess.run(['open', '/System/Applications/System Preferences.app'], check=False)
                self.logger.debug("系统偏好设置已打开")
            else:
                self.logger.warning("非macOS系统，无法打开系统偏好设置")
        except Exception as e:
            self.logger.error(f"打开系统偏好设置失败: {e}")
    
    # 事件处理方法
    def _on_show_window(self):
        """处理显示窗口请求"""
        if self._show_window_callback:
            self._show_window_callback()
        else:
            self.show_window_requested.emit()
    
    def _on_show_settings(self):
        """处理显示设置请求"""
        if self._show_settings_callback:
            self._show_settings_callback()
        else:
            self.show_settings_requested.emit()
    
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
        """清理系统资源"""
        try:
            # 清理托盘图标
            if self.tray_icon:
                self.tray_icon.hide()
                self.tray_icon = None
            
            self.logger.debug("系统资源清理完成")
            
        except Exception as e:
            self.logger.error(f"系统资源清理失败: {e}")
