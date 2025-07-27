import pyperclip
import time
from pynput.keyboard import Controller, Key
import platform

class ClipboardManager:
    def __init__(self):
        self.keyboard = Controller()
        self.is_macos = platform.system() == 'Darwin'
        
    def copy_to_clipboard(self, text):
        """复制文本到剪贴板"""
        pyperclip.copy(text)
        # 给剪贴板一点时间来处理
        time.sleep(0.1)
        
    def paste_to_current_app(self):
        """将剪贴板内容粘贴到当前活动应用"""
        try:
            if self.is_macos:
                # macOS 使用 Command+V
                with self.keyboard.pressed(Key.cmd):
                    self.keyboard.press('v')
                    self.keyboard.release('v')
            else:
                # Windows/Linux 使用 Ctrl+V
                with self.keyboard.pressed(Key.ctrl):
                    self.keyboard.press('v')
                    self.keyboard.release('v')
        except Exception as e:
            print(f"粘贴失败: {e}")