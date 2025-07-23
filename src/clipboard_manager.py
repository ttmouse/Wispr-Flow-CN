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
            import logging
            logging.warning(f"剪贴板功能测试失败: {e}")
        
    def copy_to_clipboard(self, text):
        """复制文本到剪贴板"""
        try:
            # 清理文本，确保没有多余的空白字符
            clean_text = text.strip() if text else ""
            
            # 复制到剪贴板
            pyperclip.copy(clean_text)
            
            # 最小化延迟以提高响应速度
            time.sleep(0.001)
            
            # 验证复制是否成功
            try:
                copied_text = pyperclip.paste()
                if copied_text == clean_text:
                    return True
                else:
                    import logging
                    copied_preview = copied_text[:30] + '...' if copied_text and len(copied_text) > 30 else (copied_text or '(空)')
                    logging.error(f"复制验证失败: 期望 '{clean_text[:30]}...', 实际 '{copied_preview}'")
                    return False
            except Exception as verify_error:
                import logging
                logging.error(f"复制验证失败: {verify_error}")
                return False
            
        except Exception as e:
            import logging
            logging.error(f"复制到剪贴板失败: {e}")
            return False
        
    def paste_to_current_app(self):
        """将剪贴板内容粘贴到当前活动应用"""
        try:
            if self.is_macos:
                # 在macOS上，先确保目标应用获得焦点
                self._ensure_target_app_focus()
                
                # 短暂延迟确保焦点切换完成
                time.sleep(0.1)
                
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
            import logging
            logging.error(f"粘贴失败: {e}")
    
    def _ensure_target_app_focus(self):
        """确保目标应用获得焦点（macOS专用）"""
        try:
            import subprocess
            
            # 获取当前前台应用
            script = '''
            tell application "System Events"
                set frontApp to name of first application process whose frontmost is true
                return frontApp
            end tell
            '''
            
            result = subprocess.run([
                'osascript', '-e', script
            ], capture_output=True, text=True, timeout=2)
            
            current_app = result.stdout.strip()
            
            # 记录当前前台应用用于调试
            pass
            
            # 如果当前是ASR应用，尝试切换到最近使用的其他应用
            if 'python' in current_app.lower() or 'asr' in current_app.lower() or 'dou-flow' in current_app.lower():
                # 获取最近使用的应用列表
                recent_apps_script = '''
                tell application "System Events"
                    set appList to {}
                    repeat with proc in application processes
                        if background only of proc is false and name of proc is not "Python" and name of proc is not "Dou-flow" then
                            set end of appList to name of proc
                        end if
                    end repeat
                    return appList
                end tell
                '''
                
                apps_result = subprocess.run([
                    'osascript', '-e', recent_apps_script
                ], capture_output=True, text=True, timeout=2)
                
                if apps_result.returncode == 0 and apps_result.stdout.strip():
                    apps_list = apps_result.stdout.strip().split(', ')
                    if apps_list and apps_list[0]:
                        target_app = apps_list[0]
                        
                        # 激活目标应用
                        activate_script = f'''
                        tell application "{target_app}"
                            activate
                        end tell
                        '''
                        
                        activate_result = subprocess.run([
                            'osascript', '-e', activate_script
                        ], capture_output=True, text=True, timeout=2)
                        
                        # 记录应用切换结果
                        pass
                        
                        return True
            
            return True
            
        except Exception as e:
            import logging
            logging.error(f"焦点切换失败: {e}")
            return False
    
    def get_clipboard_content(self):
        """获取当前剪贴板内容"""
        try:
            content = pyperclip.paste()
            return content
        except Exception as e:
            import logging
            logging.error(f"获取剪贴板内容失败: {e}")
            return ""
    

    
    def safe_copy_and_paste(self, text):
        """安全的复制粘贴操作"""
        try:
            # 清理文本
            clean_text = text.strip() if text else ""
            if not clean_text:
                import logging
                logging.error("复制粘贴失败: 文本为空")
                return False
            
            # 记录操作前状态用于调试
            pass
            
            # 复制操作，增加重试机制
            copy_success = False
            for attempt in range(3):  # 最多重试3次
                try:
                    pyperclip.copy(clean_text)
                    time.sleep(0.01)  # 增加延迟确保复制完成
                    
                    # 验证复制是否成功
                    copied_text = pyperclip.paste()
                    if copied_text == clean_text:
                        copy_success = True
                        break
                    else:
                        copied_preview = copied_text[:30] + '...' if copied_text and len(copied_text) > 30 else (copied_text or '(空)')
                        import logging
                        logging.warning(f"复制验证失败 (尝试 {attempt + 1}): 期望 '{clean_text[:30]}...', 实际 '{copied_preview}'")
                        if attempt < 2:  # 不是最后一次尝试
                            time.sleep(0.02)  # 等待更长时间再重试
                        
                except Exception as copy_error:
                    import logging
                    logging.error(f"复制到剪贴板失败 (尝试 {attempt + 1}): {copy_error}")
                    if attempt < 2:  # 不是最后一次尝试
                        time.sleep(0.02)
            
            if not copy_success:
                import logging
                logging.error(f"复制操作最终失败: {clean_text[:50]}{'...' if len(clean_text) > 50 else ''}")
                return False
            
            # 执行粘贴操作
            try:
                # 执行粘贴
                self.paste_to_current_app()
                
                # 增加粘贴后的延迟，确保操作完成
                time.sleep(0.05)  # 50ms延迟确保粘贴完成
                
                return True
                
            except Exception as paste_error:
                import logging
                logging.error(f"粘贴操作失败: {paste_error}")
                return False
            
        except Exception as e:
            import logging
            logging.error(f"复制粘贴操作失败: {e}", exc_info=True)
            return False