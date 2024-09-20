import pyaudio
import numpy as np
import time

class AudioCapture:
    def __init__(self, sample_rate=16000, chunk_size=1024):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.start_time = None
        self.total_read = 0

    def start_recording(self):
        # 列出所有可用的音频输入设备
        info = self.p.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        for i in range(0, numdevices):
            if (self.p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                print(f"Input Device id {i} - {self.p.get_device_info_by_host_api_device_index(0, i).get('name')}")

        # 使用默认输入设备
        default_input_device_index = self.p.get_default_input_device_info()['index']
        print(f"使用默认输入设备: {self.p.get_device_info_by_index(default_input_device_index)['name']}")

        try:
            self.stream = self.p.open(format=pyaudio.paInt16,
                                      channels=1,
                                      rate=self.sample_rate,
                                      input=True,
                                      input_device_index=default_input_device_index,
                                      frames_per_buffer=self.chunk_size)
            self.frames = []
            self.start_time = time.time()
            self.total_read = 0
            print("开始录音...")
        except Exception as e:
            print(f"打开音频流时出错: {e}")

    def stop_recording(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        audio_data = np.concatenate(self.frames) if self.frames else np.array([], dtype=np.float32)
        
        if self.start_time is not None:
            duration = time.time() - self.start_time
            print(f"录音结束，捕获的音频数据总长度：{len(audio_data)}，录音时长：{duration:.2f}秒，总读取次数：{len(self.frames)}")
        else:
            print("录音结束，但没有捕获到音频数据")
        
        return audio_data

    def clear_recording_data(self):
        self.frames = []
        self.total_read = 0
        self.start_time = None
        print("录音数据已清理")

    def __del__(self):
        if self.stream:
            self.stream.close()
        self.p.terminate()

    def read_audio(self):
        try:
            data = self.stream.read(self.chunk_size, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0  # 转换为float32并归一化
            self.frames.append(audio_data)
            self.total_read += len(audio_data)
            if len(self.frames) % 10 == 0:
                print(f"已读取音频数据，当前总长度：{self.total_read}，帧数：{len(self.frames)}")
            return audio_data
        except Exception as e:
            print(f"读取音频数据时出错: {e}")
            return np.array([], dtype=np.float32)

    def get_audio_data(self):
        return np.concatenate(self.frames) if self.frames else np.array([], dtype=np.float32)