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
        # 音量相关参数
        self.volume_threshold = 0.01  # 音量阈值，低于此值视为噪音
        self.min_valid_frames = 3     # 最少需要多少帧有效音频
        self.valid_frame_count = 0    # 有效音频帧计数
        
    def _get_default_mic_index(self):
        default_device = self.audio.get_default_input_device_info()
        print(f"使用默认麦克风: {default_device['name']}")
        return default_device['index']

    def start_recording(self):
        """开始录音"""
        self.frames = []
        self.read_count = 0
        self.valid_frame_count = 0
        self.stream = self.audio.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=16000,
            input=True,
            input_device_index=self.device_index,
            frames_per_buffer=1024,
            stream_callback=None
        )

    def _is_valid_audio(self, data):
        """检查音频数据是否有效（音量是否足够）"""
        audio_data = np.frombuffer(data, dtype=np.float32)
        # 计算音量（使用RMS值）
        volume = np.sqrt(np.mean(np.square(audio_data)))
        return volume > self.volume_threshold

    def read_audio(self):
        """读取音频数据"""
        if self.stream and self.stream.is_active():
            data = self.stream.read(1024, exception_on_overflow=False)
            # 检查音量
            if self._is_valid_audio(data):
                self.valid_frame_count += 1
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
        
        # 检查是否有足够的有效音频
        if self.valid_frame_count < self.min_valid_frames:
            print(f"❌ 未检测到有效语音（音量过小或噪音）")
            return np.array([], dtype=np.float32)
            
        return data

    def get_audio_data(self):
        """获取录音数据"""
        if not self.frames:
            return np.array([], dtype=np.float32)
            
        audio_data = b"".join(self.frames)
        data = np.frombuffer(audio_data, dtype=np.float32)
        
        # 检查是否有足够的有效音频
        if self.valid_frame_count < self.min_valid_frames:
            print(f"❌ 未检测到有效语音（音量过小或噪音）")
            return np.array([], dtype=np.float32)
            
        return data

    def clear_recording_data(self):
        """清理录音数据"""
        self.frames = []
        self.read_count = 0
        self.valid_frame_count = 0