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
        print(f"✓ 剪贴板管理器已初始化 (平台: {self.platform}, 调试模式: {debug_mode})")
        
        # 测试剪贴板功能
        try:
            test_content = pyperclip.paste()
            print(f"✓ 剪贴板功能测试成功")
        except Exception as e:
            print(f"⚠️ 剪贴板功能测试失败: {e}")
        
    def copy_to_clipboard(self, text):
        """复制文本到剪贴板"""
        try:
            # 清理文本，确保没有多余的空白字符
            clean_text = text.strip() if text else ""
            
            # 先清空剪贴板，防止累积历史内容
            try:
                pyperclip.copy("")
                time.sleep(0.02)
            except Exception as clear_error:
                print(f"⚠️ 清空剪贴板失败: {clear_error}")
            
            # 复制到剪贴板
            pyperclip.copy(clean_text)
            
            # 给剪贴板一点时间来处理
            time.sleep(0.05)
            
            # 验证复制是否成功
            try:
                copied_text = pyperclip.paste()
                if copied_text == clean_text:
                    print(f"✓ 文本已复制到剪贴板: {clean_text[:50]}{'...' if len(clean_text) > 50 else ''}")
                    return True
                else:
                    print(f"⚠️ 剪贴板内容不匹配: 期望 '{clean_text[:30]}...', 实际 '{copied_text[:30]}...'")
                    return False
            except Exception as verify_error:
                print(f"⚠️ 剪贴板验证出错: {verify_error}")
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
                    
                print("✓ 粘贴命令已发送 (Cmd+V)")
            else:
                # Windows/Linux 使用 Ctrl+V
                with self.keyboard.pressed(Key.ctrl):
                    self.keyboard.press('v')
                    self.keyboard.release('v')
                    
                print("✓ 粘贴命令已发送 (Ctrl+V)")
                
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
        """安全的复制并粘贴操作，确保粘贴的是正确内容"""
        try:
            # 清理文本
            clean_text = text.strip() if text else ""
            if not clean_text:
                print("⚠️ 文本为空，跳过粘贴操作")
                return False
            
            # 调试模式：记录操作前的剪贴板状态
            if self.debug_mode:
                before_content = self.get_clipboard_content()
                print(f"🔍 [调试] 操作前剪贴板内容: '{before_content[:50]}{'...' if len(before_content) > 50 else ''}'")
                print(f"🔍 [调试] 准备复制的内容: '{clean_text[:50]}{'...' if len(clean_text) > 50 else ''}'")
            
            # 立即复制到剪贴板
            success = self.copy_to_clipboard(clean_text)
            if not success:
                print("❌ 复制文本失败，取消粘贴操作")
                return False
            
            # 调试模式：验证复制后的剪贴板内容
            if self.debug_mode:
                after_copy = self.get_clipboard_content()
                print(f"🔍 [调试] 复制后剪贴板内容: '{after_copy[:50]}{'...' if len(after_copy) > 50 else ''}'")
                if after_copy != clean_text:
                    print(f"⚠️ [调试] 复制后内容不匹配！")
            
            # 立即执行粘贴，减少时间窗口
            self.paste_to_current_app()
            
            # 注意：不再验证粘贴后的剪贴板内容，因为某些应用会修改剪贴板
            # 这是正常行为，不应该被视为错误
            print(f"✓ 安全粘贴成功: {clean_text[:50]}{'...' if len(clean_text) > 50 else ''}")
            return True
            
        except Exception as e:
            print(f"❌ 安全粘贴操作失败: {e}")
            return False