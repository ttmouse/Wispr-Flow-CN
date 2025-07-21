"""权限检查工具模块"""

import os
import sys
import subprocess
from typing import Dict, List, Tuple, Optional
import logging

class PermissionChecker:
    """统一的权限检查器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def check_permissions(self) -> Dict[str, bool]:
        """检查所有必要的权限"""
        results = {
            'accessibility': self.accessibility_check(),
            'microphone': self.microphone_check(),
            'system_events': self.system_events_check()
        }
        
        self.logger.info(f"权限检查结果: {results}")
        return results
    
    def accessibility_check(self) -> bool:
        """检查辅助功能权限"""
        try:
            if sys.platform != 'darwin':
                return True  # 非macOS系统默认通过
            
            # 检查辅助功能权限
            script = '''
            tell application "System Events"
                try
                    set frontApp to name of first application process whose frontmost is true
                    return true
                on error
                    return false
                end try
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            return result.returncode == 0 and 'true' in result.stdout.lower()
            
        except Exception as e:
            self.logger.error(f"辅助功能权限检查失败: {e}")
            return False
    
    def microphone_check(self) -> bool:
        """检查麦克风权限"""
        try:
            if sys.platform != 'darwin':
                return True  # 非macOS系统默认通过
            
            # 尝试访问麦克风
            import pyaudio
            
            audio = None
            stream = None
            
            try:
                audio = pyaudio.PyAudio()
                
                # 尝试打开音频流
                stream = audio.open(
                    format=pyaudio.paFloat32,
                    channels=1,
                    rate=16000,
                    input=True,
                    frames_per_buffer=1024
                )
                
                # 如果能成功打开，说明有权限
                return True
                
            except Exception as e:
                self.logger.warning(f"麦克风权限检查失败: {e}")
                return False
                
            finally:
                if stream:
                    try:
                        stream.close()
                    except:
                        pass
                if audio:
                    try:
                        audio.terminate()
                    except:
                        pass
                        
        except ImportError:
            self.logger.warning("pyaudio未安装，跳过麦克风权限检查")
            return True
        except Exception as e:
            self.logger.error(f"麦克风权限检查异常: {e}")
            return False
    
    def system_events_check(self) -> bool:
        """检查系统事件权限"""
        try:
            if sys.platform != 'darwin':
                return True  # 非macOS系统默认通过
            
            # 检查是否能访问系统事件
            script = '''
            tell application "System Events"
                try
                    get name of every process
                    return true
                on error
                    return false
                end try
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            return result.returncode == 0 and 'true' in result.stdout.lower()
            
        except Exception as e:
            self.logger.error(f"系统事件权限检查失败: {e}")
            return False
    
    def request_permissions(self) -> Dict[str, bool]:
        """请求必要的权限"""
        results = {}
        
        # 检查当前权限状态
        current_permissions = self.check_permissions()
        
        for permission, granted in current_permissions.items():
            if not granted:
                results[permission] = self._request_permission(permission)
            else:
                results[permission] = True
        
        return results
    
    def _request_permission(self, permission_type: str) -> bool:
        """请求特定权限"""
        try:
            if sys.platform != 'darwin':
                return True
            
            if permission_type == 'accessibility':
                return self._request_accessibility_permission()
            elif permission_type == 'microphone':
                return self._request_microphone_permission()
            elif permission_type == 'system_events':
                return self._request_system_events_permission()
            
            return False
            
        except Exception as e:
            self.logger.error(f"请求{permission_type}权限失败: {e}")
            return False
    
    def _request_accessibility_permission(self) -> bool:
        """请求辅助功能权限"""
        try:
            # 打开系统偏好设置的辅助功能页面
            subprocess.run([
                'open', 
                'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'
            ])
            
            self.logger.info("已打开辅助功能权限设置页面")
            return False  # 需要用户手动授权
            
        except Exception as e:
            self.logger.error(f"打开辅助功能设置失败: {e}")
            return False
    
    def _request_microphone_permission(self) -> bool:
        """请求麦克风权限"""
        try:
            # 尝试访问麦克风会自动触发权限请求
            import pyaudio
            
            audio = pyaudio.PyAudio()
            stream = audio.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024
            )
            stream.close()
            audio.terminate()
            
            return True
            
        except Exception as e:
            self.logger.warning(f"麦克风权限请求失败: {e}")
            return False
    
    def _request_system_events_permission(self) -> bool:
        """请求系统事件权限"""
        try:
            # 打开系统偏好设置的自动化页面
            subprocess.run([
                'open', 
                'x-apple.systempreferences:com.apple.preference.security?Privacy_Automation'
            ])
            
            self.logger.info("已打开自动化权限设置页面")
            return False  # 需要用户手动授权
            
        except Exception as e:
            self.logger.error(f"打开自动化设置失败: {e}")
            return False
    
    def get_permission_status_message(self, permissions: Dict[str, bool]) -> str:
        """获取权限状态消息"""
        messages = []
        
        for permission, granted in permissions.items():
            status = "✓" if granted else "✗"
            permission_name = {
                'accessibility': '辅助功能',
                'microphone': '麦克风',
                'system_events': '系统事件'
            }.get(permission, permission)
            
            messages.append(f"{status} {permission_name}")
        
        return " | ".join(messages)


# 全局权限检查器实例
permission_checker = PermissionChecker()

# 便捷函数
def check_permissions() -> Dict[str, bool]:
    """检查所有权限"""
    return permission_checker.check_permissions()

def accessibility_check() -> bool:
    """检查辅助功能权限"""
    return permission_checker.accessibility_check()

def microphone_check() -> bool:
    """检查麦克风权限"""
    return permission_checker.microphone_check()

def system_events_check() -> bool:
    """检查系统事件权限"""
    return permission_checker.system_events_check()

def request_permissions() -> Dict[str, bool]:
    """请求所有必要权限"""
    return permission_checker.request_permissions()