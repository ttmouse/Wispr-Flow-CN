from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize, QRectF, pyqtProperty
from PyQt6.QtGui import QIcon, QPainter, QColor
from PyQt6.QtMultimedia import QSoundEffect

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
        self.animation.setDuration(100)  # 更快的动画
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.9)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animation.setLoopCount(-1)  # 无限循环
        
        # 设置声音效果
        self.start_sound = QSoundEffect()
        self.start_sound.setSource(Qt.Url.fromLocalFile("resources/start.wav"))
        self.start_sound.setVolume(1.0)
        
        self.stop_sound = QSoundEffect()
        self.stop_sound.setSource(Qt.Url.fromLocalFile("resources/stop.wav"))
        self.stop_sound.setVolume(1.0)
        
        self.update_style()
    
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
        
        # 控制动画和声音
        if is_recording:
            self.setIcon(QIcon("resources/mic-recording.svg"))
            self.start_sound.play()
            self.animation.setDirection(QPropertyAnimation.Direction.Forward)
            self.animation.start()
        else:
            self.animation.stop()
            self._scale_factor = 1.0
            self.update()
            self.stop_sound.play()
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