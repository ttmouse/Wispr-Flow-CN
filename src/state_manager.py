from PyQt6.QtCore import QObject, pyqtSignal, QUrl
from PyQt6.QtMultimedia import QSoundEffect
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
        self.stop_sound = None
        self._init_sound()
    
    def _init_sound(self):
        """初始化音效"""
        try:
            # 确保在主线程中初始化
            if QApplication.instance().thread() != self.thread():
                self.moveToThread(QApplication.instance().thread())
            
            # 初始化开始音效
            self.start_sound = QSoundEffect()
            self.start_sound.moveToThread(QApplication.instance().thread())  # 确保音效对象在主线程
            start_sound_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "start.wav")
            self.start_sound.setSource(QUrl.fromLocalFile(start_sound_path))
            self.start_sound.setVolume(0.3)  # 不要修改这个大小，我需要小的音量。
            self.start_sound.setLoopCount(1)
            self.start_sound.status()  # 预加载音效
            
            # 初始化停止音效
            self.stop_sound = QSoundEffect()
            self.stop_sound.moveToThread(QApplication.instance().thread())  # 确保音效对象在主线程
            stop_sound_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "stop.wav")
            self.stop_sound.setSource(QUrl.fromLocalFile(stop_sound_path))
            self.stop_sound.setVolume(0.3)  # 不要修改这个大小，我需要小的音量。
            self.stop_sound.setLoopCount(1)
            self.stop_sound.status()  # 预加载音效
        except Exception as e:
            print(f"音效初始化失败: {e}")
    
    def start_recording(self):
        """开始录音"""
        try:
            self.status = "录音中"
            self.status_changed.emit(self.status)
            # 开始录音时不播放音效
        except Exception as e:
            print(f"开始录音失败: {e}")
    
    def stop_recording(self):
        """停止录音"""
        try:
            self.status = "就绪"
            self.status_changed.emit(self.status)
            
            # 播放停止音效 - 使用新实例避免状态冲突
            self._play_stop_sound()
        except Exception as e:
            print(f"停止录音失败: {e}")
    
    def _play_stop_sound(self):
        """播放停止音效 - 使用预初始化的音效实例"""
        try:
            # 使用预初始化的停止音效实例，避免临时创建导致的垃圾回收问题
            if self.stop_sound and self.stop_sound.status() == QSoundEffect.Status.Ready:
                self.stop_sound.play()
                print("✓ 停止音效已播放")
            else:
                # 如果预初始化的音效不可用，创建临时实例并保持引用
                if not hasattr(self, '_temp_stop_sound'):
                    self._temp_stop_sound = QSoundEffect()
                    self._temp_stop_sound.moveToThread(QApplication.instance().thread())
                    
                    # 设置音效文件路径
                    stop_sound_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "stop.wav")
                    self._temp_stop_sound.setSource(QUrl.fromLocalFile(stop_sound_path))
                    self._temp_stop_sound.setVolume(0.3)
                    self._temp_stop_sound.setLoopCount(1)
                    
                    # 连接播放完成信号，清理临时实例
                    def on_playing_changed():
                        if not self._temp_stop_sound.isPlaying():
                            self._temp_stop_sound.deleteLater()
                            self._temp_stop_sound = None
                    
                    self._temp_stop_sound.playingChanged.connect(on_playing_changed)
                
                # 播放临时音效
                if self._temp_stop_sound.status() == QSoundEffect.Status.Ready:
                    self._temp_stop_sound.play()
                    print("✓ 停止音效已播放（临时实例）")
                else:
                    print("⚠️ 停止音效未就绪，无法播放")
                
        except Exception as e:
            print(f"❌ 播放停止音效失败: {e}")
    
    def update_status(self, status):
        """更新状态"""
        self.status = status
        self.status_changed.emit(self.status)
    
    def reload_hotwords(self):
        """重新加载热词"""
        if hasattr(self, 'funasr_engine'):
            self.funasr_engine.reload_hotwords()
    
    def get_hotwords(self):
        """获取热词列表"""
        if hasattr(self, 'funasr_engine'):
            return getattr(self.funasr_engine, 'hotwords', [])
        return []
    
    def cleanup(self):
        """清理资源"""
        try:
            # 停止并清理音效资源
            if hasattr(self, 'start_sound') and self.start_sound:
                self.start_sound.stop()
                self.start_sound.deleteLater()
                self.start_sound = None
            
            if hasattr(self, 'stop_sound') and self.stop_sound:
                self.stop_sound.stop()
                self.stop_sound.deleteLater()
                self.stop_sound = None
            
            # 清理临时停止音效实例
            if hasattr(self, '_temp_stop_sound') and self._temp_stop_sound:
                self._temp_stop_sound.stop()
                self._temp_stop_sound.deleteLater()
                self._temp_stop_sound = None
            
            print("✓ StateManager资源已清理")
        except Exception as e:
            print(f"❌ StateManager资源清理失败: {e}")