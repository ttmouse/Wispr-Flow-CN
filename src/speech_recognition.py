import logging
import os
import time
import wave
import pyaudio
import numpy as np
import torch
import torchaudio
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
from PyQt6.QtCore import QObject, pyqtSignal
from .ui.settings_window import SettingsWindow

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SpeechRecognizer(QObject):
    text_ready = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.recording = False
        self.frames = []
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.audio_format = pyaudio.paInt16
        self.channels = 1
        
        # 初始化音频接口
        self.audio = pyaudio.PyAudio()
        
        # 初始化语音识别模型
        self.model = pipeline(
            task=Tasks.auto_speech_recognition,
            model='damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch',
            model_revision='v1.2.4'
        )
        
        # 加载高频词
        self.high_frequency_words = self._load_high_frequency_words()
    
    def _load_high_frequency_words(self):
        """加载高频词"""
        return SettingsWindow.get_high_frequency_words()
    
    def start_recording(self):
        """开始录音"""
        self.recording = True
        self.frames = []
        
        # 打开音频流
        self.stream = self.audio.open(
            format=self.audio_format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )
        
        logger.info("开始录音")
    
    def stop_recording(self):
        """停止录音并进行识别"""
        if not self.recording:
            return
            
        self.recording = False
        
        # 停止并关闭音频流
        if hasattr(self, 'stream'):
            self.stream.stop_stream()
            self.stream.close()
        
        # 保存音频文件
        temp_wav = "temp_recording.wav"
        self._save_audio(temp_wav)
        
        # 语音识别
        try:
            # 重新加载高频词（以获取最新设置）
            self.high_frequency_words = self._load_high_frequency_words()
            
            # 进行语音识别
            result = self.model(temp_wav)
            text = result['text']
            
            # 应用高频词修正
            if self.high_frequency_words:
                text = self._apply_high_frequency_words(text)
            
            logger.info(f"识别结果: {text}")
            self.text_ready.emit(text)
            
        except Exception as e:
            logger.error(f"语音识别失败: {e}")
            self.text_ready.emit("识别失败，请重试")
        
        # 删除临时文件
        if os.path.exists(temp_wav):
            os.remove(temp_wav)
    
    def _apply_high_frequency_words(self, text):
        """应用高频词修正"""
        if not self.high_frequency_words:
            return text
            
        # 对每个高频词进行检查
        for word in sorted(self.high_frequency_words, key=len, reverse=True):
            # 检查文本中是否包含与高频词相似的内容
            # 这里可以添加更复杂的模糊匹配逻辑
            if len(word) > 1:  # 只处理长度大于1的词，避免误修正
                # 简单的相似度检查示例
                # 在实际应用中，可以使用更复杂的算法，如编辑距离等
                text = text.replace(word[0] + word[1:], word)  # 修正可能的错误
        
        return text
    
    def record_chunk(self):
        """录制一个音频块"""
        if self.recording and hasattr(self, 'stream'):
            try:
                data = self.stream.read(self.chunk_size)
                self.frames.append(data)
            except Exception as e:
                logger.error(f"录音错误: {e}")
                self.stop_recording()
    
    def _save_audio(self, filename):
        """保存录音到文件"""
        if not self.frames:
            return
            
        try:
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.audio_format))
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(self.frames))
        except Exception as e:
            logger.error(f"保存音频文件失败: {e}")
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'stream'):
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate() 