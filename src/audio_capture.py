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
        self.volume_threshold = 0.005  # 降低音量阈值，使其更容易捕获语音
        self.min_valid_frames = 3      # 降低最少有效帧数要求（约0.2秒）
        self.valid_frame_count = 0     # 有效音频帧计数
        self.max_silence_frames = 30    # 最大连续静音帧数（约1.8秒）
        self.silence_frame_count = 0    # 连续静音帧计数
        self.frame_window = []         # 用于计算移动平均的窗口
        self.window_size = 5           # 增加窗口大小，使音量判断更平滑
        
    def _get_default_mic_index(self):
        default_device = self.audio.get_default_input_device_info()
        print(f"使用默认麦克风: {default_device['name']}")
        return default_device['index']

    def start_recording(self):
        """开始录音"""
        self.frames = []
        self.read_count = 0
        self.valid_frame_count = 0
        self.silence_frame_count = 0
        self.frame_window = []  # 清空窗口
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
        
        # 使用移动平均来平滑音量判断
        self.frame_window.append(volume)
        if len(self.frame_window) > self.window_size:
            self.frame_window.pop(0)
        avg_volume = np.mean(self.frame_window)
        
        # 如果窗口还没满，使用当前音量判断
        if len(self.frame_window) < self.window_size:
            is_valid = volume > self.volume_threshold
        else:
            is_valid = avg_volume > self.volume_threshold
        
        # 更新静音计数
        if is_valid:
            self.silence_frame_count = 0
            self.valid_frame_count += 1  # 只在这里计数一次
        else:
            self.silence_frame_count += 1
            
        return is_valid

    def read_audio(self):
        """读取音频数据"""
        if self.stream and self.stream.is_active():
            try:
                data = self.stream.read(1024, exception_on_overflow=False)
                # 检查音量并更新状态
                is_valid = self._is_valid_audio(data)
                self.frames.append(data)
                self.read_count += 1
                
                # 如果静音时间太长，自动停止录音
                if self.silence_frame_count >= self.max_silence_frames:
                    return None  # 返回None表示需要停止录音
                    
                return data
            except Exception as e:
                print(f"读取音频时出错: {e}")
                return b""
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
            # print(f"❌ 未检测到有效语音（音量过小或噪音）")
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
            print(f"❌ 未检测到有效语音（有效帧数：{self.valid_frame_count}，需要：{self.min_valid_frames}）")
            return np.array([], dtype=np.float32)
            
        return data

    def clear_recording_data(self):
        """清理录音数据"""
        self.frames = []
        self.read_count = 0
        self.valid_frame_count = 0