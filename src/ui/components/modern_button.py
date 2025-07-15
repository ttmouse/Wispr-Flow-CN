# 这个文件是用来实现录音按钮的动画效果的。
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import (Qt, QPropertyAnimation, QEasingCurve, QSize, 
                         QRectF, pyqtProperty, QTimer, QTime, QEvent)
from PyQt6.QtGui import QIcon, QPainter, QColor, QPixmapCache
import random
import sys
import os

# 添加父目录到路径以导入resource_utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from resource_utils import get_icon_path

class ModernButton(QPushButton):
    # 缓存资源
    _normal_icon = None
    _recording_icon = None
    _recording_color = QColor("#FF3B30")
    _normal_color = QColor("black")
    
    # 缓存键
    _CACHE_KEY_NORMAL = "modern_button_normal"
    _CACHE_KEY_RECORDING = "modern_button_recording"
    
    @classmethod
    def _ensure_icons(cls):
        if cls._normal_icon is None:
            cls._normal_icon = QIcon(get_icon_path("mic.png"))
        if cls._recording_icon is None:
            cls._recording_icon = QIcon(get_icon_path("mic-recording.svg"))
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 确保图标已加载
        self._ensure_icons()
        
        # 固定尺寸
        self._base_size = 64
        self._half_size = self._base_size / 2
        self.setFixedSize(self._base_size, self._base_size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 设置图标
        self.setIcon(self._normal_icon)
        self.setIconSize(QSize(24, 24))
        
        # 初始化属性
        self._scale_factor = 1.0
        self._is_recording = False
        self._last_update_time = 0
        
        # 创建动画
        self.animation = QPropertyAnimation(self, b"scale_factor")
        self.animation.setDuration(120)
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        # 创建定时器用于更新动画
        self.update_timer = QTimer()
        self.update_timer.moveToThread(self.thread())
        self.update_timer.timeout.connect(self.update_animation)
        self.update_timer.setInterval(150)  # 降低更新频率
        
        # 预计算动画范围
        self._min_scale = 0.85
        self._max_scale = 0.98
        self._scale_range = self._max_scale - self._min_scale
        
        # 安装事件过滤器
        self.installEventFilter(self)
        
        # 初始化缓存
        self._init_cache()
        
        self.update_style()
    
    def _init_cache(self):
        """初始化按钮状态缓存"""
        # 设置缓存大小（根据需要调整）
        QPixmapCache.setCacheLimit(1024)  # 1MB
    
    @pyqtProperty(float)
    def scale_factor(self):
        return self._scale_factor
    
    @scale_factor.setter
    def scale_factor(self, value):
        if self._scale_factor != value:
            self._scale_factor = value
            self.update()
    
    def update_animation(self):
        """更新动画"""
        if not self._is_recording or not self.isVisible():
            return
            
        current_time = QTime.currentTime().msecsSinceStartOfDay()
        if current_time - self._last_update_time < 100:
            return
            
        # 使用预计算的范围生成随机值
        random_scale = self._min_scale + random.random() * self._scale_range
        
        self.animation.stop()
        self.animation.setStartValue(self._scale_factor)
        self.animation.setEndValue(random_scale)
        self.animation.start()
        
        self._last_update_time = current_time
    
    def set_recording_state(self, is_recording):
        """设置录音状态"""
        if self._is_recording == is_recording:
            return
            
        self._is_recording = is_recording
        self.update_style()
        
        # 控制动画
        if is_recording and self.isVisible():
            self.setIcon(self._recording_icon)
            self._scale_factor = 1.0
            self._last_update_time = QTime.currentTime().msecsSinceStartOfDay()
            self.update_timer.start()
        else:
            self.update_timer.stop()
            self.animation.stop()
            self._scale_factor = 1.0
            self.update()
            self.setIcon(self._normal_icon)
    
    def update_style(self):
        """更新按钮样式"""
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
        """)
    
    def eventFilter(self, obj, event):
        """事件过滤器"""
        if obj is self:
            if event.type() == QEvent.Type.Show:
                if self._is_recording:
                    self._last_update_time = QTime.currentTime().msecsSinceStartOfDay()
                    self.update_timer.start()
            elif event.type() == QEvent.Type.Hide:
                if self._is_recording:
                    self.update_timer.stop()
                    self.animation.stop()
        return super().eventFilter(obj, event)
    
    def paintEvent(self, event):
        """自定义绘制按钮"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 使用缓存的尺寸计算
        scaled_size = self._base_size * self._scale_factor
        x = (self._base_size - scaled_size) / 2
        y = x  # 正方形按钮，x和y偏移相同
        
        # 创建圆形区域
        circle_rect = QRectF(x, y, scaled_size, scaled_size)
        
        # 使用缓存的颜色
        painter.setBrush(self._recording_color if self._is_recording else self._normal_color)
        painter.setPen(Qt.PenStyle.NoPen)
        
        # 绘制完整的圆形
        painter.drawEllipse(circle_rect)
        
        # 绘制图标
        super().paintEvent(event)