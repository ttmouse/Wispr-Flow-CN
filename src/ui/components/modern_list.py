# 自定义列表组件模块，用于显示语音识别历史记录
# 实现了现代化的UI设计，支持自动换行和滚动

from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QLabel, QWidget, QVBoxLayout, QStackedWidget
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
        
        # 创建字体并设置平滑渲染
        font = QFont("-apple-system", 14)
        # 设置字体渲染策略，组合多个策略以获得最佳效果
        font.setStyleStrategy(
            QFont.StyleStrategy.PreferAntialias |    # 优先使用抗锯齿
            QFont.StyleStrategy.PreferQuality |      # 优先质量渲染
            QFont.StyleStrategy.PreferOutline        # 优先使用轮廓渲染
        )
        font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)  # 禁用微调以获得更平滑的渲染
        font.setWeight(QFont.Weight.Thin)  # 设置字体粗细为最细
        self.setFont(font)
        
        # 设置样式
        self.setStyleSheet("""
            QLabel {
                color: #1D1D1F;  /* 深灰色文本 */
                padding: 0px;
                line-height: 150%;  /* 行高1.4倍，提高可读性 */
                font-weight: 100;  /* CSS样式设置为最细 */
            }
        """)
        
        # 启用文本平滑渲染
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # 允许半透明背景
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)     # 禁用系统背景
        self.setAttribute(Qt.WidgetAttribute.WA_MacShowFocusRect, False)  # 禁用焦点框
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)  # 禁用文本交互以避免影响渲染

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
        
        # 创建空状态提示
        self.empty_widget = None
    
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
        
    def setEmptyState(self, widget):
        """设置空状态显示的部件"""
        self.empty_widget = widget
        self.updateEmptyState()
        
    def updateEmptyState(self):
        """更新空状态显示"""
        if self.count() == 0 and self.empty_widget:
            # 如果列表为空且有空状态部件，显示空状态
            self.empty_widget.setParent(self.viewport())
            self.empty_widget.show()
            # 调整空状态部件的大小和位置
            self.empty_widget.setGeometry(self.viewport().rect())
        elif self.empty_widget:
            # 如果列表不为空，隐藏空状态
            self.empty_widget.hide()
            
    def resizeEvent(self, event):
        """处理窗口大小改变事件"""
        super().resizeEvent(event)
        # 调整所有项的大小
        for i in range(self.count()):
            item = self.item(i)
            if item and self.itemWidget(item):
                widget = self.itemWidget(item)
                item.setSizeHint(widget.sizeHint())
        # 更新空状态显示
        self.updateEmptyState()
        
    def addItem(self, item):
        """添加新的历史记录项到列表顶部"""
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
        self.updateEmptyState()  # 更新空状态显示
        
    def clear(self):
        """清空列表"""
        super().clear()
        self.updateEmptyState()  # 更新空状态显示 