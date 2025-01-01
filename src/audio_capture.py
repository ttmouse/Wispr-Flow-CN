import pyaudio
import numpy as np
import time

class AudioCapture:
    def __init__(self):
        self.frames = []
        self.stream = None
        self.audio = pyaudio.PyAudio()
        self.device_index = self._get_default_mic_index()
        self.read_count = 0
        
    def _get_default_mic_index(self):
        default_device = self.audio.get_default_input_device_info()
        return default_device['index']

    def start_recording(self):
        """开始录音"""
        self.frames = []
        self.read_count = 0
        self.stream = self.audio.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=16000,
            input=True,
            input_device_index=self.device_index,
            frames_per_buffer=1024,
            stream_callback=None
        )

    def read_audio(self):
        """读取音频数据"""
        if self.stream and self.stream.is_active():
            data = self.stream.read(1024, exception_on_overflow=False)
            self.frames.append(data)
            self.read_count += 1
            return data
        return b""

    def stop_recording(self):
        """停止录音"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            
        audio_data = b"".join(self.frames)
        data = np.frombuffer(audio_data, dtype=np.float32)
        return data

    def get_audio_data(self):
        """获取录音数据"""
        if not self.frames:
            return np.array([], dtype=np.float32)
            
        audio_data = b"".join(self.frames)
        data = np.frombuffer(audio_data, dtype=np.float32)
        return data

    def clear_recording_data(self):
        """清理录音数据"""
        self.frames = []
        self.read_count = 0