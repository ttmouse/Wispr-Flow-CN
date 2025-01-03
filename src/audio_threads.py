from PyQt6.QtCore import QThread, pyqtSignal

class AudioCaptureThread(QThread):
    """音频捕获线程"""
    audio_captured = pyqtSignal(object)
    recording_stopped = pyqtSignal()  # 新增信号用于通知录音停止

    def __init__(self, audio_capture):
        super().__init__()
        self.audio_capture = audio_capture
        self.is_recording = False

    def run(self):
        self.is_recording = True
        self.audio_capture.start_recording()
        while self.is_recording:
            data = self.audio_capture.read_audio()
            if data is None:  # 检测到需要停止录音
                self.is_recording = False
                break
            if len(data) > 0:
                self.audio_captured.emit(data)
        audio_data = self.audio_capture.stop_recording()
        self.audio_captured.emit(audio_data)
        if not self.is_recording:  # 如果是自动停止，发送信号
            self.recording_stopped.emit()

    def stop(self):
        self.is_recording = False

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
            print(f"❌ 转写失败: {e}")
            self.transcription_done.emit("转写失败，请重试") 