from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QSystemTrayIcon, QMenu, QApplication, QDialog, QMenuBar
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPoint, QSettings
from PyQt6.QtGui import QIcon, QFont, QAction
from .components.modern_button import ModernButton
from .components.modern_list import ModernListWidget
from .hotwords_window import HotwordsWindow
import os
import sys
import json
from datetime import datetime
from config import APP_VERSION  # 使用绝对导入

class MainWindow(QMainWindow):
    # 常量定义
    WINDOW_TITLE = "Dou-flow"
    VERSION = APP_VERSION  # 使用导入的版本号
    record_button_clicked = pyqtSignal()
    history_item_clicked = pyqtSignal(str)

    def __init__(self, app_instance=None):
        super().__init__()
        self.app_instance = app_instance  # 保存应用程序实例的引用
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setMinimumSize(400, 600)
        
        # 设置窗口标志
        self.setWindowFlags(
            Qt.WindowType.Window |  # 普通窗口
            Qt.WindowType.FramelessWindowHint |  # 无边框
            Qt.WindowType.WindowSystemMenuHint |  # 系统菜单
            Qt.WindowType.WindowStaysOnTopHint  # 总是在最前
        )
        
        # 设置窗口属性
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)  # 显示时需要激活
        
        # 历史记录文件路径
        self.history_file = 'history.json'
        self._loading_history = False  # 标志是否正在加载历史记录
        
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
        
        # 设置应用图标
        icon = QIcon(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "resources", "mic1.png"))
        self.setWindowIcon(icon)
        
        # 设置焦点策略
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_MacShowFocusRect, True)
        
        # 初始化状态
        self.state_manager = None
        
        # 恢复窗口位置
        self.restore_window_position()
        
        # 加载历史记录
        self.load_history()
    
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
        layout.setContentsMargins(16, 0, 8, 0)
        layout.setSpacing(8)
        
        # 标题和版本号
        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(8)
        
        title_label = QLabel(self.WINDOW_TITLE)
        title_label.setStyleSheet("color: white; font-size: 16px;")
        title_layout.addWidget(title_label)
        
        version_label = QLabel(f"v{self.VERSION}")
        version_label.setStyleSheet("color: #666666; font-size: 12px;")
        title_layout.addWidget(version_label)
        
        # 添加加载状态标签
        self.loading_status_label = QLabel("")
        self.loading_status_label.setStyleSheet("color: #999999; font-size: 11px; margin-left: 8px;")
        title_layout.addWidget(self.loading_status_label)
        
        layout.addWidget(title_container)
        
        # 添加弹性空间
        layout.addStretch()
        
        # 最小化按钮
        self.minimize_button = QLabel("−")
        self.minimize_button.setStyleSheet("""
            QLabel {
                color: #999999;
                font-size: 16px;
                padding: 4px 8px;
                border-radius: 3px;
                margin: 12px 0;
                background-color: rgba(255, 255, 255, 0.05);
                min-width: 16px;
                min-height: 16px;
                text-align: center;
            }
            QLabel:hover {
                color: white;
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)
        self.minimize_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.minimize_button.mousePressEvent = lambda e: self.hide()
        layout.addWidget(self.minimize_button)
        
        # 关闭按钮
        self.close_button = QLabel("×")
        self.close_button.setStyleSheet("""
            QLabel {
                color: #999999;
                font-size: 16px;
                padding: 4px 8px;
                border-radius: 3px;
                margin: 12px 0;
                background-color: rgba(255, 255, 255, 0.05);
                min-width: 16px;
                min-height: 16px;
                text-align: center;
            }
            QLabel:hover {
                color: white;
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)
        self.close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_button.mousePressEvent = lambda e: self.quit_application()
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
            # 检查是否已存在相同文本，避免重复
            for i in range(self.history_list.count()):
                existing_item = self.history_list.item(i)
                if existing_item and existing_item.text() == text:
                    return  # 已存在，不重复添加
            
            item = QListWidgetItem(text)
            self.history_list.addItem(item)  # ModernListWidget会自动添加到顶部
            
            # 只有在不是加载历史记录时才保存
            if not self._loading_history:
                self.save_history()
    
    def update_status(self, status):
        """更新状态显示"""
        is_recording = status == "录音中"
        self.record_button.set_recording_state(is_recording)
    
    def update_loading_status(self, status):
        """更新加载状态显示"""
        if hasattr(self, 'loading_status_label'):
            self.loading_status_label.setText(status)
            if status:
                self.loading_status_label.show()
            else:
                self.loading_status_label.hide()
    
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
        event.accept()  # 接受关闭事件
        self.quit_application()  # 退出程序
    
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
    
    def moveEvent(self, event):
        """处理窗口移动事件，保存新位置"""
        super().moveEvent(event)
        self.save_window_position()
    
    def save_window_position(self):
        """保存窗口位置"""
        settings = QSettings("Dou-flow", "WindowState")
        settings.setValue("window_position", self.pos())
    
    def restore_window_position(self):
        """恢复窗口位置"""
        settings = QSettings("Dou-flow", "WindowState")
        saved_pos = settings.value("window_position")
        
        if saved_pos and isinstance(saved_pos, QPoint):
            # 确保位置在可见区域内
            screen = self.screen()
            if screen:
                screen_geo = screen.availableGeometry()
                
                # 如果保存的位置在屏幕外，则移动到屏幕内
                if not screen_geo.contains(saved_pos):
                    self.center_on_screen()
                else:
                    self.move(saved_pos)
        else:
            # 首次运行或无效位置，居中显示
            self.center_on_screen()
    
    def _show_window_internal(self):
        """在主线程中显示窗口"""
        try:
            if sys.platform == 'darwin':
                try:
                    from AppKit import NSApplication
                    app = NSApplication.sharedApplication()
                    
                    # 显示并激活窗口
                    if not self.isVisible():
                        self.show()
                    
                    # 强制激活应用和窗口
                    app.activateIgnoringOtherApps_(True)
                    self.raise_()
                    self.activateWindow()
                    self.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
                    
                except Exception as e:
                    print(f"显示窗口时出错: {e}")
                    self._fallback_show_window()
            else:
                self._fallback_show_window()
            
            print("✓ 窗口已显示")
        except Exception as e:
            print(f"❌ 显示窗口失败: {e}")
    
    def _fallback_show_window(self):
        """后备的窗口显示方法"""
        if not self.isVisible():
            self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
    
    def save_history(self):
        """保存历史记录到文件"""
        try:
            history_data = []
            # 限制历史记录数量为100条
            max_history = 100
            count = min(self.history_list.count(), max_history)
            
            for i in range(count):
                item = self.history_list.item(i)
                if item:
                    history_data.append({
                        'text': item.text(),
                        'timestamp': datetime.now().isoformat()
                    })
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史记录失败: {e}")
    
    def load_history(self):
        """从文件加载历史记录"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                
                # 清空现有历史记录
                self.history_list.clear()
                
                # 按时间倒序排列（最新的在前）
                if history_data:
                    # 如果有时间戳，按时间排序
                    if isinstance(history_data[0], dict) and 'timestamp' in history_data[0]:
                        history_data.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
                    
                    for entry in history_data:
                        if isinstance(entry, dict) and 'text' in entry:
                            # 临时禁用保存，避免加载时重复保存
                            self._loading_history = True
                            item = QListWidgetItem(entry['text'])
                            self.history_list.addItem(item)
                            self._loading_history = False
                        elif isinstance(entry, str):
                            # 兼容旧格式
                            self._loading_history = True
                            item = QListWidgetItem(entry)
                            self.history_list.addItem(item)
                            self._loading_history = False
        except Exception as e:
            print(f"加载历史记录失败: {e}")
    
    def quit_application(self):
        """退出应用程序"""
        self.save_history()  # 退出前保存历史记录
        if self.app_instance:
            self.app_instance.quit_application()
        else:
            # 如果没有应用程序实例引用，直接退出
            QApplication.instance().quit()