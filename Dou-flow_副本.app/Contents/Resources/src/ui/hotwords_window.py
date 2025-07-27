from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTextEdit, QPushButton, 
    QHBoxLayout, QWidget, QLabel, QMessageBox
)

logger = logging.getLogger(__name__)


class ModernButton(QPushButton):
    """
    现代风格按钮，用于在深色背景上提供良好视觉效果。

    Attributes:
        text (str): 按钮显示文本
        primary (bool): 是否为主按钮，如果为 True 则使用主色调
        parent: 父级窗口
    """

    def __init__(self, text: str, primary: bool = False, parent=None) -> None:
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(self._get_style(primary))

    def _get_style(self, primary: bool) -> str:
        """
        获取按钮样式表字符串。

        Args:
            primary (bool): 如果为 True，则使用主按钮配色；否则使用次按钮配色。
        
        Returns:
            str: 与按钮状态相关的 CSS 样式表。
        """
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
    """
    现代风格文本编辑框，在深色背景环境下保持良好的对比度。

    Attributes:
        placeholder (str): 占位文本，会在用户未输入时显示
        parent: 父级窗口
    """

    def __init__(self, placeholder: str = "", parent=None) -> None:
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
    """
    可拖动的标签，可选是否可点击。

    Signals:
        clicked: 当 label 可点击且用户单击左键时触发
    """

    clicked = pyqtSignal()

    def __init__(self, text: str, clickable: bool = False, parent=None) -> None:
        super().__init__(text, parent)
        self._clickable = clickable
        if clickable:
            self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event) -> None:
        """
        鼠标按下事件。如果是可点击状态并且使用了左键点击则发出 clicked 信号。
        """
        if self._clickable and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


class ModernTitleBar(QWidget):
    """
    现代风格标题栏，可实现窗口的拖动和关闭功能。

    Attributes:
        title (str): 标题栏显示文本
        parent: 父级窗口（对话框或其他窗口）
    """

    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self.parent = parent
        self._is_dragging = False
        self._drag_start_pos = QPoint()
        self._setup_ui(title)

    def _setup_ui(self, title: str) -> None:
        """
        设置标题栏的界面布局，包含一个拖拽区域(标题)和一个关闭按钮。
        """
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

    def mousePressEvent(self, event) -> None:
        """
        当鼠标在标题栏区域被按下时，记录按下的位置用于拖拽。
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_start_pos = event.pos()

    def mouseMoveEvent(self, event) -> None:
        """
        当鼠标移动时，如果处于拖拽状态，则移动父窗体的位置。
        """
        if self._is_dragging:
            self.parent.move(self.parent.pos() + event.pos() - self._drag_start_pos)

    def mouseReleaseEvent(self, event) -> None:
        """
        当鼠标释放时，结束拖拽状态。
        """
        self._is_dragging = False


class ModernDialog(QDialog):
    """
    现代风格对话框基类，配合 ModernTitleBar 实现定制化外观。

    Attributes:
        title (str): 对话框标题
        parent: 父级窗口
    """

    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("QDialog { background-color: black; border-radius: 10px; }")

    def center_on_screen(self) -> None:
        """
        将对话框移动到当前屏幕可用区域的中心位置。
        """
        if (screen := self.screen()) is not None:
            geo = self.frameGeometry()
            geo.moveCenter(screen.availableGeometry().center())
            self.move(geo.topLeft())

    def showEvent(self, event) -> None:
        """
        当对话框显示时，使其居中显示。
        """
        super().showEvent(event)
        self.center_on_screen()


class HotwordsWindow(ModernDialog):
    """
    热词编辑窗口，允许用户查看或编辑热词。

    Attributes:
        HOTWORDS_FILE (Path): 存储热词内容的文件路径
        text_edit (ModernTextEdit): 用于编辑热词的文本框
    """

    HOTWORDS_FILE = Path("resources") / "hotwords.txt"

    def __init__(self, parent=None) -> None:
        super().__init__("编辑热词", parent)
        self.resize(500, 600)
        self.setup_ui()
        self.load_hotwords()

    def setup_ui(self) -> None:
        """
        设置窗口组件布局，包括标题栏和主要内容区域。
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 标题栏
        layout.addWidget(ModernTitleBar("编辑热词", self))

        # 内容区域
        content = self._create_content()
        layout.addWidget(content)

    def _create_content(self) -> QWidget:
        """
        创建窗口主体内容区域，包括文本编辑框和按钮（保存、取消）。

        Returns:
            QWidget: 组装完毕的内容区域小部件。
        """
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

    def load_hotwords(self) -> None:
        """
        从文件读取热词列表并加载到文本编辑框中。
        如果文件不存在，跳过。
        """
        try:
            if self.HOTWORDS_FILE.exists():
                content = self.HOTWORDS_FILE.read_text(encoding="utf-8")
                self.text_edit.setText(content)
        except Exception as e:
            logger.error(f"加载热词失败: {e}")
            QMessageBox.warning(self, "错误", f"加载热词失败: {e}")

    def save_hotwords(self) -> None:
        """
        将编辑框内热词写入到文件中，如果写入失败则弹窗提示错误。
        """
        try:
            content = self.text_edit.toPlainText()
            self.HOTWORDS_FILE.parent.mkdir(exist_ok=True)
            self.HOTWORDS_FILE.write_text(content, encoding="utf-8")
            self.accept()
        except Exception as e:
            logger.error(f"保存热词失败: {e}")
            QMessageBox.critical(self, "错误", f"保存热词失败: {e}")

    def showEvent(self, event) -> None:
        """
        在窗口显示时，将焦点定位到文本框并调用父类事件。
        """
        super().showEvent(event)
        self.text_edit.setFocus() 