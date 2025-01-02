from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtCore import QUrl
import os

class StateManager(QObject):
    status_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.status = "就绪"
        self.start_sound = None
        self._init_sound()
    
    def _init_sound(self):
        """初始化音效"""
        try:
            sound_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "start.wav")
            if os.path.exists(sound_path):
                self.start_sound = QSoundEffect()
                self.start_sound.setSource(QUrl.fromLocalFile(sound_path))
                self.start_sound.setVolume(1.0)
                self.start_sound.setLoopCount(1)
        except Exception as e:
            print(f"❌ 音效初始化失败: {e}")
            self.start_sound = None
    
    def start_recording(self):
        """开始录音"""
        self.status = "录音中"
        self.status_changed.emit(self.status)
        # 播放音效
        if self.start_sound:
            # 如果正在播放，先停止
            if self.start_sound.isPlaying():
                self.start_sound.stop()
            # 重新初始化音效
            self._init_sound()
            # 播放
            self.start_sound.play()
    
    def stop_recording(self):
        """停止录音"""
        self.status = "就绪"
        self.status_changed.emit(self.status)
    
    def update_status(self, status):
        """更新状态"""
        self.status = status
        self.status_changed.emit(self.status) 