from enum import Enum
import logging
from datetime import datetime

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
        
    @property
    def state(self):
        return self._state
        
    @property
    def can_record(self):
        return self._state in [RecordingState.IDLE]
        
    def transition_to(self, new_state, error=None):
        old_state = self._state
        self._state = new_state
        
        if error:
            self._error = error
            self._retry_count += 1
            logging.error(f"状态转换错误 {old_state} -> {new_state}: {error}")
        else:
            self._error = None
            self._retry_count = 0
            if new_state == RecordingState.IDLE:
                self._last_success_time = datetime.now()
                
        return self._retry_count <= self.MAX_RETRIES
        
    def get_error_message(self):
        if self._error:
            return f"错误: {str(self._error)}"
        return None 