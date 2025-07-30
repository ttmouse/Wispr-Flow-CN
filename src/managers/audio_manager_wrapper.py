"""
音频管理器包装器
完全兼容原始AudioCapture接口，作为第四步替换
"""

import logging
from audio_capture import AudioCapture as OriginalAudioCapture


class AudioManagerWrapper:
    """音频管理器包装器 - 第四步模块化替换"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._original_capture = None
        self._initialized = False
        self._initialize()
    
    def _initialize(self):
        """初始化原始音频捕获 - 延迟初始化避免焦点问题"""
        try:
            # 延迟初始化，避免在包装器创建时立即初始化音频系统
            self._original_capture = None
            self._initialized = False
            self.logger.info("音频管理器包装器创建成功（延迟初始化）")
        except Exception as e:
            self.logger.error(f"音频管理器包装器创建失败: {e}")
            raise
    
    def _ensure_initialized(self):
        """确保原始音频捕获已初始化"""
        if not self._initialized:
            try:
                self._original_capture = OriginalAudioCapture()
                self._initialized = True
                self.logger.info("音频管理器延迟初始化成功")
            except Exception as e:
                self.logger.error(f"音频管理器延迟初始化失败: {e}")
                raise
    
    # 完全委托给原始音频捕获的所有方法
    def start_recording(self):
        """开始录音"""
        self._ensure_initialized()
        return self._original_capture.start_recording()
    
    def stop_recording(self):
        """停止录音"""
        if self._initialized and self._original_capture:
            return self._original_capture.stop_recording()
    
    def get_audio_data(self):
        """获取录音数据"""
        self._ensure_initialized()
        return self._original_capture.get_audio_data()
    
    def clear_recording_data(self):
        """清理录音数据"""
        if self._initialized and self._original_capture:
            return self._original_capture.clear_recording_data()
    
    def set_volume_threshold(self, threshold):
        """设置音量阈值"""
        self._ensure_initialized()
        return self._original_capture.set_volume_threshold(threshold)
    
    def cleanup(self):
        """清理资源"""
        if self._initialized and self._original_capture and hasattr(self._original_capture, 'cleanup'):
            return self._original_capture.cleanup()
    
    # 属性委托
    @property
    def frames(self):
        """音频帧数据"""
        if self._initialized and self._original_capture:
            return getattr(self._original_capture, 'frames', None)
        return None
    
    @property
    def stream(self):
        """音频流"""
        if self._initialized and self._original_capture:
            return getattr(self._original_capture, 'stream', None)
        return None
    
    @property
    def audio(self):
        """PyAudio实例"""
        if self._initialized and self._original_capture:
            return getattr(self._original_capture, 'audio', None)
        return None
    
    @property
    def device_index(self):
        """设备索引"""
        if self._initialized and self._original_capture:
            return getattr(self._original_capture, 'device_index', None)
        return None
    
    @property
    def volume_threshold(self):
        """音量阈值"""
        if self._initialized and self._original_capture:
            return getattr(self._original_capture, 'volume_threshold', 0.001)
        return 0.001
    
    @volume_threshold.setter
    def volume_threshold(self, value):
        """设置音量阈值"""
        self._ensure_initialized()
        if self._original_capture:
            self._original_capture.volume_threshold = value
    
    # 委托所有其他方法调用给原始音频捕获
    def __getattr__(self, name):
        """委托所有其他方法调用给原始音频捕获"""
        self._ensure_initialized()
        if self._original_capture and hasattr(self._original_capture, name):
            return getattr(self._original_capture, name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def get_status(self):
        """获取管理器状态"""
        return {
            'name': 'AudioManagerWrapper',
            'initialized': self._initialized,
            'original_capture_type': type(self._original_capture).__name__ if self._initialized and self._original_capture else None,
            'has_stream': self.stream is not None if self._initialized else False,
            'device_index': self.device_index if self._initialized else None
        }
