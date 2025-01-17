import json
import os
import logging
from typing import Dict, Any, List

class SettingsManager:
    # 默认设置
    DEFAULT_SETTINGS = {
        'hotkey': 'fn',              # 快捷键设置：fn, ctrl, alt
        'high_frequency_words': [],   # 高频词列表
        'audio': {
            'input_device': None,     # 输入设备名称，None表示系统默认
            'volume_threshold': 150,   # 音量阈值：0-1000，对应实际阈值0-0.02，默认值150对应0.003
        },
        'asr': {
            'model_path': '',          # ASR模型路径
            'punc_model_path': '',     # 标点符号模型路径
            'auto_punctuation': True,  # 自动添加标点
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