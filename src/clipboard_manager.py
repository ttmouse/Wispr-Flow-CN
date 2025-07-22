import pyperclip
import time
from pynput.keyboard import Controller, Key
import platform

class ClipboardManager:
    def __init__(self, debug_mode=False):
        """初始化剪贴板管理器"""
        self.keyboard = Controller()
        self.is_macos = platform.system() == 'Darwin'
        self.platform = platform.system().lower()
        self.debug_mode = debug_mode
        # 测试剪贴板功能
        try:
            test_content = pyperclip.paste()
            pass  # 剪贴板功能测试成功
        except Exception as e:
            print(f"⚠️ 剪贴板功能测试失败: {e}")
        
    def copy_to_clipboard(self, text):
        """复制文本到剪贴板"""
        try:
            # 清理文本，确保没有多余的空白字符
            clean_text = text.strip() if text else ""
            
            if self.debug_mode:
                before_content = pyperclip.paste()
                print(f"🔍 [调试] 复制前剪贴板内容: '{before_content[:30]}...'")
            
            # 复制到剪贴板
            pyperclip.copy(clean_text)
            
            # 给剪贴板时间来处理
            time.sleep(0.05)
            
            # 验证复制是否成功
            try:
                copied_text = pyperclip.paste()
                if copied_text == clean_text:
                    if self.debug_mode:
                        print(f"🔍 [调试] 复制成功")
                    print(f"✓ 文本已复制到剪贴板: {clean_text[:50]}{'...' if len(clean_text) > 50 else ''}")
                    return True
                else:
                    print(f"❌ 复制验证失败: 期望 '{clean_text[:30]}...', 实际 '{copied_text[:30]}...'")
                    return False
            except Exception as verify_error:
                print(f"❌ 复制验证失败: {verify_error}")
                return False
            
        except Exception as e:
            print(f"❌ 复制到剪贴板失败: {e}")
            return False
        
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
            print(f"❌ 粘贴失败: {e}")
    
    def get_clipboard_content(self):
        """获取当前剪贴板内容"""
        try:
            content = pyperclip.paste()
            return content
        except Exception as e:
            print(f"❌ 获取剪贴板内容失败: {e}")
            return ""
    

    
    def safe_copy_and_paste(self, text):
        """安全的复制粘贴操作"""
        try:
            # 清理文本
            clean_text = text.strip() if text else ""
            if not clean_text:
                return False
            
            # 调试模式：记录操作前的剪贴板状态
            if self.debug_mode:
                before_content = self.get_clipboard_content()
                print(f"🔍 [调试] 操作前剪贴板内容: '{before_content[:50]}{'...' if len(before_content) > 50 else ''}'")
                print(f"🔍 [调试] 准备复制的内容: '{clean_text[:50]}{'...' if len(clean_text) > 50 else ''}'")
            
            # 复制到剪贴板
            copy_success = self.copy_to_clipboard(clean_text)
            if not copy_success:
                return False
            
            # 执行粘贴操作
            if self.debug_mode:
                print(f"🔍 [调试] 准备粘贴内容: '{clean_text[:30]}...'")
            
            # 执行粘贴
            self.paste_to_current_app()
            
            # 给粘贴操作一点时间
            time.sleep(0.05)
            if self.debug_mode:
                final_content = self.get_clipboard_content()
                print(f"🔍 [调试] 粘贴完成，剪贴板内容: '{final_content[:30]}...'")
            
            return True
            
        except Exception as e:
            print(f"❌ 复制粘贴操作失败: {e}")
            return False