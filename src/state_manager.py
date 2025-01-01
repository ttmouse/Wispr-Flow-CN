from enum import Enum
import logging
from datetime import datetime
import time

class RecordingState(Enum):
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    ERROR = "error"

class StateManager:
    def __init__(self):
        self._state = RecordingState.IDLE
        self._error = None
        self._last_success_time = None
        self._retry_count = 0
        self.MAX_RETRIES = 3
        self._recording_duration = 0  # 录音持续时间（秒）
        self._recording_dots = 0  # 动态点的数量
        self._last_console_update = 0  # 上次控制台更新时间
        self._last_status = ""  # 上次显示的状态
        
    @property
    def state(self):
        return self._state
        
    @property
    def can_record(self):
        return self._state in [RecordingState.IDLE]
    
    @property
    def recording_status_text(self):
        if self._state == RecordingState.RECORDING:
            dots = "." * ((self._recording_dots % 3) + 1)
            return f"⏺️  录音中 ({self._recording_duration:.1f}秒){dots}"
        elif self._state == RecordingState.PROCESSING:
            return f"⏺️  录音中 ({self._recording_duration:.1f}秒) 完成"
        elif self._state == RecordingState.ERROR:
            return f"❌ {self.get_error_message()}"
        return "准备就绪"
    
    def update_recording_status(self, duration):
        """更新录音状态"""
        self._recording_duration = duration
        self._recording_dots = (self._recording_dots + 1) % 3
        
        # 每100ms更新一次控制台显示
        current_time = time.time()
        if current_time - self._last_console_update >= 0.1:
            if self._state == RecordingState.RECORDING:
                status = self.recording_status_text
                # 只有状态变化时才更新
                if status != self._last_status:
                    # 使用\r清除当前行，使用固定宽度格式化
                    print(f"\r\033[K{status}", end="", flush=True)
                    self._last_status = status
            self._last_console_update = current_time
        
    def transition_to(self, new_state, error=None):
        old_state = self._state
        self._state = new_state
        
        if error:
            self._error = error
            self._retry_count += 1
            logging.error(f"状态转换错误 {old_state} -> {new_state}: {error}")
            # 清除当前行并显示错误状态
            print(f"\r\033[K{self.recording_status_text}")
        else:
            self._error = None
            self._retry_count = 0
            if new_state == RecordingState.IDLE:
                self._last_success_time = datetime.now()
                self._recording_duration = 0
                self._recording_dots = 0
                print()  # 打印一个换行，清理录音状态行
            elif new_state == RecordingState.PROCESSING:
                # 清除当前行并显示录音完成状态
                print(f"\r\033[K{self.recording_status_text}")
                
        return self._retry_count <= self.MAX_RETRIES
        
    def get_error_message(self):
        if self._error:
            return f"{str(self._error)}"
        return None 