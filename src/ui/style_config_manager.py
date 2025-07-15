# 样式配置管理器 - 从配置文件加载和管理UI样式
# 支持动态更新样式配置

import json
import os
from typing import Dict, Any

class StyleConfigManager:
    """样式配置管理器
    
    负责：
    - 从JSON配置文件加载样式参数
    - 提供样式参数的访问接口
    - 支持运行时更新配置
    - 提供默认配置作为备用
    """
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self.load_config()
    
    def load_config(self, config_path: str = None):
        """加载样式配置文件"""
        if config_path is None:
            # 默认配置文件路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, 'styles_config.json')
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"加载样式配置失败: {e}，使用默认配置")
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "colors": {
                "background": "white",
                "text": "#1D1D1F",
                "border": "#eee",
                "hover": "#f5f5f5",
                "selected": "#e3f2fd",
                "scrollbar": "#C0C0C0",
                "scrollbar_hover": "#A0A0A0",
                "separator": "#E5E5E7"
            },
            "fonts": {
                "family": "PingFang SC",
                "size": 14,
                "weight": "normal"
            },
            "spacing": {
                "list_item_padding": 5,
                "list_spacing": 0,
                "text_padding": 1,
                "text_margin": 0,
                "line_height": 1.4,
                "line_spacing_multiplier": 1.3
            },
            "layout": {
                "history_item_margins": {
                    "left": 6,
                    "top": 8,
                    "right": 6,
                    "bottom": 8
                },
                "min_item_height": 35,
                "min_text_width": 250,
                "scrollbar_width": 8,
                "scrollbar_radius": 4,
                "min_handle_height": 20,
                "text_width_margin": 30
            }
        }
    
    def get_color(self, key: str) -> str:
        """获取颜色配置"""
        return self._config.get('colors', {}).get(key, '#000000')
    
    def get_font_family(self) -> str:
        """获取字体族"""
        return self._config.get('fonts', {}).get('family', 'PingFang SC')
    
    def get_font_size(self) -> int:
        """获取字体大小"""
        return self._config.get('fonts', {}).get('size', 14)
    
    def get_font_weight(self) -> str:
        """获取字体粗细"""
        return self._config.get('fonts', {}).get('weight', 'normal')
    
    def get_spacing(self, key: str) -> float:
        """获取间距配置"""
        return self._config.get('spacing', {}).get(key, 0)
    
    def get_layout(self, key: str) -> Any:
        """获取布局配置"""
        return self._config.get('layout', {}).get(key, {})
    
    def get_history_item_margins(self) -> Dict[str, int]:
        """获取历史项边距配置"""
        return self.get_layout('history_item_margins')
    
    def update_config(self, new_config: Dict[str, Any]):
        """更新配置"""
        if self._config is None:
            self._config = {}
        
        # 深度合并配置
        self._deep_update(self._config, new_config)
    
    def _deep_update(self, base_dict: Dict, update_dict: Dict):
        """深度更新字典"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def save_config(self, config_path: str = None):
        """保存配置到文件"""
        if config_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, 'styles_config.json')
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存样式配置失败: {e}")
    
    def get_all_config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self._config.copy() if self._config else {}

# 全局样式配置实例
style_config = StyleConfigManager()