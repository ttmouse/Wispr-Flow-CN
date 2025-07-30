"""
权限管理器包装器 - 第9步减法重构
将Application类中的权限相关方法迁移到此处
"""
import logging
import subprocess
import time
from PyQt6.QtWidgets import QMessageBox


class PermissionManagerWrapper:
    """权限管理器包装器 - 纯粹的方法迁移，不改变任何逻辑"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("权限管理器包装器创建成功")
    
    def check_development_permissions(self, app_instance):
        """检查开发环境权限 - 从Application类移过来"""
        try:
            pass  # 检查开发环境权限
            
            # 检查辅助功能权限
            accessibility_check = subprocess.run([
                'osascript',
                '-e', 'tell application "System Events"',
                '-e', 'set isEnabled to UI elements enabled',
                '-e', 'return isEnabled',
                '-e', 'end tell'
            ], capture_output=True, text=True)
            
            has_accessibility = 'true' in accessibility_check.stdout.lower()
            
            # 检查麦克风权限
            mic_check = subprocess.run([
                'osascript',
                '-e', 'tell application "System Events"',
                '-e', 'return "mic_check"',
                '-e', 'end tell'
            ], capture_output=True, text=True)
            
            # 如果能执行 AppleScript，说明有基本权限
            has_mic_access = 'mic_check' in mic_check.stdout
            
            missing_permissions = []
            if not has_accessibility:
                missing_permissions.append("辅助功能")
            
            if missing_permissions:
                pass  # 缺少权限
                pass
                pass
                pass
                pass  # 权限设置说明
                
                # 尝试打开系统设置
                try:
                    subprocess.run(['open', 'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'], check=False)
                    pass  # 已尝试打开系统设置页面
                except:
                    pass
                
                pass  # 提示信息
                
                # 给用户一些时间查看信息
                time.sleep(3)
            else:
                pass  # 权限检查通过
            
            # 更新权限缓存
            app_instance.settings_manager.update_permissions_cache(has_accessibility, has_mic_access)
                
        except Exception as e:
            logging.error(f"权限检查失败: {e}")
            # 权限检查失败时也更新缓存，避免重复检查
            app_instance.settings_manager.update_permissions_cache(False, False)
    
    def check_permissions(self, app_instance):
        """检查应用权限状态 - 从Application类移过来"""
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
            msg_box = QMessageBox()
            msg_box.setWindowTitle("权限检查")
            msg_box.setText(status_msg)
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.exec()
        except Exception as e:
            msg_box = QMessageBox()
            msg_box.setWindowTitle("权限检查失败")
            msg_box.setText(f"检查权限时出错：{str(e)}")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.exec()
    
    def get_status(self):
        """获取管理器状态"""
        return {
            'name': 'PermissionManagerWrapper',
            'description': '权限管理器包装器'
        }
