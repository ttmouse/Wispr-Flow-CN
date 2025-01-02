# 自定义列表组件模块，用于显示语音识别历史记录
# 实现了现代化的UI设计，支持自动换行和滚动

from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QLabel, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont
import time
from PyQt6.QtCore import QTimer

class TextLabel(QLabel):
    """自定义文本标签组件
    
    特点：
    - 支持自动换行
    - 使用系统默认字体
    - 统一的文本样式和间距
    """
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setWordWrap(True)  # 启用自动换行
        self.setTextFormat(Qt.TextFormat.PlainText)  # 使用纯文本格式，避免HTML注入
        self.setFont(QFont("-apple-system", 14))  # 使用系统字体，大小14pt
        self.setStyleSheet("""
            QLabel {
                color: #1D1D1F;  /* 深灰色文本 */
                padding: 0px;
                line-height: 140%;  /* 行高1.4倍，提高可读性 */
            }
        """)

class HistoryItemWidget(QWidget):
    """历史记录项的自定义Widget
    
    每个历史记录项的容器，包含：
    - 文本内容
    - 统一的内边距
    - 底部分隔线
    """
    def __init__(self, text, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)  # 设置四周内边距
        layout.setSpacing(0)  # 移除内部间距
        
        # 创建文本标签
        self.text_label = TextLabel(text, self)
        layout.addWidget(self.text_label)
        
        # 设置样式，添加底部分隔线
        self.setStyleSheet("""
            HistoryItemWidget {
                background-color: white;
            }
            HistoryItemWidget::after {  /* 使用伪元素添加分隔线 */
                content: '';
                position: absolute;
                left: 20px;
                right: 20px;
                bottom: 0;
                height: 1px;
                background-color: #E5E5E7;
            }
        """)
    
    def getText(self):
        """获取文本内容"""
        return self.text_label.text()

class HistoryItem(QListWidgetItem):
    """历史记录列表项
    
    用于存储历史记录的数据模型，包含：
    - 文本内容
    - 时间戳
    """
    def __init__(self, text, timestamp):
        super().__init__()
        self.text = text
        self.timestamp = timestamp
        self.setSizeHint(QSize(0, 0))  # 初始大小，会被自动调整
    
    def getText(self):
        """获取文本内容"""
        return self.text

class ModernListWidget(QListWidget):
    """现代化列表组件
    
    用于显示语音识别历史记录的主列表组件，特点：
    - 现代化的UI设计
    - 支持自动换行
    - 鼠标悬停效果
    - 平滑滚动
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # 设置基本样式
        self.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: none;
                padding: 1px;
            }
            QListWidget::item {
                color: black;
                background-color: white;
                padding: 10px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;  /* 鼠标悬停时的背景色 */
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;  /* 选中时的背景色 */
                color: black;
            }
        """)
        
        # 配置滚动条
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWordWrap(True)  # 启用自动换行
        self.setSpacing(0)  # 历史记录项之间的间距
        
        # 设置字体
        font = QFont()
        font.setPointSize(14)  # 设置字体大小
        self.setFont(font)
    
    def mousePressEvent(self, event):
        """处理鼠标点击事件"""
        super().mousePressEvent(event)
        # 获取点击位置的项
        item = self.itemAt(event.pos())
        if item:
            # 发送点击信号后清除选中状态
            QTimer.singleShot(100, self.clearSelection)
    
    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件"""
        super().mouseReleaseEvent(event)
        # 延迟清除选中状态，确保点击事件已经处理完成
        QTimer.singleShot(100, self.clearSelection)
    
    def addItem(self, item):
        """添加新的历史记录项到列表顶部
        
        Args:
            item: 可以是字符串或 QListWidgetItem 实例
        """
        if isinstance(item, str):
            # 如果是字符串，创建自定义widget
            list_item = QListWidgetItem()
            self.insertItem(0, list_item)  # 在顶部插入
            
            widget = HistoryItemWidget(item)
            list_item.setSizeHint(widget.sizeHint())
            self.setItemWidget(list_item, widget)
        else:
            self.insertItem(0, item)  # 在顶部插入
        
        self.scrollToTop()  # 滚动到顶部显示最新项
    
    def addHistoryItem(self, text, timestamp=None):
        """添加新的历史记录项到列表顶部
        
        Args:
            text: 要显示的文本内容
            timestamp: 可选的时间戳
        """
        item = QListWidgetItem()
        self.insertItem(0, item)  # 在顶部插入
        
        widget = HistoryItemWidget(text)
        item.setSizeHint(widget.sizeHint())
        self.setItemWidget(item, widget)
        
        self.scrollToTop()  # 滚动到顶部显示最新项
    
    def getItemText(self, item):
        """获取列表项的文本内容
        
        Args:
            item: QListWidgetItem 实例
        
        Returns:
            str: 文本内容，如果项不存在则返回空字符串
        """
        if item and self.itemWidget(item):
            return self.itemWidget(item).getText()
        return ""
    
    def resizeEvent(self, event):
        """处理窗口大小改变事件
        
        当窗口大小改变时，重新计算所有项的大小，
        确保文本正确换行和显示
        """
        super().resizeEvent(event)
        for i in range(self.count()):
            item = self.item(i)
            if item and self.itemWidget(item):
                widget = self.itemWidget(item)
                item.setSizeHint(widget.sizeHint()) 