import time
from PyQt6.QtCore import QObject, pyqtSignal
import os
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtCore import QUrl
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StateManager(QObject):
    status_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.recording_status_text = "就绪"
        self.is_recording = False
        self.start_time = 0
        self._last_status = ""
        self._last_dots = ""
        self._dots_count = 0
        
        # 在主线程中创建定时器
        self.moveToThread(QApplication.instance().thread())
        self.status_timer = QTimer()
        self.status_timer.setInterval(200)  # 200ms更新一次
        self.status_timer.timeout.connect(self.update_status)
        
    def start_recording(self):
        """开始录音"""
        self.is_recording = True
        self.start_time = time.time()
        self.status_timer.start()
        
    def stop_recording(self):
        """停止录音"""
        self.is_recording = False
        self.status_timer.stop()
        self.recording_status_text = "就绪"
        self._last_status = ""
        self._last_dots = ""
        self._dots_count = 0
        self.status_changed.emit(self.recording_status_text)
        
    def update_status(self):
        """更新录音状态"""
        if not self.is_recording:
            return
            
        duration = time.time() - self.start_time
        dots = "." * (self._dots_count % 4)
        self._dots_count += 1
        
        # 只在状态真正改变时才发送信号
        status = f"⏺️  录音中{dots} ({duration:.1f}秒)"
        if status != self._last_status:
            self._last_status = status
            self.recording_status_text = status
            self.status_changed.emit(status) 