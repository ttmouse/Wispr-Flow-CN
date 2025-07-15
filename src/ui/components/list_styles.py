# 列表样式管理器 - 统一管理列表组件的样式
# 包含主题、颜色、字体等样式定义

from ..simple_style_config import style_config

class ListStyleManager:
    """列表样式管理器
    
    统一管理列表组件的样式，包括：
    - 主列表样式
    - 滚动条样式
    - 悬停和选中效果
    - 字体和颜色配置
    """
    
    @classmethod
    def _get_color(cls, key: str) -> str:
        """获取颜色配置"""
        return style_config.get_color(key)
    
    @classmethod
    def _get_size(cls, key: str) -> int:
        """获取尺寸配置"""
        if key == 'font_size':
            return style_config.get_font_size()
        elif key == 'padding':
            return int(style_config.get_spacing('list_item_padding'))
        elif key == 'spacing':
            return int(style_config.get_spacing('list_spacing'))
        elif key == 'scrollbar_width':
            return style_config.get_layout('scrollbar_width')
        elif key == 'scrollbar_radius':
            return style_config.get_layout('scrollbar_radius')
        elif key == 'min_handle_height':
            return style_config.get_layout('min_handle_height')
        return 0
    
    @classmethod
    def get_list_widget_style(cls):
        """获取主列表组件样式"""
        return f"""
            QListWidget {{
                background-color: {cls._get_color('background')};
                border: none;
                padding: 1px;
            }}
            QListWidget::item {{
                color: {cls._get_color('text')};
                background-color: {cls._get_color('background')};
                padding: {cls._get_size('padding')}px;
                border-bottom: 1px solid {cls._get_color('border')};
            }}
            QListWidget::item:hover {{
                background-color: {cls._get_color('hover')};
            }}
            QListWidget::item:selected {{
                background-color: {cls._get_color('selected')};
                color: {cls._get_color('text')};
            }}
            {cls._get_scrollbar_style()}
        """
    
    @classmethod
    def _get_scrollbar_style(cls):
        """获取滚动条样式"""
        return f"""
            QScrollBar:vertical {{
                background: transparent;
                width: {cls._get_size('scrollbar_width')}px;
                margin: 0px;
                border-radius: {cls._get_size('scrollbar_radius')}px;
            }}
            QScrollBar::handle:vertical {{
                background: {cls._get_color('scrollbar')};
                border-radius: {cls._get_size('scrollbar_radius')}px;
                min-height: {cls._get_size('min_handle_height')}px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {cls._get_color('scrollbar_hover')};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
        """
    
    @classmethod
    def get_font_config(cls):
        """获取字体配置"""
        from PyQt6.QtGui import QFont
        font = QFont(style_config.get_font_family())
        font.setPointSize(style_config.get_font_size())
        return font
    
    @classmethod
    def reload_config(cls):
        """重新加载配置"""
        style_config.load_config()