from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QLabel)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from .components.modern_button import ModernButton
from .components.modern_list import ModernListWidget, HistoryItem

class MainWindow(QMainWindow):
    record_button_clicked = pyqtSignal()
    space_key_pressed = pyqtSignal()
    history_item_clicked = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("语音识别")
        self.setFixedSize(400, 600)
        
        # 设置窗口无边框
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # 创建主窗口部件和布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 添加标题栏
        self.title_bar = self.setup_title_bar()
        self.main_layout.addWidget(self.title_bar)
        
        # 添加历史记录列表
        self.history_list = ModernListWidget()
        self.history_list.itemClicked.connect(self._on_history_item_clicked)
        self.main_layout.addWidget(self.history_list)
        
        # 添加底部按钮区域
        self.setup_bottom_bar()
        
        # 保存拖动相关的状态
        self._is_dragging = False
        self._drag_start_pos = None
        
        # 初始化状态管理器
        self.state_manager = None
        
        # 设置焦点策略，使窗口可以接收键盘事件
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def setup_title_bar(self):
        """设置标题栏"""
        title_bar = QWidget()
        title_bar.setStyleSheet("background-color: black;")
        title_bar.setFixedHeight(40)
        
        # 添加鼠标事件追踪
        title_bar.mousePressEvent = self._on_title_bar_mouse_press
        title_bar.mouseMoveEvent = self._on_title_bar_mouse_move
        
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(8)
        
        # 标题
        title_label = QLabel("语音识别")
        title_label.setStyleSheet("color: white; font-size: 14px;")
        layout.addWidget(title_label)
        
        # 添加弹性空间
        layout.addStretch()
        
        # 设置按钮
        self.settings_button = QPushButton("⚙")
        self.settings_button.setStyleSheet("""
            QPushButton {
                color: white;
                background: transparent;
                border: none;
                font-size: 18px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
            }
        """)
        self.settings_button.clicked.connect(self.show_settings)
        layout.addWidget(self.settings_button)
        
        # 关闭按钮
        self.close_button = QPushButton("×")
        self.close_button.setStyleSheet("""
            QPushButton {
                color: white;
                background: transparent;
                border: none;
                font-size: 20px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background: #FF4136;
                border-radius: 4px;
            }
        """)
        self.close_button.clicked.connect(self.close)
        layout.addWidget(self.close_button)
        
        return title_bar
    
    def setup_bottom_bar(self):
        """设置底部按钮区域"""
        bottom_bar = QWidget()
        bottom_bar.setFixedHeight(100)
        bottom_bar.setStyleSheet("background-color: white;")
        
        layout = QHBoxLayout(bottom_bar)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 录音按钮
        self.record_button = ModernButton()
        self.record_button.clicked.connect(self.record_button_clicked.emit)
        layout.addWidget(self.record_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.main_layout.addWidget(bottom_bar)
    
    def show_settings(self):
        """显示设置窗口"""
        from .settings_window import SettingsWindow
        settings_window = SettingsWindow(self)
        settings_window.exec()
    
    def _on_title_bar_mouse_press(self, event):
        """处理标题栏的鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_start_pos = event.pos()
    
    def _on_title_bar_mouse_move(self, event):
        """处理标题栏的鼠标移动事件"""
        if self._is_dragging and self._drag_start_pos is not None:
            self.move(self.pos() + event.pos() - self._drag_start_pos)
    
    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件"""
        self._is_dragging = False
        self._drag_start_pos = None
    
    def add_to_history(self, text):
        """添加新的识别结果到历史记录"""
        if text and text.strip():
            self.history_list.addHistoryItem(text)
    
    def update_status(self, status):
        """更新状态显示"""
        is_recording = "录音中" in status if status else False
        self.record_button.set_recording_state(is_recording)
    
    def set_state_manager(self, state_manager):
        """设置状态管理器"""
        self.state_manager = state_manager
        if state_manager:
            self.update_status(state_manager.recording_status_text)
    
    def keyPressEvent(self, event):
        """处理键盘事件"""
        if event.key() == Qt.Key.Key_Space:
            self.space_key_pressed.emit()
        super().keyPressEvent(event)
    
    def _on_history_item_clicked(self, item):
        """处理历史记录项点击事件"""
        text = self.history_list.getItemText(item)
        if text:
            self.history_item_clicked.emit(text)
    
    def display_result(self, text):
        """显示识别结果"""
        if text and text.strip():
            self.add_to_history(text)