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
    
    def set_system_volume(self, volume):
        """设置系统音量 - 从Application类移过来
        volume: 0-100 的整数，或者 None 表示静音"""
        import subprocess
        import logging
        try:
            if volume is None:
                # 直接静音，不检查当前状态以减少延迟
                subprocess.run([
                    'osascript',
                    '-e', 'set volume output muted true'
                ], check=True)
            else:
                # 设置音量并取消静音
                volume = max(0, min(100, volume))  # 确保音量在 0-100 范围内
                subprocess.run([
                    'osascript',
                    '-e', f'set volume output volume {volume}',
                    '-e', 'set volume output muted false'
                ], check=True)
        except subprocess.CalledProcessError as e:
            logging.error(f"设置系统音量失败: {e}")
        except Exception as e:
            logging.error(f"设置系统音量时发生错误: {e}")

    def get_system_volume(self):
        """获取当前系统音量 - 从Application类移过来"""
        import subprocess
        import logging
        try:
            # 获取完整的音量设置
            result = subprocess.run([
                'osascript',
                '-e', 'get volume settings'
            ], capture_output=True, text=True, check=True)

            settings = result.stdout.strip()
            # 解析输出，格式类似：output volume:50, input volume:75, alert volume:75, output muted:false
            volume_str = settings.split(',')[0].split(':')[1].strip()
            muted = "output muted:true" in settings

            if muted:
                return 0

            volume = int(volume_str)
            return volume
        except subprocess.CalledProcessError as e:
            logging.error(f"获取系统音量失败: {e}")
            return None
        except Exception as e:
            logging.error(f"获取系统音量时发生错误: {e}")
            return None

    def restore_volume_async(self, volume):
        """异步恢复音量 - 从Application类移过来"""
        import logging
        try:
            self.set_system_volume(volume)
        except Exception as e:
            logging.error(f"异步恢复音量失败: {e}")

    def start_recording_process(self, state_manager, audio_capture_thread, settings_manager, recording_timer_callback):
        """开始录音流程 - 从Application类移过来"""
        import logging
        try:
            # 先播放音效，让用户立即听到反馈
            state_manager.start_recording()

            # 然后保存当前音量并静音系统
            previous_volume = self.get_system_volume()
            if previous_volume is not None:
                self.set_system_volume(None)  # 静音

            # 初始化或重新初始化录音线程
            if audio_capture_thread is None or audio_capture_thread.isFinished():
                from audio_threads import AudioCaptureThread
                audio_capture_thread = AudioCaptureThread(self._original_capture)
                # 返回新线程，让外部重新连接信号

            # 启动录音线程
            audio_capture_thread.start()

            # 设置录音定时器
            max_duration = settings_manager.get_setting('audio.max_recording_duration', 10)
            recording_timer_callback(max_duration * 1000)  # 转换为毫秒

            return previous_volume, audio_capture_thread

        except Exception as e:
            error_msg = f"开始录音时出错: {str(e)}"
            logging.error(error_msg)
            raise Exception(error_msg)

    def stop_recording_process(self, state_manager, audio_capture_thread, previous_volume, volume_timer_callback):
        """停止录音流程 - 从Application类移过来"""
        import logging
        try:
            # 检查录音线程是否存在
            if audio_capture_thread:
                audio_capture_thread.stop()
                audio_capture_thread.wait()

            # 播放停止音效（先播放音效，再恢复音量）
            state_manager.stop_recording()

            # 异步恢复音量，避免阻塞主线程
            if previous_volume is not None:
                # 使用回调延迟恢复音量，确保音效播放完成
                volume_timer_callback(previous_volume, 150)  # 150ms后恢复音量

            # 获取录音数据
            self._ensure_initialized()
            audio_data = self._original_capture.get_audio_data()
            return audio_data

        except Exception as e:
            logging.error(f"停止录音失败: {e}")
            # 返回空数据而不是抛出异常
            return []

    def get_status(self):
        """获取状态信息"""
        return {
            'name': 'AudioManagerWrapper',
            'initialized': self._initialized,
            'has_original_capture': self._original_capture is not None
        }
    
    def get_audio_devices(self):
        """获取系统中所有可用的音频输入设备"""
        try:
            self._ensure_initialized()
            if self._original_capture and hasattr(self._original_capture, 'get_audio_devices'):
                return self._original_capture.get_audio_devices()
            
            # 如果原始类没有这个方法，直接使用pyaudio获取
            import pyaudio
            devices = []
            
            # 获取默认输入设备信息
            try:
                default_device = self._original_capture.audio.get_default_input_device_info()
                default_name = default_device['name']
                devices.append({'name': f"系统默认 ({default_name})", 'index': default_device['index']})
            except Exception as e:
                self.logger.error(f"获取默认设备失败: {e}")
                devices.append({'name': "系统默认", 'index': None})
            
            # 获取所有设备信息
            for i in range(self._original_capture.audio.get_device_count()):
                try:
                    device_info = self._original_capture.audio.get_device_info_by_index(i)
                    # 只添加输入设备（maxInputChannels > 0）
                    if device_info['maxInputChannels'] > 0:
                        name = device_info['name']
                        # 避免重复添加默认设备
                        if not any(dev['name'] == f"系统默认 ({name})" for dev in devices):
                            devices.append({'name': name, 'index': i})
                except Exception as e:
                    self.logger.error(f"获取设备 {i} 信息失败: {e}")
                    continue
                    
            return devices
            
        except Exception as e:
            self.logger.error(f"获取音频设备列表失败: {e}")
            # 返回至少一个默认选项
            return [{'name': "系统默认", 'index': None}]
