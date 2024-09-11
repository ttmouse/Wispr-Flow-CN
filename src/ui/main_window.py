from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QLabel, QPushButton, QWidget, QTextEdit
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import Qt, pyqtSlot

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FunASR 语音转文字")
        self.setGeometry(100, 100, 400, 300)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.status_label = QLabel("就绪")
        layout.addWidget(self.status_label)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        font = QFont("Arial", 12)  # 设置字体和大小
        self.result_text.setFont(font)
        layout.addWidget(self.result_text)

        self.settings_button = QPushButton("设置")
        layout.addWidget(self.settings_button)

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    @pyqtSlot(str)
    def update_status(self, status):
        print(f"更新状态: {status}")  # 添加这行
        self.status_label.setText(status)

    @pyqtSlot(str)
    def display_result(self, result):
        print(f"显示结果: {result[:30]}...")  # 添加这行，只打印结果的前30个字符
        self.result_text.setText(result)
        self.result_text.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)  # 设置文本对齐方式