from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
                            QLabel, QTextEdit, QPushButton, QListWidget, QListWidgetItem,
                            QSplitter)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QMetaObject, Q_ARG, pyqtSlot
from PyQt6.QtGui import QKeyEvent, QFont
import time

class HistoryItem(QListWidgetItem):
    def __init__(self, text, timestamp):
        super().__init__()
        self.text = text
        self.timestamp = timestamp
        self.update_display()
        
    def update_display(self):
        time_str = time.strftime("%H:%M:%S", time.localtime(self.timestamp))
        display_text = f"{time_str}\n{self.text[:50]}..." if len(self.text) > 50 else self.text
        self.setText(display_text)

class MainWindow(QMainWindow):
    record_button_clicked = pyqtSignal()
    pause_button_clicked = pyqtSignal()
    space_key_pressed = pyqtSignal()
    status_update_needed = pyqtSignal()
    start_timer = pyqtSignal()
    stop_timer = pyqtSignal()
    history_item_clicked = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("FunASR 语音转文字")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(600, 400)

        self._recording_start_time = 0
        self._status_timer = None  # 将在 showEvent 中初始化
        
        self.setup_ui()
        
    def showEvent(self, event):
        """窗口显示时初始化定时器"""
        super().showEvent(event)
        if self._status_timer is None:
            self._status_timer = QTimer(self)
            self._status_timer.timeout.connect(self._on_timer)
            self._status_timer.setInterval(100)
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 使用水平分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧面板 - 历史记录
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        history_label = QLabel("历史记录")
        history_label.setFont(QFont("", 14))
        left_layout.addWidget(history_label)
        
        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(self._on_history_item_clicked)
        left_layout.addWidget(self.history_list)
        
        # 右侧面板 - 主要内容
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # 状态面板
        status_panel = QWidget()
        status_layout = QHBoxLayout(status_panel)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setFont(QFont("", 14))
        status_layout.addWidget(self.status_label)
        
        # 录音时长
        self.duration_label = QLabel("")
        self.duration_label.setFont(QFont("", 14))
        status_layout.addWidget(self.duration_label)
        
        right_layout.addWidget(status_panel)
        
        # 结果文本框
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setFont(QFont("", 13))
        right_layout.addWidget(self.result_text)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        self.record_button = QPushButton("开始录音")
        self.record_button.clicked.connect(self.record_button_clicked.emit)
        button_layout.addWidget(self.record_button)
        
        # 暂停按钮（暂时隐藏）
        self.pause_button = QPushButton("暂停录音")
        self.pause_button.clicked.connect(self.pause_button_clicked.emit)
        self.pause_button.setEnabled(False)
        self.pause_button.hide()  # 隐藏暂停按钮
        button_layout.addWidget(self.pause_button)
        
        right_layout.addLayout(button_layout)
        
        # 添加面板到分割器
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        
        # 设置分割器的初始大小
        splitter.setSizes([200, 600])
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.addWidget(splitter)
        
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
    def add_to_history(self, text):
        """添加新的识别结果到历史记录"""
        if text.strip():  # 只添加非空文本
            item = HistoryItem(text, time.time())
            self.history_list.insertItem(0, item)  # 在顶部插入
            # 保持最多10条记录
            while self.history_list.count() > 10:
                self.history_list.takeItem(self.history_list.count() - 1)
    
    def _on_history_item_clicked(self, item):
        """处理历史记录项点击事件"""
        if isinstance(item, HistoryItem):
            self.history_item_clicked.emit(item.text)
    
    def display_result(self, result, add_to_history=True):
        """显示识别结果
        
        Args:
            result: 要显示的文本
            add_to_history: 是否添加到历史记录，默认为True
        """
        self.result_text.setText(result)
        if add_to_history:
            self.add_to_history(result)
    
    def update_status(self, status):
        """更新状态显示"""
        # 分离状态文本和时长信息
        if "录音中" in status and "秒" in status:
            base_status = status[:status.find("(")].strip()
            duration_info = status[status.find("("):].strip()
            self.status_label.setText(base_status)
            self.duration_label.setText(duration_info)
        else:
            self.status_label.setText(status)
            self.duration_label.setText("")
    
    def set_state_manager(self, state_manager):
        """设置状态管理器"""
        self.state_manager = state_manager
        self.update_status(state_manager.recording_status_text)
    
    def set_paused_state(self, is_paused):
        """设置暂停状态"""
        if is_paused:
            self.pause_button.setText("继续录音")
        else:
            self.pause_button.setText("暂停录音")
    
    def keyPressEvent(self, event):
        """处理按键事件"""
        if event.key() == Qt.Key.Key_Space:
            self.space_key_pressed.emit()
        super().keyPressEvent(event)
    
    def _start_timer(self):
        """启动定时器"""
        if self._status_timer:
            self._status_timer.start()
    
    def _stop_timer(self):
        """停止定时器"""
        if self._status_timer:
            self._status_timer.stop()
    
    def _on_timer(self):
        """定时器回调"""
        self.status_update_needed.emit()