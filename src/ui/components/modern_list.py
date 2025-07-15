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
        super().__init__(parent)  # 不传递text参数，避免HTML转义
        self.setWordWrap(True)  # 启用自动换行
        self.setTextFormat(Qt.TextFormat.RichText)  # 使用富文本格式，支持HTML热词高亮
        self.setText(text)  # 在设置格式后再设置文本
        
        # 创建字体并设置平滑渲染
        font = QFont("PingFang SC", 14)
        # 设置字体渲染策略，组合多个策略以获得最佳效果
        font.setStyleStrategy(
            QFont.StyleStrategy.PreferAntialias |    # 优先使用抗锯齿
            QFont.StyleStrategy.PreferQuality |      # 优先质量渲染
            QFont.StyleStrategy.PreferOutline        # 优先使用轮廓渲染
        )
        font.setHintingPreference(QFont.HintingPreference.PreferDefaultHinting)  # 使用默认微调以获得更好的可读性
        font.setWeight(QFont.Weight.Normal)  # 设置字体粗细为正常
        self.setFont(font)
        
        # 设置样式，确保行高一致性和字体完整显示，减少内边距
        self.setStyleSheet("""
            QLabel {
                color: #1D1D1F;  /* 深灰色文本 */
                padding: 1px;  /* 减少内边距，实现更紧凑的布局 */
                margin: 0px;
                line-height: 1.4;  /* 适当调整行高，保持高度自适应 */
                font-weight: normal;  /* CSS样式设置为正常 */
            }
        """)
        
        # 启用富文本格式以支持HTML高亮
        self.setTextFormat(Qt.TextFormat.RichText)
        
        # 启用文本平滑渲染
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # 允许半透明背景
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)     # 禁用系统背景
        self.setAttribute(Qt.WidgetAttribute.WA_MacShowFocusRect, False)  # 禁用焦点框
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)  # 禁用文本交互以避免影响渲染
    
    def sizeHint(self):
        """返回文本标签的建议大小"""
        # 获取字体度量信息
        font_metrics = self.fontMetrics()
        
        # 获取文本内容（去除HTML标签进行计算）
        import re
        plain_text = self.text()
        # 去除所有HTML标签，包括热词高亮的<b>标签和其他可能的标签
        plain_text = re.sub(r'<[^>]+>', '', plain_text)
        
        # 如果没有文本，返回最小高度
        if not plain_text.strip():
            line_height = font_metrics.height()
            min_height = int(line_height * 1.4) + 4
            return QSize(300, min_height)
        
        # 获取可用宽度（考虑父容器的内边距和滚动条宽度）
        parent_widget = self.parent()
        if parent_widget and hasattr(parent_widget, 'layout'):
            layout = parent_widget.layout()
            if layout:
                margins = layout.contentsMargins()
                available_width = parent_widget.width() - margins.left() - margins.right() - 20  # 额外预留空间
            else:
                available_width = parent_widget.width() - 20 if parent_widget.width() > 0 else 280
        else:
            available_width = 280  # 默认宽度
        
        # 查找最顶层的QListWidget来检查滚动条
        list_widget = self.parent()
        while list_widget and not isinstance(list_widget, QListWidget):
            list_widget = list_widget.parent()
        
        # 如果找到了QListWidget，始终为滚动条预留空间
        if list_widget:
            # 始终预留滚动条空间，避免文字被截断
            # 总共预留20px间距
            available_width -= 20
        
        # 确保最小宽度
        available_width = max(available_width, 200)
        
        # 使用QFontMetrics计算在指定宽度下的文本边界
        text_rect = font_metrics.boundingRect(
            0, 0, available_width, 0,
            Qt.TextFlag.TextWordWrap | Qt.TextFlag.TextWrapAnywhere,
            plain_text
        )
        
        # 计算实际需要的行数
        line_height = font_metrics.height()
        actual_lines = max(1, (text_rect.height() + line_height - 1) // line_height)  # 向上取整
        
        # 基于行数计算高度，确保一致性
        # 使用固定的行高倍数，不受文本长度影响
        line_spacing = int(line_height * 1.4)  # 与CSS line-height: 1.4 保持一致
        calculated_height = actual_lines * line_spacing + 4  # 4px 为上下内边距
        
        # 确保最小高度（单行文本的标准高度）
        min_height = line_spacing + 4
        final_height = max(calculated_height, min_height)
        
        return QSize(available_width, final_height)

class HistoryItemWidget(QWidget):
    """历史记录项的自定义Widget
    
    每个历史记录项的容器，包含：
    - 文本内容
    - 统一的内边距
    - 底部分隔线
    """
    def __init__(self, text, parent=None):
        super().__init__(parent)
        # 保存原始HTML文本
        self.original_text = text
        
        layout = QVBoxLayout(self)
        # 减少内边距，实现更紧凑的布局，同时保持高度自适应
        # 增加右边距为滚动条预留更多空间
        layout.setContentsMargins(6, 8, 20, 8)  # 左、上、右、下内边距，右边距设置为20px
        layout.setSpacing(0)  # 移除内部间距
        
        # 创建文本标签
        self.text_label = TextLabel(text, self)
        self.text_label.setOpenExternalLinks(False)  # 禁用外部链接，安全考虑
        # 确保文本标签在容器中垂直居中
        layout.addWidget(self.text_label, 0, Qt.AlignmentFlag.AlignVCenter)
        
        # 设置样式，添加底部分隔线
        self.setStyleSheet("""
            HistoryItemWidget {
                background-color: white;
            }
            HistoryItemWidget::after {  /* 使用伪元素添加分隔线 */
                content: '';
                position: absolute;
                left: 5px;
                right: 5px;
                bottom: 0;
                height: 1px;
                background-color: #E5E5E7;
            }
        """)
    
    def getText(self):
        """获取原始HTML文本内容"""
        return self.original_text
    
    def setText(self, text):
        """设置文本内容并更新显示"""
        self.original_text = text
        self.text_label.setText(text)
        # 更新widget大小提示
        self.updateGeometry()
    
    def sizeHint(self):
        """返回widget的建议大小"""
        # 获取文本标签的建议大小
        text_size = self.text_label.sizeHint()
        
        # 计算总高度：文本高度 + 上下内边距
        margins = self.layout().contentsMargins()
        total_height = text_size.height() + margins.top() + margins.bottom()
        
        # 实现高度自适应，根据内容动态调整高度
        min_height = 35  # 减少最小高度，实现更紧凑的布局
        final_height = max(total_height, min_height)
        
        return QSize(text_size.width(), final_height)

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
                padding: 5px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;  /* 鼠标悬停时的背景色 */
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;  /* 选中时的背景色 */
                color: black;
            }
            /* 滚动条样式 */
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 0px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #C0C0C0;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #A0A0A0;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: transparent;
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
        print(f"更新空状态显示: 列表项数量={self.count()}, 有空状态widget={self.empty_widget is not None}")
        if self.count() == 0 and self.empty_widget:
            # 如果列表为空且有空状态部件，显示空状态
            self.empty_widget.setParent(self.viewport())
            self.empty_widget.show()
            # 调整空状态部件的大小和位置
            self.empty_widget.setGeometry(self.viewport().rect())
            print("✓ 显示空状态提示")
        elif self.empty_widget:
            # 如果列表不为空，隐藏空状态
            self.empty_widget.hide()
            print("✓ 隐藏空状态提示，显示历史记录列表")
            
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