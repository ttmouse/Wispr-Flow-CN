from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
                            QLabel, QTextEdit, QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from .components import ModernButton, ModernListWidget, HistoryItem
import time

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
        self.setWindowTitle("音频转文本")
        self.setGeometry(100, 100, 400, 600)
        self.setMinimumSize(400, 400)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: white;
            }
            QLabel {
                color: #1D1D1F;
            }
        """)

        self._recording_start_time = 0
        self._status_timer = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI布局"""
        self.setup_central_widget()
        self.setup_title_bar()
        self.setup_history_section()
        self.setup_bottom_section()
        self.setup_hidden_components()
        
    def setup_central_widget(self):
        """设置中央部件"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
    def setup_title_bar(self):
        """设置标题栏"""
        title_bar = QWidget()
        title_bar.setStyleSheet("background-color: black; color: white;")
        title_bar.setFixedHeight(58)
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(20, 0, 20, 0)
        
        title_label = QLabel("音频转文本")
        title_label.setFont(QFont("", 16))
        title_label.setStyleSheet("color: white;")
        title_layout.addWidget(title_label)
        
        self.main_layout.addWidget(title_bar)
        
    def setup_history_section(self):
        """设置历史记录部分"""
        recent_label = QLabel("最近记录")
        recent_label.setFont(QFont("", 14))
        recent_label.setContentsMargins(20, 20, 20, 10)
        self.main_layout.addWidget(recent_label)
        
        self.history_list = ModernListWidget()
        self.history_list.itemClicked.connect(self._on_history_item_clicked)
        self.main_layout.addWidget(self.history_list)
        
    def setup_bottom_section(self):
        """设置底部录音按钮区域"""
        bottom_area = QWidget()
        bottom_area.setFixedHeight(120)
        bottom_layout = QVBoxLayout(bottom_area)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        self.setup_record_button(bottom_layout)
        self.main_layout.addWidget(bottom_area)
        
    def setup_record_button(self, parent_layout):
        """设置录音按钮"""
        self.record_button = QPushButton()
        self.record_button.setFixedSize(64, 64)
        self.record_button.setStyleSheet("""
            QPushButton {
                background-color: black;
                border-radius: 32px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1a1a1a;
            }
            QPushButton:pressed {
                background-color: #333333;
            }
        """)
        
        # 麦克风图标容器
        icon_container = QWidget(self.record_button)
        icon_container.setFixedSize(64, 64)
        icon_layout = QHBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setSpacing(0)
        
        mic_icon = QLabel()
        mic_icon.setFixedSize(24, 24)
        mic_icon.setStyleSheet("""
            QLabel {
                image: url(resources/mic.png);
                padding: 0;
                background: transparent;
            }
        """)
        icon_layout.addWidget(mic_icon, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.record_button.clicked.connect(self.record_button_clicked.emit)
        parent_layout.addWidget(self.record_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
    def setup_hidden_components(self):
        """设置隐藏的组件"""
        self.result_text = QTextEdit()
        self.result_text.hide()
        
        self.pause_button = QPushButton()
        self.pause_button.hide()
        
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def add_to_history(self, text):
        """添加新的识别结果到历史记录"""
        if text.strip():
            item = HistoryItem(text, time.time())
            self.history_list.insertItem(0, item)
            while self.history_list.count() > 10:
                self.history_list.takeItem(self.history_list.count() - 1)
    
    def _on_history_item_clicked(self, item):
        """处理历史记录项点击事件"""
        if isinstance(item, HistoryItem):
            self.history_item_clicked.emit(item.text)
    
    def display_result(self, result, add_to_history=True):
        """显示识别结果"""
        self.result_text.setText(result)
        if add_to_history:
            self.add_to_history(result)
    
    def update_status(self, status):
        """更新状态显示"""
        pass
    
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