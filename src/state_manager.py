from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QApplication
import os
import logging

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StateManager(QObject):
    status_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.status = "就绪"
        self.start_sound = None
        self._init_sound()
    
    def _init_sound(self):
        """初始化音效"""
        # 确保在主线程中初始化
        if QApplication.instance().thread() != self.thread():
            self.moveToThread(QApplication.instance().thread())
        
        # 初始化音效
        self.start_sound = QSoundEffect(self)  # 指定父对象
        sound_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "start.wav")
        self.start_sound.setSource(QUrl.fromLocalFile(sound_path))
        self.start_sound.setVolume(0.3)  # 不要修改这个大小，我需要小的音量。
        self.start_sound.setLoopCount(1)
    
    def start_recording(self):
        """开始录音"""
        self.status = "录音中"
        self.status_changed.emit(self.status)
        
        # 播放音效
        if self.start_sound:
            if self.start_sound.isPlaying():
                self.start_sound.stop()
            self.start_sound.play()
    
    def stop_recording(self):
        """停止录音"""
        self.status = "就绪"
        self.status_changed.emit(self.status)
    
    def update_status(self, status):
        """更新状态"""
        self.status = status
        self.status_changed.emit(self.status) 