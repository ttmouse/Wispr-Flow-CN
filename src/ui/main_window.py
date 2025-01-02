from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QSystemTrayIcon, QMenu, QApplication, QDialog, QMenuBar
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPoint
from PyQt6.QtGui import QIcon, QFont, QAction
from .components.modern_button import ModernButton
from .components.modern_list import ModernListWidget
from .hotwords_window import HotwordsWindow
import os
import sys

class MainWindow(QMainWindow):
    # 常量定义
    WINDOW_TITLE = "Dou-flow"
    record_button_clicked = pyqtSignal()
    history_item_clicked = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setMinimumSize(400, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 设置窗口样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: white;
            }
        """)
        
        # 创建UI组件
        self.setup_ui(main_layout)
        
        # 设置窗口属性
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |  # 无边框
            Qt.WindowType.Window  # 普通窗口
        )
        
        # 设置应用图标
        icon = QIcon(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "resources", "mic1.png"))
        self.setWindowIcon(icon)
        
        # 设置焦点策略
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_MacShowFocusRect, True)
        
        # 初始化状态
        self.state_manager = None
        
        # 移动窗口到屏幕中央
        self.center_on_screen()
        
        # 创建系统状态栏菜单
        self.setup_status_menu()
    
    def setup_ui(self, main_layout):
        """设置UI组件"""
        # 添加标题栏
        self.title_bar = self.setup_title_bar()
        main_layout.addWidget(self.title_bar)
        
        # 添加历史记录列表
        self.history_list = ModernListWidget()
        self.history_list.itemClicked.connect(self._on_history_item_clicked)
        
        # 添加空状态提示
        self.empty_state = QWidget()
        empty_layout = QVBoxLayout(self.empty_state)
        empty_layout.setContentsMargins(0, 60, 0, 60)
        empty_layout.setSpacing(20)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 图标
        icon_label = QLabel("⌥")
        icon_label.setStyleSheet("""
            QLabel {
                color: #999999;
                font-size: 24px;
                font-weight: 300;
            }
        """)
        empty_layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 提示文字
        hint_label = QLabel("点击录音按钮开始录音\n松开后自动转换为文字")
        hint_label.setStyleSheet("""
            QLabel {
                color: #999999;
                font-size: 14px;
                font-weight: 400;
            }
        """)
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(hint_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 将空状态提示添加到列表中
        self.history_list.setEmptyState(self.empty_state)
        
        main_layout.addWidget(self.history_list)
        
        # 添加底部按钮区域
        self.setup_bottom_bar(main_layout)
        
        # 保存拖动相关的状态
        self._is_dragging = False
        self._drag_start_pos = None
        
        # 设置焦点策略，使窗口可以接收键盘事件
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def setup_title_bar(self):
        """设置标题栏"""
        title_bar = QWidget()
        title_bar.setStyleSheet("background-color: black;")
        title_bar.setFixedHeight(50)
        
        # 添加鼠标事件追踪
        title_bar.mousePressEvent = self._on_title_bar_mouse_press
        title_bar.mouseMoveEvent = self._on_title_bar_mouse_move
        
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(8)
        
        # 标题
        title_label = QLabel(self.WINDOW_TITLE)
        title_label.setStyleSheet("color: white; font-size: 16px;")
        layout.addWidget(title_label)
        
        # 添加弹性空间
        layout.addStretch()
        
        # 关闭按钮
        self.close_button = QLabel("×")
        self.close_button.setStyleSheet("""
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
        self.close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_button.mousePressEvent = lambda e: self.hide()
        layout.addWidget(self.close_button)
        
        return title_bar
    
    def setup_bottom_bar(self, main_layout):
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
        
        main_layout.addWidget(bottom_bar)
    
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
            item = QListWidgetItem(text)
            self.history_list.addItem(item)
    
    def update_status(self, status):
        """更新状态显示"""
        is_recording = status == "录音中"
        self.record_button.set_recording_state(is_recording)
    
    def set_state_manager(self, state_manager):
        """设置状态管理器"""
        self.state_manager = state_manager
        if state_manager:
            self.update_status("就绪")
    
    def _on_history_item_clicked(self, item):
        """处理历史记录项点击事件"""
        text = item.text()
        if text:
            self.history_item_clicked.emit(text)
    
    def display_result(self, text):
        """显示识别结果"""
        if text and text.strip():
            self.add_to_history(text)
    
    def closeEvent(self, event):
        """处理窗口关闭事件"""
        event.ignore()  # 忽略关闭事件
        self.hide()  # 只是隐藏窗口
    
    def center_on_screen(self):
        """将窗口移动到屏幕中央"""
        screen = self.screen()
        if screen:
            center = screen.availableGeometry().center()
            geo = self.frameGeometry()
            geo.moveCenter(center)
            self.move(geo.topLeft())
    
    def show_hotwords_window(self):
        """显示热词编辑窗口"""
        dialog = HotwordsWindow(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 如果用户点击了保存，重新加载热词
            if hasattr(self, 'state_manager'):
                self.state_manager.reload_hotwords()
    
    def setup_status_menu(self):
        """设置系统状态栏菜单"""
        # 创建菜单栏
        menubar = QMenuBar()
        
        # 设置为系统菜单栏
        menubar.setNativeMenuBar(True)
        
        # 创建应用菜单
        app_menu = menubar.addMenu("Dou-flow")
        
        # 编辑热词
        edit_hotwords_action = QAction("编辑热词...", self)
        edit_hotwords_action.triggered.connect(self.show_hotwords_window)
        app_menu.addAction(edit_hotwords_action)
        
        # 分隔线
        app_menu.addSeparator()
        
        # 退出
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(QApplication.quit)
        app_menu.addAction(quit_action)
        
        # 设置为窗口的菜单栏
        self.setMenuBar(menubar)