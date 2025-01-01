from PyQt6.QtWidgets import QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QFontMetrics
import time

class HistoryItem(QListWidgetItem):
    def __init__(self, text, timestamp):
        super().__init__()
        self.text = text
        self.timestamp = timestamp  # 保留timestamp属性，但不显示
        self.update_display()
        
    def update_display(self):
        self.setText(self.text)
        # 动态计算合适的大小
        font = QFont("", 14)
        metrics = QFontMetrics(font)
        width = 400 - 32  # 假设最小宽度400，减去padding
        rect = metrics.boundingRect(0, 0, width, 2000, Qt.TextFlag.TextWordWrap, self.text)
        height = max(60, rect.height() + 24)  # 最小高度60，加上padding
        self.setSizeHint(QSize(width, height))

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
                border-bottom: 1px solid #E5E5E7;
                padding: 12px 16px;
                margin: 0;
                color: #1D1D1F;
                font-size: 14px;
            }
            QListWidget::item:hover {
                background-color: #F5F5F7;
            }
            QListWidget::item:selected {
                background-color: #F5F5F7;
                color: #1D1D1F;
            }
        """)
        # 启用自动换行
        self.setWordWrap(True)
        # 设置动态高度
        self.setTextElideMode(Qt.TextElideMode.ElideNone)
        # 设置自动调整大小
        self.setSizeAdjustPolicy(QListWidget.SizeAdjustPolicy.AdjustToContents)
        
    def sizeHintForRow(self, row) -> int:
        """返回每行的建议高度"""
        item = self.item(row)
        if not item:
            return 0
            
        # 获取文本内容
        text = item.text()
        font = self.font()
        metrics = QFontMetrics(font)
        
        # 计算文本宽度和换行
        available_width = self.viewport().width() - 32  # 减去左右padding
        text_rect = metrics.boundingRect(
            0, 0, available_width, 1000,
            Qt.TextFlag.TextWordWrap,
            text
        )
        
        # 返回文本高度加上padding
        return max(60, text_rect.height() + 24)  # 最小高度60，加上padding 