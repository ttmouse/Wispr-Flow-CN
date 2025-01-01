import time
from PyQt6.QtCore import QObject, pyqtSignal
import os
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtCore import QUrl
import logging

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StateManager(QObject):
    status_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.recording = False
        self.paused = False
        self._recording_start_time = 0
        self._dot_count = 0
        self._last_update = 0
        self._last_console_status = ""  # 用于避免重复打印相同状态
        self._last_dots = ""  # 用于动态点的状态
        
        # 初始化开始录音音效
        self.start_sound = QSoundEffect()
        self.start_sound.setSource(QUrl.fromLocalFile(os.path.join("resources", "start.wav")))
        self.start_sound.setVolume(0.5)
        logger.info("状态管理器初始化完成")
    
    @property
    def recording_status_text(self):
        if not self.recording:
            return "就绪"
        elif self.paused:
            return "已暂停"
        else:
            # 只更新动态点，保持基本文本不变
            new_dots = "." * ((int(time.time() * 2) % 3) + 1)
            if new_dots != self._last_dots:
                self._last_dots = new_dots
            duration = time.time() - self._recording_start_time
            return f"⏺️  录音中{self._last_dots} ({duration:.1f}秒)"
    
    def start_recording(self):
        self.recording = True
        self._recording_start_time = time.time()
        self.paused = False
        self.start_sound.play()
        status = self.recording_status_text
        logger.info("开始录音")
        self._print_status(status)
        self.status_changed.emit(status)
    
    def stop_recording(self):
        if self.recording:
            self.recording = False
            duration = time.time() - self._recording_start_time
            status = f"✓ 录音完成 ({duration:.1f}秒)"
            logger.info(f"停止录音 - {status}")
            print()  # 打印空行，为下一次录音准备
            self.status_changed.emit(status)
    
    def toggle_pause(self):
        if self.recording:
            self.paused = not self.paused
            status = self.recording_status_text
            logger.info("暂停录音" if self.paused else "恢复录音")
            self._print_status(status)
            self.status_changed.emit(status)
    
    def update_recording_status(self, duration=None):
        current_time = time.time()
        if current_time - self._last_update >= 0.1:  # 每 100ms 更新一次
            self._last_update = current_time
            status = self.recording_status_text
            self._print_status(status)
            self.status_changed.emit(status)
    
    def _print_status(self, status):
        """打印状态到控制台，避免重复打印相同状态"""
        # 只比较不包含时间的部分
        base_status = status[:status.rfind("(")] if "(" in status else status
        last_base_status = self._last_console_status[:self._last_console_status.rfind("(")] if "(" in self._last_console_status else self._last_console_status
        
        if base_status != last_base_status or "秒" in status:
            print(f"\r\033[K{status}", end="", flush=True)  # \r 回到行首，\033[K 清除行
            self._last_console_status = status 