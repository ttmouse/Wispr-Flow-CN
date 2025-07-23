# 现代化列表组件 - 重构后的主列表组件
# 专注于列表管理和用户交互

from PyQt6.QtWidgets import QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt, QTimer
from .history_item import HistoryItemWidget, HistoryItem
from .list_styles import ListStyleManager
from ..simple_style_config import style_config

class ModernListWidget(QListWidget):
    """现代化列表组件
    
    用于显示语音识别历史记录的主列表组件，特点：
    - 现代化的UI设计
    - 支持自动换行
    - 鼠标悬停效果
    - 平滑滚动
    - 模块化的样式管理
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.empty_widget = None
        self._last_click_time = 0
        self._last_clicked_item = None  # 记录上次点击的项目
        self._click_debounce_ms = 50  # 减少到50ms防抖间隔
        self._setup_ui()
        self._setup_styles()
        self._setup_scrolling()
    
    def _setup_ui(self):
        """设置UI基本属性"""
        self.setWordWrap(True)
        self.setSpacing(int(style_config.get_spacing('list_spacing')))
        self.setFont(ListStyleManager.get_font_config())
    
    def _setup_styles(self):
        """设置样式"""
        self.setStyleSheet(ListStyleManager.get_list_widget_style())
    
    def _setup_scrolling(self):
        """设置滚动条配置"""
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    
    def addItem(self, item):
        """添加新的历史记录项到列表底部"""
        if isinstance(item, str):
            self._add_string_item(item)
        else:
            self._add_list_item(item)
        
        # 添加新项目后，更新所有项目的尺寸
        QTimer.singleShot(10, self._update_item_sizes)
        
        self.scrollToBottom()
        self.updateEmptyState()
    
    def _add_string_item(self, text):
        """添加字符串类型的项目"""
        list_item = QListWidgetItem()
        super().addItem(list_item)  # 使用父类方法添加到底部
        
        widget = HistoryItemWidget(text)
        # 先设置widget到列表中，确保它能获得正确的父容器
        self.setItemWidget(list_item, widget)
        # 强制更新widget的几何信息
        widget.updateGeometry()
        # 然后设置正确的尺寸
        list_item.setSizeHint(widget.sizeHint())
    
    def _add_list_item(self, item):
        """添加列表项类型的项目"""
        super().addItem(item)  # 使用父类方法添加到底部
    
    def clear(self):
        """清空列表"""
        super().clear()
        self.updateEmptyState()
    
    def setEmptyState(self, widget):
        """设置空状态显示的部件"""
        self.empty_widget = widget
        self.updateEmptyState()
    
    def updateEmptyState(self):
        """更新空状态显示"""
        # print(f"更新空状态显示: 列表项数量={self.count()}, 有空状态widget={self.empty_widget is not None}")
        
        if self.count() == 0 and self.empty_widget:
            self._show_empty_state()
        elif self.empty_widget:
            self._hide_empty_state()
    
    def _show_empty_state(self):
        """显示空状态"""
        self.empty_widget.setParent(self.viewport())
        self.empty_widget.show()
        self.empty_widget.setGeometry(self.viewport().rect())
    
    def _hide_empty_state(self):
        """隐藏空状态"""
        self.empty_widget.hide()
        pass
    
    def mousePressEvent(self, event):
        """处理鼠标点击事件"""
        try:
            # 改进的防抖处理：只对同一项目进行防抖，不同项目可以立即点击
            import time
            current_time = time.time() * 1000  # 转换为毫秒
            current_item = self.itemAt(event.pos())
            
            # 只有在短时间内点击同一项目时才进行防抖
            if (current_item is not None and 
                current_item == self._last_clicked_item and 
                current_time - self._last_click_time < self._click_debounce_ms):
                # 在防抖间隔内点击同一项目，忽略此次点击
                return
            
            self._last_click_time = current_time
            self._last_clicked_item = current_item
            
            # 确保事件正常传递给父类
            super().mousePressEvent(event)
            
        except Exception as e:
            import logging
            logging.error(f"鼠标点击事件处理失败: {e}")
            # 即使出错也要确保事件传递
            try:
                super().mousePressEvent(event)
            except:
                pass
    
    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件"""
        try:
            item_at_pos = self.itemAt(event.pos())
            
            # 先调用父类方法，确保itemClicked信号能正常触发
            super().mouseReleaseEvent(event)
            
            # 只在点击空白区域时清除选择，避免影响正常的项目点击
            if item_at_pos is None:
                # 点击的是空白区域，立即清除选择
                self.clearSelection()
            else:
                # 点击的是列表项，使用极短延迟确保itemClicked信号先触发
                QTimer.singleShot(5, self.clearSelection)  # 减少到5ms，几乎无感知延迟
                
        except Exception as e:
            import logging
            logging.error(f"鼠标释放事件处理失败: {e}")
            # 即使出错也要确保事件传递
            try:
                super().mouseReleaseEvent(event)
            except:
                pass
    
    def resizeEvent(self, event):
        """处理窗口大小改变事件"""
        try:
            super().resizeEvent(event)
            self._update_item_sizes()
            self.updateEmptyState()
        except Exception as e:
            import logging
            logging.error(f"窗口大小改变事件处理失败: {e}")
    
    def _update_item_sizes(self):
        """更新所有项目的大小"""
        try:
            for i in range(self.count()):
                item = self.item(i)
                if item and self.itemWidget(item):
                    widget = self.itemWidget(item)
                    if widget and hasattr(widget, 'sizeHint'):
                        item.setSizeHint(widget.sizeHint())
        except Exception as e:
            import logging
            logging.error(f"更新项目大小失败: {e}")
    
    def get_item_count(self):
        """获取列表项数量"""
        return self.count()
    
    def get_item_text(self, index):
        """获取指定索引项目的文本"""
        if 0 <= index < self.count():
            item = self.item(index)
            if item:
                widget = self.itemWidget(item)
                if widget and hasattr(widget, 'getText'):
                    return widget.getText()
                return item.text()
        return None
    
    def update_item_text(self, index, text):
        """更新指定索引项目的文本"""
        if 0 <= index < self.count():
            item = self.item(index)
            if item:
                widget = self.itemWidget(item)
                if widget and hasattr(widget, 'setText'):
                    widget.setText(text)
                    item.setSizeHint(widget.sizeHint())
                    return True
        return False