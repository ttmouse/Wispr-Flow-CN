#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可复用的UI混入类
解决UI组件事件处理重复问题
"""

from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QWidget
from abc import ABC, abstractmethod
from typing import Optional, Callable

class DraggableMixin:
    """可拖拽混入类
    
    为任何QWidget添加拖拽功能
    """
    
    def __init__(self):
        # 拖拽相关状态
        self._is_dragging = False
        self._drag_start_pos: Optional[QPoint] = None
        self._drag_enabled = True
        
        # 性能优化：限制拖拽更新频率
        self._drag_timer = QTimer()
        self._drag_timer.setSingleShot(True)
        self._drag_timer.timeout.connect(self._apply_pending_move)
        self._pending_move_pos: Optional[QPoint] = None
        
        # 拖拽回调
        self._drag_start_callback: Optional[Callable] = None
        self._drag_end_callback: Optional[Callable] = None
    
    def set_draggable(self, enabled: bool):
        """设置是否可拖拽"""
        self._drag_enabled = enabled
    
    def set_drag_callbacks(self, 
                          start_callback: Optional[Callable] = None,
                          end_callback: Optional[Callable] = None):
        """设置拖拽回调函数"""
        self._drag_start_callback = start_callback
        self._drag_end_callback = end_callback
    
    def mousePressEvent(self, event: QMouseEvent):
        """处理鼠标按下事件"""
        if (self._drag_enabled and 
            event.button() == Qt.MouseButton.LeftButton):
            self._is_dragging = True
            self._drag_start_pos = event.pos()
            
            if self._drag_start_callback:
                self._drag_start_callback()
        
        # 调用父类方法
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """处理鼠标移动事件"""
        if (self._is_dragging and 
            self._drag_start_pos is not None and
            self._drag_enabled):
            
            # 计算新位置
            new_pos = self.pos() + event.pos() - self._drag_start_pos
            
            # 使用定时器限制更新频率
            self._pending_move_pos = new_pos
            if not self._drag_timer.isActive():
                self._drag_timer.start(16)  # ~60fps
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """处理鼠标释放事件"""
        if self._is_dragging:
            self._is_dragging = False
            self._drag_start_pos = None
            
            # 停止拖拽定时器
            self._drag_timer.stop()
            
            # 应用最后的移动位置
            if self._pending_move_pos is not None:
                self.move(self._pending_move_pos)
                self._pending_move_pos = None
            
            if self._drag_end_callback:
                self._drag_end_callback()
        
        super().mouseReleaseEvent(event)
    
    def _apply_pending_move(self):
        """应用待处理的移动"""
        if self._pending_move_pos is not None:
            self.move(self._pending_move_pos)

class ClickHandlerMixin:
    """点击处理混入类
    
    提供防抖点击处理功能
    """
    
    def __init__(self):
        self._last_click_time = 0
        self._click_debounce_ms = 300  # 300ms防抖
        self._click_callback: Optional[Callable] = None
        self._double_click_callback: Optional[Callable] = None
    
    def set_click_callback(self, callback: Callable):
        """设置单击回调"""
        self._click_callback = callback
    
    def set_double_click_callback(self, callback: Callable):
        """设置双击回调"""
        self._double_click_callback = callback
    
    def set_click_debounce(self, ms: int):
        """设置点击防抖时间"""
        self._click_debounce_ms = ms
    
    def mousePressEvent(self, event: QMouseEvent):
        """处理鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            current_time = QTimer.currentTime()
            
            # 防抖处理
            if current_time - self._last_click_time > self._click_debounce_ms:
                self._last_click_time = current_time
                
                if self._click_callback:
                    # 延迟执行，以便检测双击
                    QTimer.singleShot(200, self._handle_single_click)
        
        super().mousePressEvent(event)
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """处理鼠标双击事件"""
        if (event.button() == Qt.MouseButton.LeftButton and 
            self._double_click_callback):
            self._double_click_callback()
        
        super().mouseDoubleClickEvent(event)
    
    def _handle_single_click(self):
        """处理单击事件"""
        if self._click_callback:
            self._click_callback()

