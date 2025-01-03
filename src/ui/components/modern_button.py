# 这个文件是用来实现录音按钮的动画效果的。
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize, QRectF, pyqtProperty, QTimer
from PyQt6.QtGui import QIcon, QPainter, QColor
import random

class ModernButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(64, 64)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 设置图标
        self.setIcon(QIcon("resources/mic.png"))
        self.setIconSize(QSize(24, 24))
        
        # 初始化属性
        self._scale_factor = 1.0
        self._is_recording = False
        
        # 创建动画
        self.animation = QPropertyAnimation(self, b"scale_factor")
        self.animation.setDuration(80)
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        # 创建定时器用于更新动画
        self.update_timer = QTimer()
        self.update_timer.moveToThread(self.thread())
        self.update_timer.timeout.connect(self.update_animation)
        self.update_timer.setInterval(100)
        
        self.update_style()
    
    def update_animation(self):
        """更新动画"""
        if not self._is_recording:
            return
            
        # 简单的缩放动画
        random_scale = random.uniform(0.88, 0.95)
        
        self.animation.stop()
        self.animation.setStartValue(self._scale_factor)
        self.animation.setEndValue(random_scale)
        self.animation.start()
    
    @pyqtProperty(float)
    def scale_factor(self):
        return self._scale_factor
    
    @scale_factor.setter
    def scale_factor(self, value):
        if self._scale_factor != value:
            self._scale_factor = value
            self.update()
    
    def set_recording_state(self, is_recording):
        """设置录音状态"""
        if self._is_recording == is_recording:
            return
            
        self._is_recording = is_recording
        self.update_style()
        
        # 控制动画
        if is_recording:
            self.setIcon(QIcon("resources/mic-recording.svg"))
            self._scale_factor = 1.0
            self.update_timer.start()
        else:
            self.update_timer.stop()
            self.animation.stop()
            self._scale_factor = 1.0
            self.update()
            self.setIcon(QIcon("resources/mic.png"))
    
    def update_style(self):
        """更新按钮样式"""
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
        """)
    
    def paintEvent(self, event):
        """自定义绘制按钮"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 计算缩放后的尺寸和位置
        width = self.width()
        height = self.height()
        scaled_size = min(width, height) * self._scale_factor
        
        # 计算居中位置
        x = (width - scaled_size) / 2
        y = (height - scaled_size) / 2
        
        # 创建圆形区域
        circle_rect = QRectF(x, y, scaled_size, scaled_size)
        
        # 绘制背景圆
        if self._is_recording:
            painter.setBrush(QColor("#FF3B30"))
        else:
            painter.setBrush(QColor("black"))
        painter.setPen(Qt.PenStyle.NoPen)
        
        # 绘制完整的圆形
        painter.drawEllipse(circle_rect)
        
        # 绘制图标
        super().paintEvent(event) 