from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QSystemTrayIcon, QMenu, QApplication, QDialog, QMenuBar
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPoint, QSettings, QEvent
from PyQt6.QtGui import QIcon, QFont, QAction, QKeySequence, QShortcut
from .settings_window import SettingsWindow
from .components.modern_button import ModernButton
from .components.modern_list_widget import ModernListWidget
from .components.history_manager import HistoryManager
import os
import sys
import json
import re
from datetime import datetime
from config import APP_VERSION  # 使用绝对导入
from utils.text_utils import clean_html_tags

class MainWindow(QMainWindow):
    # 常量定义
    WINDOW_TITLE = "Dou-flow"
    VERSION = APP_VERSION  # 使用导入的版本号
    record_button_clicked = pyqtSignal()
    history_item_clicked = pyqtSignal(str)

    def __init__(self, app_instance=None):
        super().__init__()
        self.app_instance = app_instance  # 保存应用程序实例的引用
        self._initialization_complete = False  # 标志初始化是否完成
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
        # 导入资源工具
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        from resource_utils import get_icon_path
        
        icon = QIcon(get_icon_path("mic1.png"))
        self.setWindowIcon(icon)
        
        # 设置焦点策略
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_MacShowFocusRect, True)
        
        # 初始化状态
        self.state_manager = None
        
        # 初始化拖动相关的状态变量
        self._is_dragging = False
        self._drag_start_pos = None
        
        # 恢复窗口位置
        self.restore_window_position()
        
        # 加载历史记录
        self.load_history()
        
        # 设置快捷键
        self.setup_shortcuts()
        
        # 初始化热键状态更新定时器
        self.hotkey_status_timer = QTimer()
        self.hotkey_status_timer.timeout.connect(self.update_hotkey_status)
        self.hotkey_status_timer.start(2000)  # 每2秒检查一次
        
        # 初始化状态稳定器
        try:
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from hotkey_status_stabilizer import create_status_stabilizer
            self.status_stabilizer = create_status_stabilizer()
        except Exception as e:
            import logging
            logging.error(f"初始化状态稳定器失败: {e}")
            self.status_stabilizer = None
        
        # 标记初始化完成
        self._initialization_complete = True
    
    def setup_ui(self, main_layout):
        """设置UI组件"""
        # 添加标题栏
        self.title_bar = self.setup_title_bar()
        main_layout.addWidget(self.title_bar)
        
        # 创建历史记录管理器
        # 使用项目根目录下的history.json文件
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.history_file = os.path.join(project_root, "history.json")
        self.history_manager = HistoryManager(self.history_file)
        
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
        
        # 设置焦点策略，使窗口可以接收键盘事件
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def setup_shortcuts(self):
        """设置快捷键"""
        # Command+逗号 打开设置面板
        settings_shortcut = QShortcut(QKeySequence("Ctrl+,"), self)
        settings_shortcut.activated.connect(self.open_settings)
        
        # 在 macOS 上使用 Cmd+逗号
        if sys.platform == 'darwin':
            settings_shortcut_mac = QShortcut(QKeySequence("Meta+,"), self)
            settings_shortcut_mac.activated.connect(self.open_settings)
    
    def open_settings(self):
        """打开设置窗口"""
        if self.app_instance and hasattr(self.app_instance, 'show_settings'):
            self.app_instance.show_settings()
        else:
            import logging
            logging.error("无法打开设置窗口：应用程序实例不可用")
    
    def open_settings_panel(self):
        """打开设置面板"""
        try:
            # 从应用程序实例获取必要的参数
            settings_manager = None
            audio_capture = None
            
            if self.app_instance:
                settings_manager = getattr(self.app_instance, 'settings_manager', None)
                audio_capture = getattr(self.app_instance, 'audio_capture', None)
            
            settings_window = SettingsWindow(self, settings_manager, audio_capture)
            settings_window.exec()
        except Exception as e:
            import logging
            logging.error(f"打开设置面板失败: {e}")
    

    
    def setup_title_bar(self):
        """设置标题栏"""
        title_bar = QWidget()
        title_bar.setStyleSheet("background-color: black;")
        title_bar.setFixedHeight(50)
        
        # 使用事件过滤器而不是直接绑定事件，避免初始化期间的事件处理
        title_bar.installEventFilter(self)
        # 标记这是标题栏widget，用于事件过滤
        title_bar.setProperty("is_title_bar", True)
        
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
        
        # 热键状态指示器
        self.hotkey_status_label = QLabel("●")
        self.hotkey_status_label.setStyleSheet("color: #999999; font-size: 10px; margin-left: 8px;")
        self.hotkey_status_label.setToolTip("热键状态：检查中...")
        title_layout.addWidget(self.hotkey_status_label)
        
        layout.addWidget(title_container)
        
        # 添加弹性空间
        layout.addStretch()
        
        # 样式设置按钮
        self.style_button = QLabel("⚙")
        self.style_button.setStyleSheet("""
            QLabel {
                color: #999999;
                font-size: 14px;
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
        self.style_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.style_button.mousePressEvent = lambda e: self.open_settings_panel()
        self.style_button.setToolTip("设置")
        layout.addWidget(self.style_button)
        
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
    
    def eventFilter(self, obj, event):
        """事件过滤器，用于处理标题栏事件"""
        try:
            # 检查是否是标题栏的事件
            if obj.property("is_title_bar"):
                # 如果初始化未完成，阻止鼠标事件
                if not self._initialization_complete:
                    if event.type() in [QEvent.Type.MouseButtonPress, QEvent.Type.MouseMove, QEvent.Type.MouseButtonRelease]:
                        return True
                
                # 处理鼠标事件
                if event.type() == QEvent.Type.MouseButtonPress:
                    return self._handle_title_bar_mouse_press(event)
                elif event.type() == QEvent.Type.MouseMove:
                    return self._handle_title_bar_mouse_move(event)
                elif event.type() == QEvent.Type.MouseButtonRelease:
                    return self._handle_title_bar_mouse_release(event)
            
            return super().eventFilter(obj, event)
        except Exception:
            return False
    
    def _handle_title_bar_mouse_press(self, event):
        """处理标题栏的鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_start_pos = event.pos()
            return True
        return False
    
    def _handle_title_bar_mouse_move(self, event):
        """处理标题栏的鼠标移动事件"""
        if self._is_dragging and self._drag_start_pos is not None:
            self.move(self.pos() + event.pos() - self._drag_start_pos)
            return True
        return False
    
    def _handle_title_bar_mouse_release(self, event):
        """处理标题栏的鼠标释放事件"""
        self._is_dragging = False
        self._drag_start_pos = None
        return True
    
    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件"""
        self._is_dragging = False
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)
    
    def add_to_history(self, text):
        """添加新的识别结果到历史记录"""
        if not text or not text.strip():
            return
        
        # 清理HTML标签，确保历史记录中只保存纯文本
        from utils.text_utils import clean_html_tags
        clean_text = clean_html_tags(text)
        
        # 使用历史记录管理器添加记录（保存纯文本）
        if self.history_manager.add_history_item(clean_text):
            # 成功添加，更新UI
            # 基于清理后的纯文本重新应用热词高亮用于显示
            highlighted_text = self._apply_hotword_highlight(clean_text)
            
            # 传递高亮后的文本给ModernListWidget
            self.history_list.addItem(highlighted_text)
            
            # 添加同步验证机制，确保UI与数据管理器索引一致
            from PyQt6.QtCore import QTimer
            def verify_sync():
                ui_count = self.history_list.count()
                manager_count = len(self.history_manager.history_items)
                if ui_count != manager_count:
                    self._resync_history_ui()
            
            # 延迟验证，等待异步更新完成
            QTimer.singleShot(20, verify_sync)
            
            # 滚动到最新项
            self.history_list.scrollToBottom()
            
            # 保存到文件
            self.save_history()
    
    def _resync_history_ui(self):
        """重新同步历史记录UI"""
        try:
            # 清空UI列表
            self.history_list.clear()
            
            # 重新添加所有历史记录
            for i, text in enumerate(self.history_manager.get_history_texts()):
                text_with_highlight = self._apply_hotword_highlight(text)
                self.history_list.addItem(text_with_highlight)
            
        except Exception as e:
            import logging
            logging.error(f"重新同步历史记录UI失败: {e}")
            import traceback
            logging.error(traceback.format_exc())
    
    def update_status(self, status):
        """更新状态显示"""
        is_recording = status == "录音中"
        self.record_button.set_recording_state(is_recording)
    

    
    def set_state_manager(self, state_manager):
        """设置状态管理器"""
        self.state_manager = state_manager
        if state_manager:
            self.update_status("就绪")
            # 重新应用热词高亮到已加载的历史记录
            self._reapply_hotword_highlight_to_history()
    
    def _reapply_hotword_highlight_to_history(self):
        """重新应用热词高亮到所有历史记录项"""
        try:
            if not hasattr(self, 'state_manager') or not self.state_manager:
                return
            
            # print(f"开始重新应用热词高亮，历史记录项数量: {self.history_list.count()}")
            
            # 遍历所有历史记录项
            for i in range(self.history_list.count()):
                item = self.history_list.item(i)
                if item:
                    # 获取原始文本（去除HTML标签）
                    widget = self.history_list.itemWidget(item)
                    if widget and hasattr(widget, 'getText'):
                        original_text = clean_html_tags(widget.getText())
                    else:
                        original_text = clean_html_tags(item.text())
                    
                    # 重新应用热词高亮
                    highlighted_text = self._apply_hotword_highlight(original_text)
                    
                    # 更新widget的显示内容
                    if widget and hasattr(widget, 'setText'):
                        widget.setText(highlighted_text)
                        pass  # 已更新历史记录项
            
            pass
        except Exception as e:
            import logging
            logging.error(f"重新应用热词高亮失败: {e}")
            import traceback
            logging.error(traceback.format_exc())
    
    def _on_history_item_clicked(self, item):
        """处理历史记录项点击事件"""
        try:
            # 获取历史记录项的索引
            index = self.history_list.row(item)
            total_count = len(self.history_manager.history_items)
            ui_count = self.history_list.count()
            
            if index < 0:
                self.update_status("点击处理失败：无效索引")
                return
            
            # 优先使用备用方法获取文本，避免索引不同步问题
            original_text = None
            
            # 方法1：直接从列表项获取文本（最可靠）
            if item and item.text():
                from utils.text_utils import clean_html_tags
                fallback_text = clean_html_tags(item.text())
                if fallback_text and fallback_text.strip():
                    original_text = fallback_text
            
            # 方法2：如果索引在管理器范围内，尝试从管理器获取
            if not original_text and index < total_count:
                manager_text = self.history_manager.get_original_text_by_index(index)
                if manager_text and manager_text.strip():
                    original_text = manager_text
            
            # 如果两种方法都失败
            if not original_text:
                self.update_status("点击处理失败：无法获取文本")
                return
            
            # 成功获取文本，发出点击信号
            if original_text and original_text.strip():
                # 立即更新状态显示，提供即时反馈
                self.update_status("正在处理点击...")
                
                # 发出信号
                self.history_item_clicked.emit(original_text)
            else:
                self.update_status("点击处理失败：文本为空")
                
        except Exception as e:
            import logging
            logging.error(f"处理历史记录项点击失败: {e}")
            import traceback
            logging.error(traceback.format_exc())
            self.update_status("点击处理出错")
    
    def display_result(self, text, skip_history=False):
        """显示识别结果"""
        if text and text.strip() and not skip_history:
            self.add_to_history(text)
    
    def closeEvent(self, event):
        """处理窗口关闭事件 - 完全退出应用程序"""
        # print("主窗口接收到关闭事件，准备退出应用程序")
        try:
            # 保存历史记录
            self.save_history()
            
            # 保存窗口位置
            self.save_window_position()
            
            # 调用应用程序退出方法，完全退出程序
            if self.app_instance and hasattr(self.app_instance, 'quit_application'):
                self.app_instance.quit_application()
            else:
                pass
                QApplication.instance().quit()
            
            event.accept()  # 接受关闭事件
            pass
        except Exception as e:
            import logging
            logging.error(f"处理主窗口关闭事件失败: {e}")
            # 即使出错也要退出程序
            try:
                QApplication.instance().quit()
            except:
                import os
                os._exit(0)
            event.accept()
    
    def center_on_screen(self):
        """将窗口移动到屏幕中央"""
        screen = self.screen()
        if screen:
            center = screen.availableGeometry().center()
            geo = self.frameGeometry()
            geo.moveCenter(center)
            self.move(geo.topLeft())
    

    
    def moveEvent(self, event):
        """处理窗口移动事件，保存新位置"""
        super().moveEvent(event)
        # 只有在初始化完成后才保存窗口位置，避免初始化期间的移动事件导致崩溃
        if hasattr(self, '_initialization_complete') and self._initialization_complete:
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
                    import logging
                    logging.error(f"显示窗口时出错: {e}")
                    self._fallback_show_window()
            else:
                self._fallback_show_window()
            
        except Exception as e:
            import logging
            logging.error(f"显示窗口失败: {e}")
    
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
            # 使用历史记录管理器保存
            history_data = self.history_manager.get_history_for_save()
            
            # 添加超时保护，避免在程序退出时因文件操作卡死
            import signal
            import threading
            
            def timeout_handler(signum, frame):
                raise TimeoutError("保存历史记录超时")
            
            # 设置1秒超时
            if hasattr(signal, 'SIGALRM'):  # Unix系统
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(1)
            
            try:
                with open(self.history_file, 'w', encoding='utf-8') as f:
                    json.dump(history_data, f, ensure_ascii=False, indent=2)
            finally:
                if hasattr(signal, 'SIGALRM'):
                    signal.alarm(0)  # 取消超时
                    
        except TimeoutError:
            import logging
            logging.warning("保存历史记录超时，跳过保存操作")
        except Exception as e:
            import logging
            logging.error(f"保存历史记录失败: {e}")
    
    def load_history(self):
        """从文件加载历史记录"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                
                # 清空现有历史记录
                self.history_list.clear()
                self.history_manager.clear_history()
                
                # 使用历史记录管理器加载数据
                if history_data:
                    self._loading_history = True
                    loaded_count = self.history_manager.load_history_data(history_data)
                    
                    # 将历史记录添加到UI，确保顺序一致
                    history_texts = self.history_manager.get_history_texts()
                    
                    for i, text in enumerate(history_texts):
                        text_with_highlight = self._apply_hotword_highlight(text)
                        self.history_list.addItem(text_with_highlight)
                    
                    self._loading_history = False
        except Exception as e:
            import logging
            logging.error(f"加载历史记录失败: {e}")
            import traceback
            logging.error(traceback.format_exc())
    
    def _apply_hotword_highlight(self, text):
        """应用热词高亮（使用简单的加粗效果）"""
        if not text or not hasattr(self, 'state_manager') or not self.state_manager:
            return text
        
        try:
            # 获取热词列表
            hotwords = self.state_manager.get_hotwords() if hasattr(self.state_manager, 'get_hotwords') else []
            if not hotwords:
                return text
            
            highlighted_text = text
            # 按长度降序排列热词，避免短词覆盖长词
            sorted_hotwords = sorted(hotwords, key=len, reverse=True)
            
            for hotword in sorted_hotwords:
                if hotword and hotword.strip():
                    # 使用正则表达式进行不区分大小写的替换，使用简单的加粗标签
                    pattern = re.escape(hotword.strip())
                    highlighted_text = re.sub(
                        f'({pattern})',
                        r'<b>\1</b>',
                        highlighted_text,
                        flags=re.IGNORECASE
                    )
            
            return highlighted_text
        except Exception as e:
            import logging
            logging.error(f"应用热词高亮失败: {e}")
            return text
    
    def update_hotkey_status(self):
        """更新热键状态显示（使用状态稳定器）"""
        try:
            if not hasattr(self, 'hotkey_status_label') or not self.app_instance:
                return
            
            # 从应用程序实例获取热键管理器
            hotkey_manager = getattr(self.app_instance, 'hotkey_manager', None)
            
            # 使用状态稳定器获取稳定的状态
            if hasattr(self, 'status_stabilizer') and self.status_stabilizer:
                status = self.status_stabilizer.get_stable_status(hotkey_manager)
            else:
                # 回退到原始状态检测
                if not hotkey_manager:
                    status = {
                        'active': False,
                        'scheme': 'unknown',
                        'hotkey_type': 'unknown',
                        'is_recording': False,
                        'last_error': '热键管理器不存在'
                    }
                else:
                    status = hotkey_manager.get_status()
            
            # 根据稳定状态更新UI
            self._update_status_ui(status)
                
        except Exception as e:
            # 状态检查出错
            if hasattr(self, 'hotkey_status_label'):
                self.hotkey_status_label.setStyleSheet("color: #ff4444; font-size: 10px; margin-left: 8px;")
                self.hotkey_status_label.setToolTip(f"热键状态：检查出错 - {str(e)}")
    
    def _update_status_ui(self, status):
        """根据状态更新UI显示"""
        try:
            if not hasattr(self, 'hotkey_status_label'):
                return
            
            # 获取状态信息
            is_active = status.get('active', False)
            is_recording = status.get('is_recording', False)
            hotkey_type = status.get('hotkey_type', 'unknown')
            scheme = status.get('scheme', 'unknown')
            stability = status.get('stability', '')
            active_ratio = status.get('active_ratio', 0)
            
            # 构建工具提示
            tooltip_parts = []
            
            if is_active:
                if is_recording:
                    # 正在录音
                    self.hotkey_status_label.setStyleSheet("color: #ff6b35; font-size: 10px; margin-left: 8px;")
                    tooltip_parts.append(f"热键状态：录音中 ({hotkey_type})")
                else:
                    # 正常待机
                    self.hotkey_status_label.setStyleSheet("color: #00cc66; font-size: 10px; margin-left: 8px;")
                    tooltip_parts.append(f"热键状态：正常 ({hotkey_type})")
            else:
                # 热键失效
                self.hotkey_status_label.setStyleSheet("color: #ff4444; font-size: 10px; margin-left: 8px;")
                
                # 分析失效原因
                if scheme == 'hammerspoon' and not status.get('hammerspoon_running', True):
                    tooltip_parts.append("Hammerspoon进程未运行")
                elif not status.get('listener_running', True):
                    tooltip_parts.append("监听器未运行")
                if hotkey_type == 'fn' and not status.get('fn_thread_running', True):
                    tooltip_parts.append("Fn监听线程未运行")
                if status.get('last_error'):
                    tooltip_parts.append(f"错误: {status['last_error']}")
                
                if not tooltip_parts:
                    tooltip_parts.append(f"热键状态：失效 ({hotkey_type})")
                else:
                    tooltip_parts.insert(0, f"热键状态：失效 ({hotkey_type})")
            
            # 添加稳定性信息（调试用）
            if stability:
                if stability == 'stable_active':
                    tooltip_parts.append(f"稳定性：良好 ({active_ratio:.1%})")
                elif stability == 'stable_inactive':
                    tooltip_parts.append(f"稳定性：稳定失效 ({active_ratio:.1%})")
                elif stability == 'unstable_using_last':
                    tooltip_parts.append(f"稳定性：不稳定，使用上次状态 ({active_ratio:.1%})")
                elif stability == 'unstable_no_history':
                    tooltip_parts.append(f"稳定性：不稳定，无历史记录 ({active_ratio:.1%})")
            
            # 添加方案信息
            tooltip_parts.append(f"方案: {scheme}")
            
            # 设置工具提示
            self.hotkey_status_label.setToolTip("\n".join(tooltip_parts))
            
        except Exception as e:
            import logging
            logging.error(f"更新状态UI失败: {e}")
    
    def quit_application(self):
        """退出应用程序"""
        # 停止状态更新定时器
        if hasattr(self, 'hotkey_status_timer'):
            self.hotkey_status_timer.stop()
        
        self.save_history()  # 退出前保存历史记录
        if self.app_instance:
            self.app_instance.quit_application()
        else:
            # 如果没有应用程序实例引用，直接退出
            QApplication.instance().quit()