class HoverEffectMixin:
    """悬停效果混入类
    
    提供鼠标悬停视觉反馈
    """
    
    def __init__(self):
        self._hover_style = ""
        self._normal_style = ""
        self._hover_enabled = True
    
    def set_hover_styles(self, normal_style: str, hover_style: str):
        """设置悬停样式"""
        self._normal_style = normal_style
        self._hover_style = hover_style
        self.setStyleSheet(normal_style)
    
    def set_hover_enabled(self, enabled: bool):
        """设置是否启用悬停效果"""
        self._hover_enabled = enabled
    
    def enterEvent(self, event):
        """鼠标进入事件"""
        if self._hover_enabled and self._hover_style:
            self.setStyleSheet(self._hover_style)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        if self._hover_enabled and self._normal_style:
            self.setStyleSheet(self._normal_style)
        super().leaveEvent(event)

class ResizableMixin:
    """可调整大小混入类
    
    为组件添加调整大小功能
    """
    
    def __init__(self):
        self._resize_enabled = True
        self._resize_margin = 5  # 调整大小的边缘区域
        self._resizing = False
        self._resize_start_pos: Optional[QPoint] = None
        self._resize_start_size = None
    
    def set_resizable(self, enabled: bool):
        """设置是否可调整大小"""
        self._resize_enabled = enabled
    
    def mousePressEvent(self, event: QMouseEvent):
        """处理鼠标按下事件"""
        if (self._resize_enabled and 
            event.button() == Qt.MouseButton.LeftButton and
            self._is_in_resize_area(event.pos())):
            
            self._resizing = True
            self._resize_start_pos = event.globalPos()
            self._resize_start_size = self.size()
            return
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """处理鼠标移动事件"""
        if self._resizing and self._resize_start_pos is not None:
            # 计算新大小
            delta = event.globalPos() - self._resize_start_pos
            new_width = max(self.minimumWidth(), 
                          self._resize_start_size.width() + delta.x())
            new_height = max(self.minimumHeight(), 
                           self._resize_start_size.height() + delta.y())
            
            self.resize(new_width, new_height)
            return
        
        # 更新鼠标光标
        if self._resize_enabled and self._is_in_resize_area(event.pos()):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """处理鼠标释放事件"""
        if self._resizing:
            self._resizing = False
            self._resize_start_pos = None
            self._resize_start_size = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
            return
        
        super().mouseReleaseEvent(event)
    
    def _is_in_resize_area(self, pos: QPoint) -> bool:
        """检查是否在调整大小区域"""
        rect = self.rect()
        return (pos.x() > rect.width() - self._resize_margin and
                pos.y() > rect.height() - self._resize_margin)

# 组合使用示例
class ModernWindow(QWidget, DraggableMixin, HoverEffectMixin):
    """现代化窗口组件
    
    组合多个混入类的功能
    """
    
    def __init__(self):
        QWidget.__init__(self)
        DraggableMixin.__init__(self)
        HoverEffectMixin.__init__(self)
        
        self._setup_ui()
        self._setup_styles()
    
    def _setup_ui(self):
        """设置UI"""
        self.setFixedSize(400, 300)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # 设置拖拽回调
        self.set_drag_callbacks(
            start_callback=self._on_drag_start,
            end_callback=self._on_drag_end
        )
    
    def _setup_styles(self):
        """设置样式"""
        normal_style = """
            QWidget {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
            }
        """
        
        hover_style = """
            QWidget {
                background-color: #3d3d3d;
                border: 1px solid #4d4d4d;
                border-radius: 8px;
            }
        """
        
        self.set_hover_styles(normal_style, hover_style)
    
    def _on_drag_start(self):
        """拖拽开始回调"""
        print("开始拖拽窗口")
    
    def _on_drag_end(self):
        """拖拽结束回调"""
        print("拖拽窗口结束")

class ClickableLabel(QWidget, ClickHandlerMixin, HoverEffectMixin):
    """可点击的标签组件"""
    
    def __init__(self, text: str = ""):
        QWidget.__init__(self)
        ClickHandlerMixin.__init__(self)
        HoverEffectMixin.__init__(self)
        
        self._text = text
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        # 设置点击回调
        self.set_click_callback(self._on_single_click)
        self.set_double_click_callback(self._on_double_click)
        
        # 设置悬停样式
        normal_style = "QWidget { color: #ffffff; }"
        hover_style = "QWidget { color: #007AFF; }"
        self.set_hover_styles(normal_style, hover_style)
    
    def _on_single_click(self):
        """单击处理"""
        print(f"单击标签: {self._text}")
    
    def _on_double_click(self):
        """双击处理"""
        print(f"双击标签: {self._text}")
