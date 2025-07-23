import pyaudio
import numpy as np
import time
import collections

class AudioCapture:
    def __init__(self):
        # 使用deque限制缓冲区大小，避免内存累积
        self.frames = collections.deque(maxlen=1000)  # 限制最大帧数
        self.stream = None
        self.audio = None
        self.device_index = None
        self.read_count = 0
        # 音量相关参数
        self.volume_threshold = 0.001  # 降低默认阈值提高敏感度
        self.min_valid_frames = 2      # 降低最少有效帧数要求（约0.13秒）
        self.valid_frame_count = 0     # 有效音频帧计数
        self.max_silence_frames = 50   # 增加最大静音帧数到约2秒
        self.silence_frame_count = 0   # 连续静音帧计数
        self.debug_frame_count = 0     # 调试帧计数
        
        # 初始化音频系统
        self._initialize_audio()
        
    def _initialize_audio(self):
        """初始化音频系统"""
        try:
            if self.audio is not None:
                self.audio.terminate()
            self.audio = pyaudio.PyAudio()
            self.device_index = self._get_default_mic_index()
        except Exception as e:
            import logging
            logging.error(f"初始化音频系统失败: {e}")
            self.audio = None
            self.device_index = None
        
    def _get_default_mic_index(self):
        """获取默认麦克风索引"""
        try:
            default_device = self.audio.get_default_input_device_info()
            return default_device['index']
        except Exception as e:
            import logging
            logging.error(f"获取默认麦克风失败: {e}")
            return None

    def start_recording(self):
        """开始录音"""
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                # 确保之前的录音已经停止
                self.stop_recording()
                
                # 重新初始化音频系统
                if self.audio is None:
                    self._initialize_audio()
                
                if self.audio is None or self.device_index is None:
                    raise Exception("音频系统未正确初始化")
                
                self.frames.clear()
                self.read_count = 0
                self.valid_frame_count = 0
                self.silence_frame_count = 0
                self.debug_frame_count = 0
                
                self.stream = self.audio.open(
                    format=pyaudio.paFloat32,
                    channels=1,
                    rate=16000,
                    input=True,
                    input_device_index=self.device_index,
                    frames_per_buffer=512,  # 减小缓冲区大小以降低延迟
                    stream_callback=None
                )
                return
            except Exception as e:
                retry_count += 1
                import logging
                logging.error(f"尝试 {retry_count}/{max_retries} 启动录音失败: {e}")
                self._cleanup()
                time.sleep(0.5)  # 等待系统资源释放
        
        raise Exception(f"在 {max_retries} 次尝试后仍无法启动录音")

    def stop_recording(self):
        """停止录音"""
        if not self.stream:
            return np.array([], dtype=np.float32)

        try:
            if self.stream and self.stream.is_active():
                self.stream.stop_stream()
            if self.stream:
                self.stream.close()
        except Exception as e:
            import logging
            logging.error(f"停止录音失败: {e}")
            # 强制重新初始化音频系统
            self._cleanup()
            self._initialize_audio()
        finally:
            self.stream = None
            
        try:
            audio_data = b"".join(self.frames)
            
            # 确保音频数据不为空
            if len(audio_data) == 0:
                return np.array([], dtype=np.float32)
                
            data = np.frombuffer(audio_data, dtype=np.float32)
            
            # 检查是否有足够的有效音频
            # 确保使用标量值进行比较，避免NumPy数组比较错误
            try:
                # 强制转换为Python标量类型，避免NumPy数组比较
                if hasattr(self.valid_frame_count, 'item'):
                    valid_count = int(self.valid_frame_count.item())
                elif hasattr(self.valid_frame_count, '__len__'):
                    valid_count = int(self.valid_frame_count)
                else:
                    valid_count = int(self.valid_frame_count)
                    
                if hasattr(self.min_valid_frames, 'item'):
                    min_valid = int(self.min_valid_frames.item())
                elif hasattr(self.min_valid_frames, '__len__'):
                    min_valid = int(self.min_valid_frames)
                else:
                    min_valid = int(self.min_valid_frames)
                    
                # 使用Python标量进行比较
                if valid_count < min_valid:
                    return np.array([], dtype=np.float32)
            except Exception as e:
                # 如果比较失败，返回原始数据
                pass
                
            return data
            
        except Exception as e:
            import logging
            logging.error(f"stop_recording处理音频数据时出错: {e}")
            return np.array([], dtype=np.float32)

    def _cleanup(self):
        """清理音频资源"""
        # 清理音频流
        if self.stream:
            try:
                if hasattr(self.stream, 'is_active') and self.stream.is_active():
                    self.stream.stop_stream()
                if hasattr(self.stream, 'close'):
                    self.stream.close()
            except Exception as e:
                import logging
                logging.error(f"清理音频流失败: {e}")
            finally:
                self.stream = None
            
        # 清理PyAudio实例
        if self.audio:
            try:
                # 确保所有流都已关闭
                if hasattr(self.audio, 'get_device_count'):
                    # 检查是否还有活跃的流
                    pass
                
                # 终止PyAudio
                if hasattr(self.audio, 'terminate'):
                    self.audio.terminate()
                    
            except Exception as e:
                import logging
                logging.error(f"清理音频系统失败: {e}")
            finally:
                self.audio = None
                # 给系统更多时间释放音频资源
                time.sleep(0.5)
        
        # 清理数据，确保计数器为标量值
        self.frames.clear()  # 使用deque的clear方法
        self.read_count = 0
        self.valid_frame_count = 0
        self.silence_frame_count = 0
        self.debug_frame_count = 0
        
        # 强制垃圾回收
        import gc
        gc.collect()

    def cleanup(self):
        """公共清理方法，供外部调用"""
        try:
            self._cleanup()
        except Exception as e:
            import logging
            logging.error(f"清理音频捕获资源失败: {e}")
    
    def __del__(self):
        """析构函数，确保资源被正确释放"""
        try:
            self._cleanup()
        except Exception as e:
            import logging
            logging.error(f"析构时清理资源失败: {e}")

    def set_device(self, device_name=None):
        """设置音频输入设备"""
        try:
            # 停止当前录音
            self.stop_recording()
            
            # 重新初始化音频系统
            self._initialize_audio()
            
            if device_name is None or device_name == "系统默认":
                self.device_index = self._get_default_mic_index()
                return True
                
            # 查找指定设备
            for i in range(self.audio.get_device_count()):
                device_info = self.audio.get_device_info_by_index(i)
                if (device_info['maxInputChannels'] > 0 and 
                    device_info['name'] == device_name):
                    self.device_index = i
                    return True
                    
            return False
            
        except Exception as e:
            import logging
            logging.error(f"设置音频设备失败: {e}")
            return False

    def _is_valid_audio(self, data):
        """检查音频数据是否有效（音量是否足够）"""
        audio_data = np.frombuffer(data, dtype=np.float32)
        # 直接使用RMS值判断，不使用移动平均
        volume = float(np.sqrt(np.mean(np.square(audio_data))))
        # 使用Python标量进行比较，避免NumPy数组比较错误
        is_valid = bool(volume > self.volume_threshold)
        
        # 更新调试计数器
        self.debug_frame_count += 1
        
        # 更新计数，确保计数器始终为标量值
        if is_valid:
            self.silence_frame_count = 0
            self.valid_frame_count = int(self.valid_frame_count) + 1
        else:
            self.silence_frame_count = int(self.silence_frame_count) + 1
            
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
                # 确保使用标量值进行比较，避免NumPy数组比较错误
                try:
                    # 强制转换为Python标量类型，避免NumPy数组比较
                    if hasattr(self.silence_frame_count, 'item'):
                        silence_count = self.silence_frame_count.item()
                    elif hasattr(self.silence_frame_count, '__len__'):
                        silence_count = int(self.silence_frame_count)
                    else:
                        silence_count = int(self.silence_frame_count)
                        
                    if hasattr(self.max_silence_frames, 'item'):
                        max_silence = self.max_silence_frames.item()
                    elif hasattr(self.max_silence_frames, '__len__'):
                        max_silence = int(self.max_silence_frames)
                    else:
                        max_silence = int(self.max_silence_frames)
                        
                    # 使用Python标量进行比较
                    if silence_count >= max_silence:
                        return None  # 返回None表示需要停止录音
                except Exception as e:
                    import logging
                    logging.error(f"静音检测比较时出错: {e}")
                    # 如果比较失败，继续录音
                    pass
                    
                return data
            except Exception as e:
                import logging
                logging.error(f"读取音频时出错: {e}")
                return b""
        return b""

    def get_audio_data(self):
        """获取录音数据"""
        if not self.frames:
            return np.array([], dtype=np.float32)
            
        audio_data = b"".join(self.frames)
        data = np.frombuffer(audio_data, dtype=np.float32)
        
        # 检查是否有足够的有效音频
        # 确保使用标量值进行比较，避免NumPy数组比较错误
        try:
            # 强制转换为Python标量类型，避免NumPy数组比较
            if hasattr(self.valid_frame_count, 'item'):
                valid_count = self.valid_frame_count.item()
            elif hasattr(self.valid_frame_count, '__len__'):
                valid_count = int(self.valid_frame_count)
            else:
                valid_count = int(self.valid_frame_count)
                
            if hasattr(self.min_valid_frames, 'item'):
                min_valid = self.min_valid_frames.item()
            elif hasattr(self.min_valid_frames, '__len__'):
                min_valid = int(self.min_valid_frames)
            else:
                min_valid = int(self.min_valid_frames)
                
            # 使用Python标量进行比较
            if valid_count < min_valid:
                return np.array([], dtype=np.float32)
        except Exception as e:
            import logging
            logging.error(f"音频数据检查时出错: {e}")
            # 如果比较失败，返回原始数据
            pass
            
        return data

    def clear_recording_data(self):
        """清理录音数据"""
        self.frames.clear()
        self.read_count = 0
        self.valid_frame_count = 0
        self.silence_frame_count = 0
        self.debug_frame_count = 0
        
    def clear_buffer(self):
        """手动清理缓冲区"""
        self.frames.clear()

    def set_volume_threshold(self, threshold):
        """设置音量阈值（0-1000的值会被转换为0-0.02的浮点数）"""
        self.volume_threshold = (threshold / 1000.0) * 0.02