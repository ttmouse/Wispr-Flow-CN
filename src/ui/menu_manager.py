import rumps
import os
import subprocess
from ..utils.config import Config
from .settings_window import SettingsWindow

class MenuManager:
    def __init__(self, app):
        self.app = app
        self.config = Config()
        self.settings_window = None
        
        # 创建菜单项
        self.menu = {
            "设置": self.on_settings,
            "检查权限": self.check_permissions,
            None: None,  # 分隔线
            "退出": self.on_quit
        }
        
        # 添加菜单项到应用
        for title, callback in self.menu.items():
            if title is None:
                self.app.menu.add(rumps.separator)
            else:
                self.app.menu.add(rumps.MenuItem(title=title, callback=callback))

    def check_permissions(self, _):
        """检查应用权限状态"""
        try:
            # 检查麦克风权限
            mic_status = subprocess.run([
                'osascript',
                '-e', 'tell application "System Events" to tell process "SystemUIServer"',
                '-e', 'get value of first menu bar item of menu bar 1 whose description contains "麦克风"',
                '-e', 'end tell'
            ], capture_output=True, text=True)
            
            # 检查辅助功能权限
            accessibility_status = subprocess.run([
                'osascript',
                '-e', 'tell application "System Events"',
                '-e', 'set isEnabled to UI elements enabled',
                '-e', 'return isEnabled',
                '-e', 'end tell'
            ], capture_output=True, text=True)
            
            # 检查自动化权限
            automation_status = subprocess.run([
                'osascript',
                '-e', 'tell application "System Events"',
                '-e', 'return "已授权"',
                '-e', 'end tell'
            ], capture_output=True, text=True)
            
            # 准备状态消息
            status_msg = "权限状态：\n\n"
            status_msg += f"麦克风：{'已授权' if '1' in mic_status.stdout else '未授权'}\n"
            status_msg += f"辅助功能：{'已授权' if 'true' in accessibility_status.stdout.lower() else '未授权'}\n"
            status_msg += f"自动化：{'已授权' if '已授权' in automation_status.stdout else '未授权'}\n\n"
            
            if '未授权' in status_msg:
                status_msg += "请在系统设置中授予以下权限：\n"
                status_msg += "1. 系统设置 > 隐私与安全性 > 麦克风\n"
                status_msg += "2. 系统设置 > 隐私与安全性 > 辅助功能\n"
                status_msg += "3. 系统设置 > 隐私与安全性 > 自动化"
            
            # 显示状态
            rumps.alert(
                title="权限检查",
                message=status_msg,
                ok="确定"
            )
            
        except Exception as e:
            rumps.alert(
                title="权限检查失败",
                message=f"检查权限时出错：{str(e)}",
                ok="确定"
            )

    def on_settings(self, _):
        """打开设置窗口"""
        if not self.settings_window:
            self.settings_window = SettingsWindow()
        self.settings_window.show()

    def on_quit(self, _):
        """退出应用"""
        try:
            # 调用主应用的退出方法，确保资源被正确清理
            if hasattr(self.app, 'quit_application'):
                self.app.quit_application()
            else:
                # 如果主应用没有quit_application方法，使用rumps默认退出
                rumps.quit_application()
        except Exception as e:
            import logging
            logging.error(f"退出应用时出错: {e}")
            # 强制退出
            rumps.quit_application()