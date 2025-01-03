from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTextEdit, QPushButton, 
    QHBoxLayout, QWidget, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ModernButton(QPushButton):
    """现代风格按钮"""
    def __init__(self, text: str, primary: bool = False, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(self._get_style(primary))
    
    def _get_style(self, primary: bool) -> str:
        """获取按钮样式"""
        return f"""
            QPushButton {{
                background-color: {('#007AFF' if primary else '#333333')};
                color: {'white' if primary else '#ffffff'};
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {('#0066CC' if primary else '#444444')};
            }}
            QPushButton:pressed {{
                background-color: {('#0055AA' if primary else '#222222')};
            }}
        """

class ModernTextEdit(QTextEdit):
    """现代风格文本编辑框"""
    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setStyleSheet("""
            QTextEdit {
                border: 1px solid #444444;
                border-radius: 6px;
                padding: 12px;
                font-size: 14px;
                background-color: #333333;
                color: #ffffff;
            }
            QTextEdit:focus {
                border-color: #007AFF;
            }
        """)

class DraggableLabel(QLabel):
    """可拖动的标签"""
    clicked = pyqtSignal()
    
    def __init__(self, text: str, clickable: bool = False, parent=None):
        super().__init__(text, parent)
        self._clickable = clickable
        if clickable:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def mousePressEvent(self, event):
        if self._clickable and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

class ModernTitleBar(QWidget):
    """现代风格标题栏"""
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.parent = parent
        self._is_dragging = False
        self._drag_start_pos = QPoint()
        
        self._setup_ui(title)
    
    def _setup_ui(self, title: str):
        """设置UI"""
        self.setFixedHeight(50)
        self.setStyleSheet("background-color: black;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        
        # 标题
        title_label = DraggableLabel(title)
        title_label.setStyleSheet("color: white; font-size: 16px;")
        layout.addWidget(title_label)
        layout.addStretch()
        
        # 关闭按钮
        close_button = DraggableLabel("×", clickable=True)
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
        close_button.clicked.connect(self.parent.close)
        layout.addWidget(close_button)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_start_pos = event.pos()
    
    def mouseMoveEvent(self, event):
        if self._is_dragging:
            self.parent.move(self.parent.pos() + event.pos() - self._drag_start_pos)
    
    def mouseReleaseEvent(self, event):
        self._is_dragging = False

class ModernDialog(QDialog):
    """现代风格对话框基类"""
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("QDialog { background-color: black; border-radius: 10px; }")
    
    def center_on_screen(self):
        """将窗口移动到屏幕中央"""
        if screen := self.screen():
            geo = self.frameGeometry()
            geo.moveCenter(screen.availableGeometry().center())
            self.move(geo.topLeft())
    
    def showEvent(self, event):
        super().showEvent(event)
        self.center_on_screen()

class HotwordsWindow(ModernDialog):
    """热词编辑窗口"""
    HOTWORDS_FILE = Path("resources") / "hotwords.txt"
    
    def __init__(self, parent=None):
        super().__init__("编辑热词", parent)
        self.resize(500, 600)
        self.setup_ui()
        self.load_hotwords()
    
    def setup_ui(self):
        """设置UI组件"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 添加标题栏
        layout.addWidget(ModernTitleBar("编辑热词", self))
        
        # 内容区域
        content = self._create_content()
        layout.addWidget(content)
    
    def _create_content(self) -> QWidget:
        """创建内容区域"""
        content = QWidget()
        content.setStyleSheet("""
            QWidget {
                background-color: #282828;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }
        """)
        
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 文本编辑框
        self.text_edit = ModernTextEdit("每行输入一个热词，以#开头的行为注释")
        layout.addWidget(self.text_edit)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        save_button = ModernButton("保存", primary=True)
        save_button.clicked.connect(self.save_hotwords)
        
        cancel_button = ModernButton("取消")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        return content
    
    def load_hotwords(self):
        """加载热词"""
        try:
            if self.HOTWORDS_FILE.exists():
                content = self.HOTWORDS_FILE.read_text(encoding="utf-8")
                self.text_edit.setText(content)
        except Exception as e:
            logger.error(f"加载热词失败: {e}")
            QMessageBox.warning(self, "错误", f"加载热词失败: {e}")
    
    def save_hotwords(self):
        """保存热词"""
        try:
            content = self.text_edit.toPlainText()
            self.HOTWORDS_FILE.parent.mkdir(exist_ok=True)
            self.HOTWORDS_FILE.write_text(content, encoding="utf-8")
            self.accept()
        except Exception as e:
            logger.error(f"保存热词失败: {e}")
            QMessageBox.critical(self, "错误", f"保存热词失败: {e}")
    
    def showEvent(self, event):
        """窗口显示事件"""
        super().showEvent(event)
        self.text_edit.setFocus() 