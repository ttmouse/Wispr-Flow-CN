from PyQt6.QtCore import QThread, pyqtSignal
import time
import threading

class AudioCaptureThread(QThread):
    """音频捕获线程 - 优化信号发射策略"""
    audio_captured = pyqtSignal(object)
    recording_stopped = pyqtSignal()  # 新增信号用于通知录音停止

    def __init__(self, audio_capture):
        super().__init__()
        self.audio_capture = audio_capture
        self.is_recording = False
        self._stop_event = threading.Event()

    def run(self):
        """改进的运行方法，减少信号发射频率避免死锁"""
        self.is_recording = True
        self.audio_capture.start_recording()
        
        audio_buffer = []
        last_emit_time = time.time()
        
        while self.is_recording and not self._stop_event.is_set():
            try:
                data = self.audio_capture.read_audio()
                if data is None:  # 检测到需要停止录音
                    self.is_recording = False
                    break
                    
                if len(data) > 0:
                    audio_buffer.append(data)
                    
                    # 批量发射信号，减少频率避免死锁
                    current_time = time.time()
                    if current_time - last_emit_time > 0.1:  # 100ms间隔
                        if audio_buffer:
                            combined_data = b''.join(audio_buffer)
                            self.audio_captured.emit(combined_data)
                            audio_buffer.clear()
                            last_emit_time = current_time
                            
            except Exception as e:
                import logging
                logging.error(f"音频捕获错误: {e}")
                break
        
        # 最终清理和发送剩余数据
        try:
            final_data = self.audio_capture.stop_recording()
            
            if final_data is not None and len(final_data) > 0:
                self.audio_captured.emit(final_data)
            elif audio_buffer:  # 发送缓冲区中的剩余数据
                combined_data = b''.join(audio_buffer)
                self.audio_captured.emit(combined_data)
                
            if not self.is_recording:  # 如果是自动停止，发送信号
                self.recording_stopped.emit()
        except Exception as e:
            import logging
            logging.error(f"音频停止清理错误: {e}")
            # 确保即使出错也发送停止信号
            try:
                if not self.is_recording:
                    self.recording_stopped.emit()
            except:
                pass

    def stop(self):
        """改进的停止方法，避免死锁"""
        self.is_recording = False
        self._stop_event.set()
        # 不要在这里调用wait()，避免死锁

class TranscriptionThread(QThread):
    """转写线程"""
    transcription_done = pyqtSignal(str)

    def __init__(self, audio_data, funasr_engine):
        super().__init__()
        self.audio_data = audio_data
        self.funasr_engine = funasr_engine

    def run(self):
        try:
            result = self.funasr_engine.transcribe(self.audio_data)
            # 处理 FunASR 返回的结果
            if isinstance(result, list) and len(result) > 0:
                text = result[0].get('text', '')
            elif isinstance(result, dict):
                text = result.get('text', '')
            else:
                text = str(result)
            self.transcription_done.emit(text)
        except Exception as e:
            import logging
            logging.error(f"转写失败: {e}")
            self.transcription_done.emit("转写失败，请重试")