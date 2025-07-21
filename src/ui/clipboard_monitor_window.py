from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTextEdit, QPushButton, QSystemTrayIcon, QMenu, QApplication
)
from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QAction, QKeySequence, QShortcut
import os
import sys
import pyperclip
from datetime import datetime

class ClipboardMonitorWindow(QMainWindow):
    """剪贴板监控窗口"""
    
    def __init__(self, clipboard_manager=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("剪贴板监控器")
        self.setMinimumSize(400, 300)
        self.resize(500, 400)
        
        # 设置窗口标志
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        
        # 初始化剪贴板管理器
        self.clipboard_manager = clipboard_manager
        
        # 初始化变量
        self.last_clipboard_content = ""
        self._is_dragging = False
        self._drag_start_pos = None
        
        # 设置UI
        self.setup_ui()
        
        # 设置样式
        self.setup_styles()
        
        # 启动剪贴板监控
        self.setup_clipboard_monitor()
        
        # 设置快捷键
        self.setup_shortcuts()
        
        # 初始化剪贴板内容
        self.update_clipboard_display()
    
    def setup_ui(self):
        """设置用户界面"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建标题栏
        self.title_bar = self.create_title_bar()
        main_layout.addWidget(self.title_bar)
        
        # 创建内容区域
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(10)
        
        # 状态标签
        self.status_label = QLabel("剪贴板监控中...")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 12px;
                padding: 5px;
            }
        """)
        content_layout.addWidget(self.status_label)
        
        # 剪贴板内容显示区域
        self.content_display = QTextEdit()
        self.content_display.setReadOnly(True)
        self.content_display.setPlaceholderText("剪贴板内容将在这里显示...")
        content_layout.addWidget(self.content_display)
        
        # 底部按钮区域
        button_layout = QHBoxLayout()
        
        # 清空按钮
        self.clear_button = QPushButton("清空显示")
        self.clear_button.clicked.connect(self.clear_display)
        button_layout.addWidget(self.clear_button)
        
        # 复制按钮
        self.copy_button = QPushButton("复制内容")
        self.copy_button.clicked.connect(self.copy_current_content)
        button_layout.addWidget(self.copy_button)
        
        # 刷新按钮
        self.refresh_button = QPushButton("手动刷新")
        self.refresh_button.clicked.connect(self.manual_refresh)
        button_layout.addWidget(self.refresh_button)
        
        button_layout.addStretch()
        
        # 关闭按钮
        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)
        
        content_layout.addLayout(button_layout)
        main_layout.addWidget(content_widget)
    
    def create_title_bar(self):
        """创建自定义标题栏"""
        title_bar = QWidget()
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
        """)
        
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(15, 0, 15, 0)
        
        # 标题
        title_label = QLabel("📋 剪贴板监控器")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # 最小化按钮
        minimize_button = QPushButton("−")
        minimize_button.setFixedSize(30, 30)
        minimize_button.clicked.connect(self.showMinimized)
        minimize_button.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                border-radius: 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        layout.addWidget(minimize_button)
        
        # 关闭按钮
        close_button = QPushButton("×")
        close_button.setFixedSize(30, 30)
        close_button.clicked.connect(self.close)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        layout.addWidget(close_button)
        
        return title_bar
    
    def setup_styles(self):
        """设置窗口样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ecf0f1;
                border-radius: 8px;
            }
            
            QTextEdit {
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
                font-size: 12px;
                line-height: 1.4;
            }
            
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 12px;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background-color: #2980b9;
            }
            
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
    
    def setup_clipboard_monitor(self):
        """设置剪贴板监控定时器"""
        self.clipboard_timer = QTimer()
        self.clipboard_timer.timeout.connect(self.check_clipboard)
        self.clipboard_timer.start(500)  # 每500ms检查一次
    
    def setup_shortcuts(self):
        """设置快捷键"""
        # Ctrl+R 刷新
        refresh_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        refresh_shortcut.activated.connect(self.manual_refresh)
        
        # Ctrl+C 复制
        copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        copy_shortcut.activated.connect(self.copy_current_content)
        
        # Escape 关闭
        close_shortcut = QShortcut(QKeySequence("Escape"), self)
        close_shortcut.activated.connect(self.close)
    
    def check_clipboard(self):
        """检查剪贴板内容变化"""
        try:
            if self.clipboard_manager:
                current_content = self.clipboard_manager.get_clipboard_content()
            else:
                current_content = pyperclip.paste()
                
            if current_content != self.last_clipboard_content:
                self.last_clipboard_content = current_content
                self.update_clipboard_display()
        except Exception as e:
            self.status_label.setText(f"剪贴板读取错误: {str(e)}")
    
    def update_clipboard_display(self):
        """更新剪贴板内容显示"""
        try:
            if self.clipboard_manager:
                content = self.clipboard_manager.get_clipboard_content()
            else:
                content = pyperclip.paste()
                
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            if content:
                # 显示内容长度和时间戳
                content_length = len(content)
                self.status_label.setText(f"最后更新: {timestamp} | 内容长度: {content_length} 字符")
                
                # 显示内容
                display_text = f"[{timestamp}] 剪贴板内容:\n\n{content}"
                self.content_display.setPlainText(display_text)
                
                # 滚动到底部
                cursor = self.content_display.textCursor()
                cursor.movePosition(cursor.MoveOperation.End)
                self.content_display.setTextCursor(cursor)
            else:
                self.status_label.setText(f"最后更新: {timestamp} | 剪贴板为空")
                self.content_display.setPlainText("剪贴板当前为空")
                
        except Exception as e:
            self.status_label.setText(f"更新显示错误: {str(e)}")
    
    def clear_display(self):
        """清空显示内容"""
        self.content_display.clear()
        self.status_label.setText("显示已清空")
    
    def copy_current_content(self):
        """复制当前显示的内容"""
        try:
            if self.clipboard_manager:
                 content = self.clipboard_manager.get_clipboard_content()
                 if content:
                     self.clipboard_manager.copy_to_clipboard(content)
                     self.status_label.setText("内容已复制到剪贴板")
                 else:
                     self.status_label.setText("没有内容可复制")
            else:
                content = pyperclip.paste()
                if content:
                    pyperclip.copy(content)
                    self.status_label.setText("内容已复制到剪贴板")
                else:
                    self.status_label.setText("没有内容可复制")
        except Exception as e:
            self.status_label.setText(f"复制失败: {str(e)}")
    
    def manual_refresh(self):
        """手动刷新剪贴板内容"""
        self.update_clipboard_display()
        self.status_label.setText("手动刷新完成")
    
    def mousePressEvent(self, event):
        """鼠标按下事件 - 用于窗口拖动"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 检查是否点击在标题栏区域
            if event.position().y() <= 40:  # 标题栏高度
                self._is_dragging = True
                self._drag_start_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 用于窗口拖动"""
        if self._is_dragging and self._drag_start_pos:
            self.move(event.globalPosition().toPoint() - self._drag_start_pos)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件 - 结束窗口拖动"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = False
            self._drag_start_pos = None
            event.accept()
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止定时器
        if hasattr(self, 'clipboard_timer'):
            self.clipboard_timer.stop()
        event.accept()

# 独立运行测试
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ClipboardMonitorWindow()
    window.show()
    sys.exit(app.exec())