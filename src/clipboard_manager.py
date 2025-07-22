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
        """复制文本到剪贴板，确保完全替换而不是累积"""
        try:
            # 清理文本，确保没有多余的空白字符
            clean_text = text.strip() if text else ""
            
            if self.debug_mode:
                before_content = pyperclip.paste()
                print(f"🔍 [调试] 复制前剪贴板内容: '{before_content[:30]}...'")
            
            # 彻底清空剪贴板，防止累积历史内容
            clear_success = self._thorough_clear_clipboard()
            if not clear_success:
                print("⚠️ 剪贴板清空不完全，但继续执行复制操作")
            
            # 多次尝试复制，确保成功
            max_copy_attempts = 3
            for attempt in range(max_copy_attempts):
                # 复制到剪贴板
                pyperclip.copy(clean_text)
                
                # 给剪贴板充足时间来处理
                time.sleep(0.08)  # 增加等待时间
                
                # 验证复制是否成功
                try:
                    copied_text = pyperclip.paste()
                    if copied_text == clean_text:
                        if self.debug_mode:
                            print(f"🔍 [调试] 第{attempt+1}次复制成功")
                        print(f"✓ 文本已完全替换到剪贴板: {clean_text[:50]}{'...' if len(clean_text) > 50 else ''}")
                        return True
                    else:
                        if attempt < max_copy_attempts - 1:
                            # 重新清空再试
                            self._thorough_clear_clipboard()
                        else:
                            print(f"❌ 多次尝试后仍不匹配: 期望 '{clean_text[:30]}...', 实际 '{copied_text[:30]}...'")
                            return False
                except Exception as verify_error:
                    if attempt == max_copy_attempts - 1:
                        return False
            
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
    
    def _thorough_clear_clipboard(self):
        """彻底清空剪贴板，确保没有历史残留"""
        try:
            # 使用更强力的清空策略，防止内容累积
            clear_attempts = 5  # 增加清空尝试次数
            
            for i in range(clear_attempts):
                # 先设置为空字符串
                pyperclip.copy("")
                time.sleep(0.02)  # 增加等待时间
                
                # 再设置为单个空格，然后再清空（某些系统需要这样）
                pyperclip.copy(" ")
                time.sleep(0.01)
                pyperclip.copy("")
                time.sleep(0.02)
                
                # 验证是否清空成功
                current_content = pyperclip.paste()
                if not current_content or current_content.strip() == "":
                    if self.debug_mode:
                        print(f"🔍 [调试] 剪贴板已在第{i+1}次尝试后彻底清空")
                    return True
                elif i == clear_attempts - 1:  # 最后一次尝试
                    # 最后尝试：强制设置为特殊标记再清空
                    pyperclip.copy("__CLEAR_MARKER__")
                    time.sleep(0.01)
                    pyperclip.copy("")
                    time.sleep(0.02)
                    
            return False
                    
        except Exception as e:
            return False
    
    def safe_copy_and_paste(self, text):
        """安全的复制粘贴操作，确保完全替换而不是累积"""
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
            
            # 使用增强的复制方法，确保完全替换
            copy_success = self.copy_to_clipboard(clean_text)
            if not copy_success:
                return False
            
            # 额外的安全验证：确保剪贴板内容正确
            max_verify_attempts = 3
            for verify_attempt in range(max_verify_attempts):
                try:
                    clipboard_content = self.get_clipboard_content()
                    if clipboard_content == clean_text:
                        if self.debug_mode:
                            print(f"🔍 [调试] 第{verify_attempt+1}次验证成功，剪贴板内容正确")
                        break
                    else:
                        if verify_attempt < max_verify_attempts - 1:
                            # 重新执行完整的复制流程
                            self._thorough_clear_clipboard()
                            pyperclip.copy(clean_text)
                            time.sleep(0.1)
                        else:
                            print(f"❌ 多次验证失败: 期望 '{clean_text[:30]}...', 实际 '{clipboard_content[:30]}...'")
                            return False
                            
                except Exception as verify_error:
                    if verify_attempt == max_verify_attempts - 1:
                        return False
            
            # 执行粘贴操作
            if self.debug_mode:
                print(f"🔍 [调试] 准备粘贴内容: '{clean_text[:30]}...'")
            
            # 立即执行粘贴，减少时间窗口
            self.paste_to_current_app()
            
            # 粘贴后保留剪贴板内容，不清空
            # 这样用户可以继续使用 Cmd+V 粘贴相同内容
            time.sleep(0.05)  # 给粘贴操作一点时间
            if self.debug_mode:
                final_content = self.get_clipboard_content()
                print(f"🔍 [调试] 粘贴完成，剪贴板保留内容: '{final_content[:30]}...'")
            
            return True
            
        except Exception as e:
            print(f"❌ 安全粘贴操作失败: {e}")
            return False