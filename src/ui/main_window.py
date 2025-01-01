from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QTextEdit, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent

class MainWindow(QMainWindow):
    record_button_clicked = pyqtSignal()
    pause_button_clicked = pyqtSignal()
    space_key_pressed = pyqtSignal()  # 新增信号

    def __init__(self):
        super().__init__()
        self.setWindowTitle("语音转文字")
        self.setGeometry(100, 100, 400, 300)

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

    def update_status(self, status):
        self.status_label.setText(status)

    def display_result(self, result):
        self.result_text.setText(result)

    def set_recording_state(self, is_recording):
        if is_recording:
            self.record_button.setText("停止录音")
            self.pause_button.setEnabled(True)
        else:
            self.record_button.setText("开始录音")
            self.pause_button.setEnabled(False)
            self.pause_button.setText("暂停录音")

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
        print("MainWindow: 窗口获得焦点")
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        print("MainWindow: 窗口失去焦点")
        super().focusOutEvent(event)