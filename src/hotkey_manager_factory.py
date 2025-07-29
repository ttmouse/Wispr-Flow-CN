import logging
from typing import Optional

# 尝试不同的导入方式以适应不同的运行环境
try:
    # 最后尝试直接导入（当在同一目录时）
    from hotkey_manager_base import HotkeyManagerBase
    from hotkey_manager import PythonHotkeyManager
    from hammerspoon_hotkey_manager import HammerspoonHotkeyManager
except ImportError:
    try:
        # 然后尝试从src包导入
        from src.hotkey_manager_base import HotkeyManagerBase
        from src.hotkey_manager import PythonHotkeyManager
        from src.hammerspoon_hotkey_manager import HammerspoonHotkeyManager
    except ImportError:
        # 首先尝试相对导入（当作为模块导入时）
        from .hotkey_manager_base import HotkeyManagerBase
        from .hotkey_manager import PythonHotkeyManager
        from .hammerspoon_hotkey_manager import HammerspoonHotkeyManager

class HotkeyManagerFactory:
    """热键管理器工厂类"""
    
    @staticmethod
    def create_hotkey_manager(scheme: str, settings_manager=None) -> Optional[HotkeyManagerBase]:
        """创建热键管理器实例
        
        Args:
            scheme: 热键方案，'hammerspoon' 或 'python'
            settings_manager: 设置管理器实例
            
        Returns:
            HotkeyManagerBase: 热键管理器实例，创建失败时返回None
        """
        logger = logging.getLogger('HotkeyManagerFactory')
        
        try:
            if scheme == 'hammerspoon':
                # 检查Hammerspoon是否可用
                manager = HammerspoonHotkeyManager(settings_manager)
                if manager._check_hammerspoon_available():
                    logger.debug("创建Hammerspoon热键管理器成功")
                    return manager
                else:
                    logger.warning("Hammerspoon不可用，回退到Python方案")
                    # 自动回退到Python方案
                    if settings_manager:
                        settings_manager.set_hotkey_scheme('python')
                    return PythonHotkeyManager(settings_manager)
                    
            elif scheme == 'python':
                logger.debug("创建Python热键管理器成功")
                return PythonHotkeyManager(settings_manager)
                
            else:
                logger.error(f"未知的热键方案: {scheme}")
                # 默认使用Python方案
                logger.debug("使用默认的Python热键管理器")
                return PythonHotkeyManager(settings_manager)
                
        except Exception as e:
            logger.error(f"创建热键管理器失败: {e}")
            # 出错时回退到Python方案
            try:
                logger.debug("回退到Python热键管理器")
                return PythonHotkeyManager(settings_manager)
            except Exception as fallback_error:
                logger.error(f"回退方案也失败: {fallback_error}")
                return None
    
    @staticmethod
    def get_available_schemes() -> list:
        """获取可用的热键方案列表
        
        Returns:
            list: 可用方案列表
        """
        schemes = ['python']  # Python方案总是可用
        
        # 检查Hammerspoon是否可用
        try:
            import subprocess
            result = subprocess.run(['which', 'hs'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                schemes.insert(0, 'hammerspoon')  # Hammerspoon优先
        except Exception:
            pass
        
        return schemes
    
    @staticmethod
    def is_scheme_available(scheme: str) -> bool:
        """检查指定方案是否可用
        
        Args:
            scheme: 方案名称
            
        Returns:
            bool: 方案是否可用
        """
        if scheme == 'python':
            return True
        elif scheme == 'hammerspoon':
            try:
                import subprocess
                result = subprocess.run(['which', 'hs'], capture_output=True, text=True, timeout=5)
                return result.returncode == 0
            except Exception:
                return False
        else:
            return False
    
    @staticmethod
    def get_scheme_info(scheme: str) -> dict:
        """获取方案信息
        
        Args:
            scheme: 方案名称
            
        Returns:
            dict: 方案信息字典
        """
        scheme_info = {
            'hammerspoon': {
                'name': 'Hammerspoon方案',
                'description': '基于Hammerspoon的热键监听，更稳定可靠',
                'pros': ['系统级集成', '高稳定性', '低CPU占用', '事件驱动'],
                'cons': ['需要安装Hammerspoon', '依赖外部工具'],
                'requirements': ['需要安装Hammerspoon应用'],
                'recommended': True
            },
            'python': {
                'name': 'Python原生方案',
                'description': '基于pynput和Quartz的Python实现',
                'pros': ['无需外部依赖', '完全控制', '快速开发'],
                'cons': ['稳定性一般', 'CPU占用较高', '权限敏感'],
                'requirements': ['macOS辅助功能权限'],
                'recommended': False
            }
        }
        
        return scheme_info.get(scheme, {
            'name': '未知方案',
            'description': '未知的热键方案',
            'pros': [],
            'cons': [],
            'requirements': [],
            'recommended': False
        })