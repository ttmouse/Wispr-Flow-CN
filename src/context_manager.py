from datetime import datetime

class Context:
    """
    上下文管理器
    用于记录程序的当前状态和最后一次操作
    """
    def __init__(self):
        self.last_action = None
        self.last_action_time = None
        self.error_message = None
        self.has_error = False
        # 新增状态字段
        self.recording_state = "idle"  # idle, recording, processing
        self.recording_duration = 0
        self.audio_data_size = 0
        self.transcription_state = "idle"  # idle, transcribing, completed
        self.transcription_result = None
        self.retry_count = 0
        
    def record_action(self, action):
        """记录最后一次操作"""
        self.last_action = action
        self.last_action_time = datetime.now()
        
    def record_error(self, error_message):
        """记录错误信息"""
        self.error_message = error_message
        self.has_error = True
        self.retry_count += 1
        
    def clear_error(self):
        """清除错误信息"""
        self.error_message = None
        self.has_error = False
        self.retry_count = 0
        
    def set_recording_state(self, state, duration=None, data_size=None):
        self.recording_state = state
        if duration is not None:
            self.recording_duration = duration
        if data_size is not None:
            self.audio_data_size = data_size
        
    def set_transcription_state(self, state, result=None):
        self.transcription_state = state
        if result is not None:
            self.transcription_result = result
        
    def get_status(self):
        """获取当前状态信息"""
        return {
            "last_action": self.last_action,
            "last_action_time": self.last_action_time,
            "has_error": self.has_error,
            "error_message": self.error_message,
            "recording_state": self.recording_state,
            "recording_duration": self.recording_duration,
            "audio_data_size": self.audio_data_size,
            "transcription_state": self.transcription_state,
            "transcription_result": self.transcription_result,
            "retry_count": self.retry_count
        } 

    def reset(self):
        self.__init__() 