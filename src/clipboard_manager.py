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
        try:
            pyperclip.copy(text)
            # 给剪贴板一点时间来处理
            time.sleep(0.1)
            
            # 验证复制是否成功
            copied_text = pyperclip.paste()
            if copied_text != text:
                print(f"⚠️ 剪贴板复制验证失败，期望: {text[:50]}..., 实际: {copied_text[:50]}...")
            else:
                print(f"✓ 文本已复制到剪贴板: {text[:50]}{'...' if len(text) > 50 else ''}")
        except Exception as e:
            print(f"❌ 复制到剪贴板失败: {e}")
        
    def paste_to_current_app(self):
        """将剪贴板内容粘贴到当前活动应用"""
        try:
            if self.is_macos:
                # macOS 使用 Command+V
                with self.keyboard.pressed(Key.cmd):
                    self.keyboard.press('v')
                    self.keyboard.release('v')
                    
                print("✓ 粘贴命令已发送 (Cmd+V)")
            else:
                # Windows/Linux 使用 Ctrl+V
                with self.keyboard.pressed(Key.ctrl):
                    self.keyboard.press('v')
                    self.keyboard.release('v')
                    
                print("✓ 粘贴命令已发送 (Ctrl+V)")
                
        except Exception as e:
            print(f"❌ 粘贴失败: {e}")