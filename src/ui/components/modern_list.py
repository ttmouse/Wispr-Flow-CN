from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QLabel, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont
import time

class TextLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setWordWrap(True)
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setFont(QFont("-apple-system", 14))
        self.setStyleSheet("""
            QLabel {
                color: #1D1D1F;
                padding: 0px;
                line-height: 140%;
            }
        """)

class HistoryItemWidget(QWidget):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(0)
        
        # 创建文本标签
        self.text_label = TextLabel(text, self)
        layout.addWidget(self.text_label)
        
        # 设置样式，添加底部分隔线
        self.setStyleSheet("""
            HistoryItemWidget {
                background-color: white;
            }
            HistoryItemWidget::after {
                content: '';
                position: absolute;
                left: 20px;
                right: 20px;
                bottom: 0;
                height: 1px;
                background-color: #E5E5E7;
            }
        """)

class HistoryItem(QListWidgetItem):
    def __init__(self, text, timestamp):
        super().__init__()
        self.text = text
        self.timestamp = timestamp
        self.setSizeHint(QSize(0, 0))  # 初始大小，会被自动调整

class ModernListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: white;
                outline: none;
            }
            QListWidget::item {
                padding: 0;
                margin: 0;
                background-color: transparent;
                border-bottom: 1px solid #E5E5E7;
            }
            QListWidget::item:hover {
                background-color: #F5F5F7;
            }
            QListWidget::item:selected {
                background-color: #F5F5F7;
            }
        """)
        
        # 基本设置
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.setSpacing(1)
        self.setMinimumWidth(300)
        
    def addHistoryItem(self, text, timestamp=None):
        """添加新的历史记录项"""
        # 创建列表项
        item = HistoryItem(text, timestamp or time.time())
        self.insertItem(0, item)
        
        # 创建自定义widget
        widget = HistoryItemWidget(text)
        item.setSizeHint(widget.sizeHint())
        self.setItemWidget(item, widget)
        
        # 滚动到顶部
        self.scrollToTop()
        
    def resizeEvent(self, event):
        """窗口大小改变时重新计算所有项的大小"""
        super().resizeEvent(event)
        for i in range(self.count()):
            item = self.item(i)
            if item and self.itemWidget(item):
                widget = self.itemWidget(item)
                item.setSizeHint(widget.sizeHint()) 