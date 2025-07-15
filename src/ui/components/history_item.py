# 历史记录项组件 - 单个历史记录的显示容器
# 包含文本内容、布局和样式管理

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidgetItem
from PyQt6.QtCore import Qt, QSize
from .text_label import TextLabel
from ..simple_style_config import style_config

class HistoryItemWidget(QWidget):
    """历史记录项的自定义Widget
    
    每个历史记录项的容器，包含：
    - 文本内容显示
    - 统一的内边距
    - 底部分隔线样式
    """
    
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.original_text = text
        self._setup_layout()
        self._create_text_label(text)
        self._setup_styles()
    
    def _setup_layout(self):
        """设置布局"""
        layout = QVBoxLayout(self)
        # 从配置获取内边距
        margins = style_config.get_history_item_margins()
        layout.setContentsMargins(
            margins.get('left', 6),
            margins.get('top', 8), 
            margins.get('right', 6),
            margins.get('bottom', 8)
        )
        layout.setSpacing(0)
        self.setLayout(layout)
    
    def _create_text_label(self, text):
        """创建文本标签"""
        self.text_label = TextLabel(text, self)
        self.layout().addWidget(self.text_label, 0, Qt.AlignmentFlag.AlignVCenter)
    
    def _setup_styles(self):
        """设置样式"""
        background_color = style_config.get_color('background')
        separator_color = style_config.get_color('separator')
        
        self.setStyleSheet(f"""
            HistoryItemWidget {{
                background-color: {background_color};
            }}
            HistoryItemWidget::after {{
                content: '';
                position: absolute;
                left: 5px;
                right: 5px;
                bottom: 0;
                height: 1px;
                background-color: {separator_color};
            }}
        """)
    
    def refresh_styles(self):
        """刷新样式和布局"""
        # 重新设置边距
        margins = style_config.get_history_item_margins()
        self.layout().setContentsMargins(
            margins.get('left', 6),
            margins.get('top', 8), 
            margins.get('right', 6),
            margins.get('bottom', 8)
        )
        
        # 重新设置样式
        self._setup_styles()
        
        # 刷新文本标签样式
        if hasattr(self, 'text_label'):
            self.text_label.refresh_styles()
        
        # 更新几何信息
        self.updateGeometry()
    
    def getText(self):
        """获取原始HTML文本内容"""
        return self.original_text
    
    def setText(self, text):
        """设置文本内容并更新显示"""
        self.original_text = text
        self.text_label.setText(text)
        self.text_label.updateGeometry()
        self.updateGeometry()
    
    def sizeHint(self):
        """返回widget的建议大小"""
        text_size = self.text_label.sizeHint()
        margins = self.layout().contentsMargins()
        total_height = text_size.height() + margins.top() + margins.bottom()
        
        # 从配置获取最小高度
        min_height = style_config.get_layout('min_item_height')
        final_height = max(total_height, min_height)
        
        return QSize(text_size.width(), final_height)

class HistoryItem(QListWidgetItem):
    """历史记录列表项数据模型
    
    用于存储历史记录的数据，包含：
    - 文本内容
    - 时间戳信息
    """
    
    def __init__(self, text, timestamp=None):
        super().__init__()
        self.text = text
        self.timestamp = timestamp
        self.setSizeHint(QSize(0, 0))  # 初始大小，会被自动调整
    
    def getText(self):
        """获取文本内容"""
        return self.text
    
    def getTimestamp(self):
        """获取时间戳"""
        return self.timestamp