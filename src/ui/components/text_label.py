# 文本标签组件 - 专门处理文本显示和样式
# 支持HTML格式、自动换行和字体渲染优化

from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont
import re
from ..style_config_manager import style_config

class TextLabel(QLabel):
    """自定义文本标签组件
    
    特点：
    - 支持自动换行
    - 使用系统默认字体
    - 统一的文本样式和间距
    - 支持HTML富文本格式
    """
    
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._setup_font()
        self._setup_styles()
        self.setText(text)
    
    def _setup_ui(self):
        """设置UI基本属性"""
        self.setWordWrap(True)
        self.setTextFormat(Qt.TextFormat.PlainText)  # 使用纯文本格式
        self.setOpenExternalLinks(False)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        # 设置渲染属性
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_MacShowFocusRect, False)
    
    def _setup_font(self):
        """设置字体和渲染策略"""
        font = QFont(style_config.get_font_family(), style_config.get_font_size())
        font.setStyleStrategy(
            QFont.StyleStrategy.PreferAntialias |
            QFont.StyleStrategy.PreferQuality |
            QFont.StyleStrategy.PreferOutline
        )
        font.setHintingPreference(QFont.HintingPreference.PreferDefaultHinting)
        
        # 根据配置设置字体粗细
        weight_map = {
            'normal': QFont.Weight.Normal,
            'bold': QFont.Weight.Bold,
            'light': QFont.Weight.Light
        }
        font.setWeight(weight_map.get(style_config.get_font_weight(), QFont.Weight.Normal))
        self.setFont(font)
    
    def _setup_styles(self):
        """设置样式表"""
        text_color = style_config.get_color('text')
        text_padding = int(style_config.get_spacing('text_padding'))
        text_margin = int(style_config.get_spacing('text_margin'))
        line_height = style_config.get_spacing('line_height')
        font_weight = style_config.get_font_weight()
        
        self.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                padding: {text_padding}px;
                margin: {text_margin}px;
                line-height: {line_height};
                font-weight: {font_weight};
            }}
        """)
    
    def setText(self, text):
        """设置文本内容"""
        # 清理HTML标签，保留纯文本
        clean_text = self._clean_html_tags(text)
        super().setText(clean_text)
        self.updateGeometry()
    
    def _clean_html_tags(self, text):
        """清理HTML标签，保留纯文本内容"""
        if not text:
            return ""
        
        # 移除HTML标签
        clean_text = re.sub(r'<[^>]+>', '', text)
        
        # 处理HTML实体
        clean_text = clean_text.replace('&lt;', '<')
        clean_text = clean_text.replace('&gt;', '>')
        clean_text = clean_text.replace('&amp;', '&')
        clean_text = clean_text.replace('&quot;', '"')
        clean_text = clean_text.replace('&#39;', "'")
        
        return clean_text.strip()
    
    def sizeHint(self):
        """计算文本标签的建议大小"""
        try:
            font_metrics = self.fontMetrics()
            text_content = self.text()
            
            if not text_content.strip():
                return self._get_minimum_size(font_metrics)
            
            available_width = self._calculate_available_width()
            return self._calculate_text_size(font_metrics, text_content, available_width)
        except Exception as e:
            print(f"❌ 计算文本大小失败: {e}")
            import traceback
            print(traceback.format_exc())
            # 返回一个安全的默认大小
            from PyQt6.QtCore import QSize
            return QSize(300, 30)
    
    def _get_plain_text(self):
        """获取去除HTML标签的纯文本"""
        return re.sub(r'<[^>]+>', '', self.text())
    
    def _get_minimum_size(self, font_metrics):
        """获取最小尺寸"""
        line_height = font_metrics.height()
        min_height = int(line_height * 1.4) + 4
        return QSize(300, min_height)
    
    def _calculate_available_width(self):
        """计算可用宽度"""
        # 查找最顶层的列表组件
        list_widget = self._find_list_widget()
        text_width_margin = style_config.get_layout('text_width_margin')
        min_text_width = style_config.get_layout('min_text_width')
        
        if list_widget and list_widget.width() > 0:
            # 直接使用列表组件的宽度，减去滚动条和边距
            available_width = list_widget.width() - text_width_margin
        else:
            # 回退到父容器宽度计算
            parent_widget = self.parent()
            if not parent_widget:
                return min_text_width
            
            if hasattr(parent_widget, 'layout') and parent_widget.layout():
                layout = parent_widget.layout()
                margins = layout.contentsMargins()
                available_width = parent_widget.width() - margins.left() - margins.right()
            else:
                available_width = parent_widget.width() if parent_widget.width() > 0 else min_text_width
        
        return max(available_width, min_text_width)  # 确保最小宽度
    
    def _find_list_widget(self):
        """查找最顶层的QListWidget"""
        from PyQt6.QtWidgets import QListWidget
        widget = self.parent()
        while widget and not isinstance(widget, QListWidget):
            widget = widget.parent()
        return widget
    
    def _calculate_text_size(self, font_metrics, text_content, available_width):
        """计算文本实际需要的尺寸"""
        # 使用更精确的文本边界计算
        text_rect = font_metrics.boundingRect(
            0, 0, available_width - 10, 0,  # 减去一些边距确保换行
            Qt.TextFlag.TextWordWrap | Qt.TextFlag.TextWrapAnywhere,
            text_content
        )
        
        # 计算实际高度，考虑换行
        line_height = font_metrics.height()
        line_spacing_multiplier = style_config.get_spacing('line_spacing_multiplier')
        line_spacing = int(line_height * line_spacing_multiplier)
        
        # 更准确的行数计算
        if text_rect.height() > 0:
            estimated_lines = max(1, (text_rect.height() + line_height - 1) // line_height)
        else:
            estimated_lines = 1
        
        # 处理显式换行符
        if '\n' in text_content:
            actual_lines = text_content.count('\n') + 1
            estimated_lines = max(estimated_lines, actual_lines)
        
        # 计算最终高度
        calculated_height = estimated_lines * line_spacing + 12  # 增加一些内边距
        min_height = line_spacing + 12
        final_height = max(calculated_height, min_height)
        
        return QSize(available_width, final_height)
    
    def refresh_styles(self):
        """刷新样式和字体"""
        self._setup_font()
        self._setup_styles()
        self.updateGeometry()