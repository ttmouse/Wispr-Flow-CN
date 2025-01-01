from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QTextEdit, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QMetaObject, Q_ARG, pyqtSlot
from PyQt6.QtGui import QKeyEvent
import time

class MainWindow(QMainWindow):
    record_button_clicked = pyqtSignal()
    pause_button_clicked = pyqtSignal()
    space_key_pressed = pyqtSignal()
    status_update_needed = pyqtSignal()  # 新增信号用于触发状态更新
    start_timer = pyqtSignal()  # 新增信号用于启动定时器
    stop_timer = pyqtSignal()   # 新增信号用于停止定时器

    def __init__(self):
        super().__init__()
        self.setWindowTitle("语音转文字")
        self.setGeometry(100, 100, 400, 300)

        # 初始化录音开始时间
        self._recording_start_time = 0
        
        # 在主线程中创建定时器
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._on_timer)
        self._status_timer.setInterval(100)
        
        # 连接定时器控制信号
        self.start_timer.connect(self._start_timer)
        self.stop_timer.connect(self._stop_timer)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        self.status_label = QLabel("就绪")
        layout.addWidget(self.status_label)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        layout.addWidget(self.result_text)

        button_layout = QHBoxLayout()
        
        self.record_button = QPushButton("开始录音")
        self.record_button.clicked.connect(self.record_button_clicked.emit)
        button_layout.addWidget(self.record_button)

        self.pause_button = QPushButton("暂停录音")
        self.pause_button.clicked.connect(self.pause_button_clicked.emit)
        self.pause_button.setEnabled(False)
        button_layout.addWidget(self.pause_button)

        layout.addLayout(button_layout)

        # 设置窗口接收键盘焦点
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # 连接状态更新信号
        self.status_update_needed.connect(self._update_recording_status)

    def set_recording_state(self, is_recording):
        if is_recording:
            self.record_button.setText("停止录音")
            self.pause_button.setEnabled(True)
            self._recording_start_time = time.time()
            self.start_timer.emit()  # 通过信号启动定时器
        else:
            self.record_button.setText("开始录音")
            self.pause_button.setEnabled(False)
            self.pause_button.setText("暂停录音")
            self.stop_timer.emit()   # 通过信号停止定时器

    @pyqtSlot()
    def _start_timer(self):
        """在主线程中启动定时器"""
        if not self._status_timer.isActive():
            self._status_timer.start()

    @pyqtSlot()
    def _stop_timer(self):
        """在主线程中停止定时器"""
        if self._status_timer.isActive():
            self._status_timer.stop()

    @pyqtSlot()
    def _on_timer(self):
        """定时器回调，在主线程中触发状态更新"""
        self.status_update_needed.emit()

    @pyqtSlot()
    def _update_recording_status(self):
        """在主线程中更新录音状态显示"""
        if hasattr(self, 'state_manager'):
            duration = time.time() - self._recording_start_time
            self.state_manager.update_recording_status(duration)
            self.update_status(self.state_manager.recording_status_text)

    def update_status(self, status):
        """在主线程中更新UI"""
        self.status_label.setText(status)

    def display_result(self, result):
        """在主线程中更新UI"""
        self.result_text.setText(result)

    def set_state_manager(self, state_manager):
        """设置状态管理器"""
        self.state_manager = state_manager
        self.update_status(state_manager.recording_status_text)

    def set_paused_state(self, is_paused):
        if is_paused:
            self.pause_button.setText("继续录音")
        else:
            self.pause_button.setText("暂停录音")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self.space_key_pressed.emit()
        super().keyPressEvent(event)

    def focusInEvent(self, event):
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)