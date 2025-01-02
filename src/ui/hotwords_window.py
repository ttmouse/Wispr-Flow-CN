from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QWidget, QLabel
from PyQt6.QtCore import Qt
import os

class HotwordsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑热词")
        self.resize(500, 600)
        
        # 设置无边框窗口
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Window
        )
        
        # 设置窗口样式
        self.setStyleSheet("""
            QDialog {
                background-color: black;
                border-radius: 10px;
            }
        """)
        
        self.setup_ui()
        self.load_hotwords()
        
        # 初始化拖动相关变量
        self._is_dragging = False
        self._drag_start_pos = None
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 标题栏
        title_bar = QWidget()
        title_bar.setFixedHeight(50)
        title_bar.setStyleSheet("background-color: black;")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(16, 0, 16, 0)
        
        # 标题
        title_label = QLabel("编辑热词")
        title_label.setStyleSheet("color: white; font-size: 16px;")
        title_layout.addWidget(title_label)
        
        # 添加弹性空间
        title_layout.addStretch()
        
        # 关闭按钮
        close_button = QLabel("×")
        close_button.setStyleSheet("""
            QLabel {
                color: #999999;
                font-size: 18px;
                padding: 4px 12px;
                border-radius: 6px;
                margin: 10px 0px;
            }
            QLabel:hover {
                color: white;
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.mousePressEvent = lambda e: self.reject()
        title_layout.addWidget(close_button)
        
        # 添加标题栏
        layout.addWidget(title_bar)
        
        # 内容区域
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }
        """)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(16)
        
        # 文本编辑框
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("每行输入一个热词，以#开头的行为注释")
        self.text_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #E5E5E7;
                border-radius: 6px;
                padding: 12px;
                font-size: 14px;
                background-color: white;
            }
            QTextEdit:focus {
                border-color: #007AFF;
            }
        """)
        content_layout.addWidget(self.text_edit)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        self.save_button = QPushButton("保存")
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0066CC;
            }
            QPushButton:pressed {
                background-color: #0055AA;
            }
        """)
        self.save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_button.clicked.connect(self.save_hotwords)
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #E5E5E7;
                color: #1D1D1F;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #D5D5D7;
            }
            QPushButton:pressed {
                background-color: #C5C5C7;
            }
        """)
        self.cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        content_layout.addLayout(button_layout)
        layout.addWidget(content_widget)
        
        # 绑定标题栏的鼠标事件
        title_bar.mousePressEvent = self._on_title_bar_mouse_press
        title_bar.mouseMoveEvent = self._on_title_bar_mouse_move
        
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
        
    def load_hotwords(self):
        """加载热词文件"""
        try:
            hotwords_file = os.path.join("resources", "hotwords.txt")
            if os.path.exists(hotwords_file):
                with open(hotwords_file, "r", encoding="utf-8") as f:
                    content = f.read()
                self.text_edit.setText(content)
        except Exception as e:
            print(f"加载热词失败: {e}")
            
    def save_hotwords(self):
        """保存热词文件"""
        try:
            content = self.text_edit.toPlainText()
            hotwords_file = os.path.join("resources", "hotwords.txt")
            with open(hotwords_file, "w", encoding="utf-8") as f:
                f.write(content)
            self.accept()
        except Exception as e:
            print(f"保存热词失败: {e}")
            
    def showEvent(self, event):
        """窗口显示时设置焦点"""
        super().showEvent(event)
        # 确保窗口在最前面并获得焦点
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        self.activateWindow()
        self.raise_()
        # 设置焦点到输入框
        self.text_edit.setFocus() 