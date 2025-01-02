from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QApplication
import os
import logging

class StateManager(QObject):
    """状态管理器，处理录音状态和音效"""
    # 常量定义
    SOUND_EFFECT_PATH = os.path.join("resources", "start.wav")
    SOUND_EFFECT_VOLUME = 0.3  # 调整音量
    STATUS_READY = "就绪"
    STATUS_RECORDING = "录音中"
    
    # 信号定义
    status_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)  # 错误信号

    def __init__(self):
        """初始化状态管理器"""
        super().__init__()
        self.is_recording = False
        self.start_sound = None
        
        try:
            self._create_sound_effect()
        except Exception as e:
            logging.error(f"音效初始化失败: {e}")
            self.error_occurred.emit(f"音效初始化失败: {e}")
        
        # 移动到主线程
        self.moveToThread(QApplication.instance().thread())

    def _create_sound_effect(self):
        """创建新的音效实例"""
        try:
            # 清理旧实例
            if self.start_sound is not None:
                self.start_sound.stop()
                self.start_sound.deleteLater()
            
            # 检查音效文件是否存在
            if not os.path.exists(self.SOUND_EFFECT_PATH):
                raise FileNotFoundError(f"音效文件不存在: {self.SOUND_EFFECT_PATH}")
            
            # 创建新实例
            self.start_sound = QSoundEffect(self)
            self.start_sound.setSource(QUrl.fromLocalFile(self.SOUND_EFFECT_PATH))
            self.start_sound.setVolume(self.SOUND_EFFECT_VOLUME)
            self.start_sound.setLoopCount(1)
            
            # 等待音效加载，但设置超时
            for _ in range(100):  # 最多等待1秒
                QApplication.processEvents()
                if self.start_sound.isLoaded():
                    break
            
            if not self.start_sound.isLoaded():
                raise TimeoutError("音效加载超时")
                
        except Exception as e:
            logging.error(f"创建音效实例失败: {e}")
            self.error_occurred.emit(f"创建音效实例失败: {e}")
            raise

    def start_recording(self):
        """开始录音"""
        if self.is_recording:
            return  # 防止重复启动
            
        try:
            self.is_recording = True
            self._create_sound_effect()  # 每次播放前创建新实例
            self.start_sound.play()
            self.status_changed.emit(self.STATUS_RECORDING)
        except Exception as e:
            self.is_recording = False
            logging.error(f"开始录音失败: {e}")
            self.error_occurred.emit(f"开始录音失败: {e}")

    def stop_recording(self):
        """停止录音"""
        if not self.is_recording:
            return  # 防止重复停止
            
        self.is_recording = False
        self.status_changed.emit(self.STATUS_READY)
        
    def __del__(self):
        """析构函数，确保资源被正确释放"""
        if self.start_sound is not None:
            try:
                self.start_sound.stop()
                self.start_sound.deleteLater()
            except:
                pass  # 忽略清理时的错误 