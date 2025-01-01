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
        
        # 设置窗口标志
        self.setWindowFlags(Qt.WindowType.Window |  # 确保是独立窗口
                          Qt.WindowType.FramelessWindowHint)  # 无边框
        
        # 设置窗口保持在最前
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        
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
        
        # 添加鼠标事件追踪
        title_bar.mousePressEvent = self._on_title_bar_mouse_press
        title_bar.mouseMoveEvent = self._on_title_bar_mouse_move
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(20, 0, 20, 0)
        
        # 标题文本
        title_label = QLabel("音频转文本")
        title_label.setFont(QFont("", 16))
        title_label.setStyleSheet("color: white;")
        title_layout.addWidget(title_label)
        
        # 添加关闭按钮
        close_button = QPushButton("×")
        close_button.setFixedSize(20, 20)
        close_button.setFont(QFont("", 16))
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.setStyleSheet("""
            QPushButton {
                border: none;
                color: #999999;
                background: transparent;
            }
            QPushButton:hover {
                color: white;
            }
            QPushButton:pressed {
                color: #666666;
            }
        """)
        close_button.clicked.connect(self.close)
        title_layout.addWidget(close_button)
        
        self.main_layout.addWidget(title_bar)
        
        # 保存拖动相关的状态
        self._is_dragging = False
        self._drag_start_pos = None
        
    def _on_title_bar_mouse_press(self, event):
        """处理标题栏鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_start_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            
    def _on_title_bar_mouse_move(self, event):
        """处理标题栏鼠标移动事件"""
        if self._is_dragging and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_start_pos)
            event.accept()
            
    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件"""
        self._is_dragging = False
        super().mouseReleaseEvent(event)
        
    def setup_history_section(self):
        """设置历史记录部分"""
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
        
        # 麦克风图标容器
        icon_container = QWidget(self.record_button)
        icon_container.setFixedSize(64, 64)
        icon_layout = QHBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setSpacing(0)
        
        # 创建两个图标标签
        self.mic_icon = QLabel()
        self.mic_icon.setFixedSize(24, 24)
        self.mic_icon.setStyleSheet("""
            QLabel {
                image: url(resources/mic.png);
                padding: 0;
                background: transparent;
            }
        """)
        
        self.mic_recording_icon = QLabel()
        self.mic_recording_icon.setFixedSize(24, 24)
        self.mic_recording_icon.setStyleSheet("""
            QLabel {
                image: url(resources/mic-recording.svg);
                padding: 0;
                background: transparent;
            }
        """)
        self.mic_recording_icon.hide()  # 初始隐藏录音状态图标
        
        # 将两个图标都添加到布局中
        icon_layout.addWidget(self.mic_icon, alignment=Qt.AlignmentFlag.AlignCenter)
        icon_layout.addWidget(self.mic_recording_icon, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 设置初始样式
        self._update_record_button_style(False)  # 初始化为非录音状态
        
        self.record_button.clicked.connect(self.record_button_clicked.emit)
        parent_layout.addWidget(self.record_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
    def _update_record_button_style(self, is_recording):
        """更新录音按钮样式"""
        self.record_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {"#D32F2F" if is_recording else "black"};
                border-radius: 32px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {"#B71C1C" if is_recording else "#1a1a1a"};
            }}
            QPushButton:pressed {{
                background-color: {"#961717" if is_recording else "#333333"};
            }}
        """)
        # 切换图标显示
        if is_recording:
            self.mic_icon.hide()
            self.mic_recording_icon.show()
        else:
            self.mic_icon.show()
            self.mic_recording_icon.hide()
        
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
    
    def display_result(self, text):
        """显示识别结果"""
        if text and text.strip():  # 确保文本不为空
            self.history_list.addHistoryItem(text)  # 使用新的addHistoryItem方法
    
    def update_status(self, status):
        """更新状态显示"""
        # 根据状态更新按钮样式
        is_recording = "录音中" in status if status else False
        self._update_record_button_style(is_recording)
    
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