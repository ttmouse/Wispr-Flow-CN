from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QWaitCondition
import time

class AudioCaptureThread(QThread):
    """音频捕获线程"""
    audio_captured = pyqtSignal(object)
    recording_stopped = pyqtSignal()  # 新增信号用于通知录音停止

    def __init__(self, audio_capture):
        super().__init__()
        self.audio_capture = audio_capture
        self.is_recording = False
        self._stop_requested = False
        self._mutex = QMutex()
        self._wait_condition = QWaitCondition()

    def run(self):
        try:
            self.is_recording = True
            self._stop_requested = False
            
            if not self.audio_capture:
                print("❌ 音频捕获对象为空")
                return
                
            self.audio_capture.start_recording()
            
            while not self._stop_requested and self.is_recording:
                try:
                    data = self.audio_capture.read_audio()
                    if data is None:  # 检测到需要停止录音
                        break
                    if len(data) > 0:
                        self.audio_captured.emit(data)
                    
                    # 使用更长的休眠时间来降低CPU使用率
                    time.sleep(0.05)  # 50ms休眠，大幅降低CPU使用率
                    
                    # 检查是否需要停止
                    if self._stop_requested:
                        break
                        
                except Exception as e:
                    print(f"❌ 音频读取错误: {e}")
                    break
            
            # 安全地停止录音
            try:
                audio_data = self.audio_capture.stop_recording()
                if audio_data and len(audio_data) > 0:
                    self.audio_captured.emit(audio_data)
            except Exception as e:
                print(f"❌ 停止录音时出错: {e}")
            
            # 发送录音停止信号
            self.recording_stopped.emit()
            
        except Exception as e:
            print(f"❌ 音频捕获线程运行错误: {e}")
        finally:
            self.is_recording = False
            self._stop_requested = True

    def stop(self):
        """安全停止线程"""
        self._mutex.lock()
        try:
            self._stop_requested = True
            self.is_recording = False
            self._wait_condition.wakeAll()
        finally:
            self._mutex.unlock()
        
        # 等待线程结束，但设置超时避免无限等待
        if not self.wait(3000):  # 等待3秒
            print("⚠️ 音频捕获线程未能在3秒内正常结束，强制终止")
            self.terminate()
            self.wait(1000)  # 再等待1秒确保终止

class TranscriptionThread(QThread):
    """转写线程"""
    transcription_done = pyqtSignal(str)

    def __init__(self, audio_data, funasr_engine):
        super().__init__()
        self.audio_data = audio_data
        self.funasr_engine = funasr_engine
        self._stop_requested = False
        self._mutex = QMutex()

    def run(self):
        try:
            # 检查是否已请求停止
            if self._stop_requested:
                return
                
            # 检查引擎是否可用
            if not self.funasr_engine:
                print("❌ FunASR引擎不可用")
                self.transcription_done.emit("引擎不可用")
                return
                
            # 检查音频数据是否有效
            if not self.audio_data or len(self.audio_data) == 0:
                print("❌ 音频数据为空")
                self.transcription_done.emit("音频数据为空")
                return
            
            print(f"开始转写，音频数据长度: {len(self.audio_data)}")
            result = self.funasr_engine.transcribe(self.audio_data)
            
            # 再次检查是否已请求停止
            if self._stop_requested:
                return
                
            # 处理 FunASR 返回的结果
            if isinstance(result, list) and len(result) > 0:
                text = result[0].get('text', '')
            elif isinstance(result, dict):
                text = result.get('text', '')
            else:
                text = str(result) if result else ''
                
            print(f"转写结果: {text}")
            
            # 最后检查是否已请求停止
            if not self._stop_requested:
                self.transcription_done.emit(text)
                
        except Exception as e:
            print(f"❌ 转写失败: {e}")
            import traceback
            print(traceback.format_exc())
            if not self._stop_requested:
                self.transcription_done.emit("转写失败，请重试")
        finally:
            # 确保线程能够正常结束
            print("转写线程结束")

    def stop(self):
        """安全停止转写线程"""
        self._mutex.lock()
        try:
            self._stop_requested = True
            print("请求停止转写线程")
        finally:
            self._mutex.unlock()
        
        # 等待线程结束，设置超时避免无限等待
        if not self.wait(5000):  # 等待5秒
            print("⚠️ 转写线程未能在5秒内正常结束，强制终止")
            self.terminate()
            self.wait(1000)  # 再等待1秒确保终止