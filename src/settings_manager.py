import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

class SettingsManager:
    # 默认设置
    DEFAULT_SETTINGS = {
        'hotkey': 'fn',              # 快捷键设置：fn, ctrl, alt
        'high_frequency_words': [],   # 高频词列表
        'audio': {
            'input_device': None,     # 输入设备名称，None表示系统默认
            'volume_threshold': 150,   # 音量阈值：0-1000，对应实际阈值0-0.02，默认值150对应0.003
            'max_recording_duration': 10,  # 最大录音时长（秒），默认10秒
        },
        'asr': {
            'model_path': '',          # ASR模型路径
            'punc_model_path': '',     # 标点符号模型路径
            'auto_punctuation': True,  # 自动添加标点
        },
        'cache': {
            'permissions': {
                'last_check': '',      # 上次权限检查时间
                'accessibility': False, # 辅助功能权限状态
                'microphone': False,   # 麦克风权限状态
                'check_interval_hours': 24,  # 检查间隔（小时）
            },
            'models': {
                'last_check': '',      # 上次模型检查时间
                'asr_available': False, # ASR模型可用状态
                'punc_available': False, # 标点模型可用状态
                'check_interval_hours': 168,  # 检查间隔（小时，7天）
            }
        }
    }

    def __init__(self):
        self.settings = {}
        self.settings_file = 'settings.json'
        self.logger = logging.getLogger('SettingsManager')
        self.load_settings()

    def load_settings(self) -> None:
        """加载设置"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    # 合并加载的设置和默认设置
                    self.settings = self._merge_settings(self.DEFAULT_SETTINGS, loaded_settings)
            else:
                self.settings = self.DEFAULT_SETTINGS.copy()
                self.save_settings()  # 保存默认设置
        except Exception as e:
            self.logger.error(f"加载设置失败: {e}")
            self.settings = self.DEFAULT_SETTINGS.copy()

    def save_settings(self) -> bool:
        """保存设置"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"保存设置失败: {e}")
            return False

    def get_setting(self, key: str, default: Any = None) -> Any:
        """获取设置值"""
        try:
            # 支持使用点号访问嵌套设置，如 'audio.volume_threshold'
            keys = key.split('.')
            value = self.settings
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set_setting(self, key: str, value: Any) -> bool:
        """设置值"""
        try:
            # 支持使用点号设置嵌套设置
            keys = key.split('.')
            target = self.settings
            for k in keys[:-1]:
                target = target[k]
            target[keys[-1]] = value
            return self.save_settings()
        except Exception as e:
            self.logger.error(f"设置值失败 {key}: {e}")
            return False

    def get_hotkey(self) -> str:
        """获取当前快捷键设置"""
        return self.get_setting('hotkey', 'fn')

    def set_hotkey(self, hotkey: str) -> bool:
        """设置快捷键"""
        return self.set_setting('hotkey', hotkey)

    def get_high_frequency_words(self) -> List[str]:
        """获取高频词列表"""
        return self.get_setting('high_frequency_words', [])

    def set_high_frequency_words(self, words: List[str]) -> bool:
        """设置高频词列表"""
        return self.set_setting('high_frequency_words', words)

    def _merge_settings(self, default: Dict, loaded: Dict) -> Dict:
        """递归合并设置，确保所有默认键都存在"""
        result = default.copy()
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_settings(result[key], value)
            else:
                result[key] = value
        return result

    def reset_to_defaults(self) -> bool:
        """重置所有设置为默认值"""
        self.settings = self.DEFAULT_SETTINGS.copy()
        return self.save_settings()

    def get_all_settings(self) -> Dict:
        """获取所有设置"""
        return self.settings.copy()

    def get_model_paths(self):
        """获取模型路径设置"""
        return {
            'asr_model_path': self.get_setting('asr.model_path', ''),
            'punc_model_path': self.get_setting('asr.punc_model_path', '')
        }

    def update_model_paths(self, paths):
        """更新模型路径设置"""
        success = True
        if 'asr_model_path' in paths:
            success &= self.set_setting('asr.model_path', paths['asr_model_path'])
        if 'punc_model_path' in paths:
            success &= self.set_setting('asr.punc_model_path', paths['punc_model_path'])
        return success

    def is_cache_expired(self, cache_type: str) -> bool:
        """检查缓存是否过期
        
        Args:
            cache_type: 缓存类型，'permissions' 或 'models'
        
        Returns:
            bool: True表示缓存已过期或不存在，需要重新检查
        """
        try:
            last_check = self.get_setting(f'cache.{cache_type}.last_check', '')
            if not last_check:
                return True
            
            interval_hours = self.get_setting(f'cache.{cache_type}.check_interval_hours', 24)
            last_check_time = datetime.fromisoformat(last_check)
            expiry_time = last_check_time + timedelta(hours=interval_hours)
            
            return datetime.now() > expiry_time
        except Exception as e:
            self.logger.error(f"检查缓存过期状态失败 {cache_type}: {e}")
            return True

    def update_permissions_cache(self, accessibility: bool, microphone: bool) -> bool:
        """更新权限缓存状态"""
        try:
            now = datetime.now().isoformat()
            success = True
            success &= self.set_setting('cache.permissions.last_check', now)
            success &= self.set_setting('cache.permissions.accessibility', accessibility)
            success &= self.set_setting('cache.permissions.microphone', microphone)
            return success
        except Exception as e:
            self.logger.error(f"更新权限缓存失败: {e}")
            return False

    def update_models_cache(self, asr_available: bool, punc_available: bool) -> bool:
        """更新模型缓存状态"""
        try:
            now = datetime.now().isoformat()
            success = True
            success &= self.set_setting('cache.models.last_check', now)
            success &= self.set_setting('cache.models.asr_available', asr_available)
            success &= self.set_setting('cache.models.punc_available', punc_available)
            return success
        except Exception as e:
            self.logger.error(f"更新模型缓存失败: {e}")
            return False

    def get_permissions_cache(self) -> Dict[str, bool]:
        """获取权限缓存状态"""
        return {
            'accessibility': self.get_setting('cache.permissions.accessibility', False),
            'microphone': self.get_setting('cache.permissions.microphone', False)
        }

    def get_models_cache(self) -> Dict[str, bool]:
        """获取模型缓存状态"""
        return {
            'asr_available': self.get_setting('cache.models.asr_available', False),
            'punc_available': self.get_setting('cache.models.punc_available', False)
        }