import time
from PyQt6.QtCore import QObject, pyqtSignal
import os
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtCore import QUrl

class StateManager(QObject):
    status_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.recording = False
        self.paused = False
        self._recording_start_time = 0
        self._dot_count = 0
        self._last_update = 0
        
        # 初始化音效
        self.start_sound = QSoundEffect()
        self.start_sound.setSource(QUrl.fromLocalFile(os.path.join("resources", "start.wav")))
        self.start_sound.setVolume(0.5)
        
        self.stop_sound = QSoundEffect()
        self.stop_sound.setSource(QUrl.fromLocalFile(os.path.join("resources", "stop.wav")))
        self.stop_sound.setVolume(0.5)
    
    @property
    def recording_status_text(self):
        if not self.recording:
            return "就绪"
        elif self.paused:
            return "已暂停"
        else:
            dots = "." * ((int(time.time() * 2) % 3) + 1)
            duration = time.time() - self._recording_start_time
            return f"⏺️  录音中{dots} ({duration:.1f}秒)"
    
    def start_recording(self):
        self.recording = True
        self._recording_start_time = time.time()
        self.paused = False
        self.start_sound.play()
        self.status_changed.emit(self.recording_status_text)
    
    def stop_recording(self):
        if self.recording:
            self.recording = False
            duration = time.time() - self._recording_start_time
            self.stop_sound.play()
            self.status_changed.emit(f"✓ 录音完成 ({duration:.1f}秒)")
    
    def toggle_pause(self):
        if self.recording:
            self.paused = not self.paused
            self.status_changed.emit(self.recording_status_text)
    
    def update_recording_status(self, duration=None):
        current_time = time.time()
        if current_time - self._last_update >= 0.1:  # 每 100ms 更新一次
            self._last_update = current_time
            self.status_changed.emit(self.recording_status_text) 