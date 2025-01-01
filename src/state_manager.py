import time
from PyQt6.QtCore import QObject, pyqtSignal
import os
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtCore import QUrl
import logging
from PyQt6.QtWidgets import QApplication

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
        self._last_console_status = ""
        self._last_dots = ""
        
        # 初始化开始录音音效
        self.start_sound = QSoundEffect(self)  # 指定父对象
        self.start_sound.setSource(QUrl.fromLocalFile("resources/start.wav"))
        self.start_sound.setVolume(1.0)
        self.start_sound.setLoopCount(1)
        
        # 移动到主线程
        self.moveToThread(QApplication.instance().thread())
    
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
    
    def _ensure_sound_ready(self):
        """确保音效就绪"""
        if not self.start_sound.isLoaded():
            logger.warning("音效未加载，重新加载中...")
            self.start_sound.setSource(QUrl.fromLocalFile("resources/start.wav"))
            # 等待音效加载完成
            while not self.start_sound.isLoaded():
                QApplication.processEvents()
    
    def start_recording(self):
        """开始录音"""
        self.recording = True
        self._recording_start_time = time.time()
        self.paused = False
        
        # 播放开始录音音效
        if self.start_sound.status() == QSoundEffect.Status.Ready:
            self.start_sound.stop()  # 先停止之前可能的播放
            self.start_sound.play()
            logger.info("播放开始录音音效")
        else:
            logger.warning("音效未就绪，重新设置")
            self.start_sound.setSource(QUrl.fromLocalFile("resources/start.wav"))
            if self.start_sound.status() == QSoundEffect.Status.Ready:
                self.start_sound.play()
        
        status = self.recording_status_text
        logger.info("开始录音")
        self._print_status(status)
        self.status_changed.emit(status)
    
    def stop_recording(self):
        """停止录音，不播放音效"""
        if self.recording:
            self.recording = False
            duration = time.time() - self._recording_start_time
            status = f"✓ 录音完成 ({duration:.1f}秒)"
            logger.info(f"停止录音 - {status}")
            print()  # 打印空行，为下一次录音准备
            self.status_changed.emit(status)
    
    def update_status(self):
        """更新状态显示"""
        if self.recording:
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
    
    @property
    def is_recording(self):
        return self.recording
    
    @property
    def is_paused(self):
        return self.paused 