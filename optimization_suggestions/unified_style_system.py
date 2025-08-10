#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一样式管理系统
解决重复样式代码问题
"""

from typing import Dict, Any, Optional
from enum import Enum
import json
import os

class ThemeType(Enum):
    """主题类型"""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"

class StyleManager:
    """统一样式管理器"""
    
    _instance = None
    _themes = {}
    _current_theme = ThemeType.DARK
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._load_themes()
            self._initialized = True
    
    def _load_themes(self):
        """加载主题配置"""
        self._themes = {
            ThemeType.DARK: {
                'colors': {
                    'primary': '#007AFF',
                    'background': '#2d2d2d',
                    'surface': '#1e1e1e',
                    'text_primary': '#ffffff',
                    'text_secondary': '#e0e0e0',
                    'text_disabled': '#999999',
                    'border': '#3d3d3d',
                    'hover': '#3d3d3d',
                    'selected': '#007AFF',
                    'error': '#FF3B30',
                    'success': '#4CAF50',
                    'warning': '#FF9500'
                },
                'fonts': {
                    'family': '"SF Pro Display", BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                    'size_small': 12,
                    'size_normal': 14,
                    'size_large': 16,
                    'size_title': 18,
                    'weight_normal': 400,
                    'weight_medium': 500,
                    'weight_bold': 600
                },
                'spacing': {
                    'xs': 4,
                    'sm': 8,
                    'md': 12,
                    'lg': 16,
                    'xl': 20,
                    'xxl': 24
                },
                'radius': {
                    'small': 3,
                    'medium': 8,
                    'large': 12
                }
            },
            ThemeType.LIGHT: {
                'colors': {
                    'primary': '#007AFF',
                    'background': '#ffffff',
                    'surface': '#f5f5f5',
                    'text_primary': '#1D1D1F',
                    'text_secondary': '#666666',
                    'text_disabled': '#999999',
                    'border': '#eee',
                    'hover': '#f5f5f5',
                    'selected': '#e3f2fd',
                    'error': '#FF3B30',
                    'success': '#4CAF50',
                    'warning': '#FF9500'
                },
                'fonts': {
                    'family': '"SF Pro Display", BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                    'size_small': 12,
                    'size_normal': 14,
                    'size_large': 16,
                    'size_title': 18,
                    'weight_normal': 400,
                    'weight_medium': 500,
                    'weight_bold': 600
                },
                'spacing': {
                    'xs': 4,
                    'sm': 8,
                    'md': 12,
                    'lg': 16,
                    'xl': 20,
                    'xxl': 24
                },
                'radius': {
                    'small': 3,
                    'medium': 8,
                    'large': 12
                }
            }
        }
    
    def get_color(self, key: str) -> str:
        """获取颜色值"""
        return self._themes[self._current_theme]['colors'].get(key, '#000000')
    
    def get_font_family(self) -> str:
        """获取字体族"""
        return self._themes[self._current_theme]['fonts']['family']
    
    def get_font_size(self, size_key: str = 'size_normal') -> int:
        """获取字体大小"""
        return self._themes[self._current_theme]['fonts'].get(size_key, 14)
    
    def get_spacing(self, size_key: str) -> int:
        """获取间距值"""
        return self._themes[self._current_theme]['spacing'].get(size_key, 8)
    
    def get_radius(self, size_key: str) -> int:
        """获取圆角值"""
        return self._themes[self._current_theme]['radius'].get(size_key, 8)
    
    def set_theme(self, theme: ThemeType):
        """设置主题"""
        self._current_theme = theme

class ComponentStyleBuilder:
    """组件样式构建器"""
    
    def __init__(self):
        self.style_manager = StyleManager()
        self._styles = []
    
    def add_background(self, color_key: str = 'background') -> 'ComponentStyleBuilder':
        """添加背景色"""
        color = self.style_manager.get_color(color_key)
        self._styles.append(f"background-color: {color};")
        return self
    
    def add_text_color(self, color_key: str = 'text_primary') -> 'ComponentStyleBuilder':
        """添加文字颜色"""
        color = self.style_manager.get_color(color_key)
        self._styles.append(f"color: {color};")
        return self
    
    def add_font(self, size_key: str = 'size_normal', weight_key: str = 'weight_normal') -> 'ComponentStyleBuilder':
        """添加字体设置"""
        family = self.style_manager.get_font_family()
        size = self.style_manager.get_font_size(size_key)
        weight = self.style_manager._themes[self.style_manager._current_theme]['fonts'].get(weight_key, 400)
        
        self._styles.extend([
            f"font-family: {family};",
            f"font-size: {size}px;",
            f"font-weight: {weight};"
        ])
        return self
    
    def add_padding(self, size_key: str = 'md') -> 'ComponentStyleBuilder':
        """添加内边距"""
        padding = self.style_manager.get_spacing(size_key)
        self._styles.append(f"padding: {padding}px;")
        return self
    
    def add_margin(self, size_key: str = 'md') -> 'ComponentStyleBuilder':
        """添加外边距"""
        margin = self.style_manager.get_spacing(size_key)
        self._styles.append(f"margin: {margin}px;")
        return self
    
    def add_border(self, color_key: str = 'border', width: int = 1) -> 'ComponentStyleBuilder':
        """添加边框"""
        color = self.style_manager.get_color(color_key)
        self._styles.append(f"border: {width}px solid {color};")
        return self
    
    def add_border_radius(self, size_key: str = 'medium') -> 'ComponentStyleBuilder':
        """添加圆角"""
        radius = self.style_manager.get_radius(size_key)
        self._styles.append(f"border-radius: {radius}px;")
        return self
    
    def add_hover_effect(self, color_key: str = 'hover') -> 'ComponentStyleBuilder':
        """添加悬停效果"""
        color = self.style_manager.get_color(color_key)
        hover_style = f"""
        :hover {{
            background-color: {color};
        }}
        """
        self._styles.append(hover_style)
        return self
    
    def add_custom(self, css: str) -> 'ComponentStyleBuilder':
        """添加自定义CSS"""
        self._styles.append(css)
        return self
    
    def build(self, selector: str = "") -> str:
        """构建最终样式"""
        if selector:
            return f"{selector} {{ {' '.join(self._styles)} }}"
        else:
            return ' '.join(self._styles)

# 预定义的常用样式
class CommonStyles:
    """常用样式集合"""
    
    @staticmethod
    def get_main_window_style() -> str:
        """获取主窗口样式"""
        return (ComponentStyleBuilder()
                .add_background('background')
                .build('QMainWindow'))
    
    @staticmethod
    def get_title_bar_style() -> str:
        """获取标题栏样式"""
        return (ComponentStyleBuilder()
                .add_background('surface')
                .add_padding('md')
                .build('QWidget'))
    
    @staticmethod
    def get_button_style() -> str:
        """获取按钮样式"""
        builder = ComponentStyleBuilder()
        normal_style = (builder
                       .add_background('primary')
                       .add_text_color('text_primary')
                       .add_font('size_normal', 'weight_medium')
                       .add_padding('md')
                       .add_border_radius('medium')
                       .build('QPushButton'))
        
        hover_style = (ComponentStyleBuilder()
                      .add_background('primary')
                      .add_custom('opacity: 0.8;')
                      .build('QPushButton:hover'))
        
        return f"{normal_style} {hover_style}"
    
    @staticmethod
    def get_list_widget_style() -> str:
        """获取列表组件样式"""
        main_style = (ComponentStyleBuilder()
                     .add_background('background')
                     .add_custom('border: none; padding: 1px;')
                     .build('QListWidget'))
        
        item_style = (ComponentStyleBuilder()
                     .add_text_color('text_primary')
                     .add_background('background')
                     .add_padding('sm')
                     .add_custom('border-bottom: 1px solid')
                     .build('QListWidget::item'))
        
        hover_style = (ComponentStyleBuilder()
                      .add_background('hover')
                      .build('QListWidget::item:hover'))
        
        selected_style = (ComponentStyleBuilder()
                         .add_background('selected')
                         .add_text_color('text_primary')
                         .build('QListWidget::item:selected'))
        
        return f"{main_style} {item_style} {hover_style} {selected_style}"

# 使用示例
def apply_styles_to_component(component, style_func):
    """应用样式到组件"""
    style = style_func()
    component.setStyleSheet(style)

# 在组件中的使用方式：
# apply_styles_to_component(self.main_window, CommonStyles.get_main_window_style)
# apply_styles_to_component(self.list_widget, CommonStyles.get_list_widget_style)
