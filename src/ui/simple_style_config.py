# 简化的样式配置类
# 提供基本的样式配置功能，不依赖复杂的配置管理器

import json
import os

class SimpleStyleConfig:
    """简化的样式配置类"""
    
    def __init__(self):
        self._config = self._load_default_config()
        self._load_config_file()
    
    def _load_default_config(self):
        """加载默认配置"""
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
                "list_item_padding": 6,
                "list_spacing": 0,
                "text_padding": 0,
                "text_margin": 0,
                "line_height": 1.4,
                "line_spacing_multiplier": 1.2
            },
            "layout": {
                "history_item_margins": {
                    "left": 6,
                    "top": 2,
                    "right": 6,
                    "bottom": 2
                },
                "min_item_height": 36,
                "min_text_width": 251,
                "scrollbar_width": 3,
                "scrollbar_radius": 1,
                "min_handle_height": 20,
                "text_width_margin": 32
            }
        }
    
    def _load_config_file(self):
        """从配置文件加载配置"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'styles_config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    self._merge_config(file_config)
        except Exception as e:
            import logging
            logging.error(f"加载样式配置文件失败: {e}")
    
    def _merge_config(self, file_config):
        """合并配置"""
        for section, values in file_config.items():
            if section in self._config:
                if isinstance(values, dict):
                    self._config[section].update(values)
                else:
                    self._config[section] = values
    
    def get_color(self, key):
        """获取颜色配置"""
        return self._config.get('colors', {}).get(key, '#000000')
    
    def get_font_family(self):
        """获取字体族"""
        return self._config.get('fonts', {}).get('family', 'PingFang SC')
    
    def get_font_size(self):
        """获取字体大小"""
        return self._config.get('fonts', {}).get('size', 14)
    
    def get_font_weight(self):
        """获取字体粗细"""
        return self._config.get('fonts', {}).get('weight', 'normal')
    
    def get_spacing(self, key):
        """获取间距配置"""
        return self._config.get('spacing', {}).get(key, 0)
    
    def get_layout(self, key):
        """获取布局配置"""
        return self._config.get('layout', {}).get(key, {})
    
    def get_history_item_margins(self):
        """获取历史项边距配置"""
        return self._config.get('layout', {}).get('history_item_margins', {
            'left': 6,
            'top': 2,
            'right': 6,
            'bottom': 2
        })

# 创建全局实例
style_config = SimpleStyleConfig()