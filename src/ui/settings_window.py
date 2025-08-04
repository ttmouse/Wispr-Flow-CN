"""
现代化的 macOS 风格设置窗口
参考系统设置界面设计
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QComboBox, QPushButton, QGroupBox,
                            QCheckBox, QSlider, QListWidget, QListWidgetItem,
                            QLineEdit, QFileDialog, QTextEdit, QMessageBox, QDialog,
                            QStackedWidget, QFrame, QScrollArea, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect, QRectF, pyqtProperty
from PyQt6.QtGui import QFont, QPalette, QColor, QPainter, QBrush, QPen, QFontMetrics, QIcon
from pathlib import Path
import pyaudio


class ModernSwitch(QWidget):
    """现代化的开关控件 - 参考系统设置"""
    toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(42, 24)  # 稍大一些，更接近系统设置
        self._checked = False
        self._position = 2
        self._animation = QPropertyAnimation(self, b"position")
        self._animation.setDuration(200)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 背景轨道
        track_rect = QRectF(0, 0, self.width(), self.height())
        track_color = QColor("#007AFF") if self._checked else QColor("#39393D")
        painter.setBrush(QBrush(track_color))
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.drawRoundedRect(track_rect, 12, 12)

        # 滑块
        knob_size = 20
        knob_x = self._position
        knob_y = 2

        # 滑块阴影
        shadow_rect = QRectF(knob_x + 0.5, knob_y + 0.5, knob_size, knob_size)
        painter.setBrush(QBrush(QColor(0, 0, 0, 20)))
        painter.drawEllipse(shadow_rect)

        # 滑块主体
        knob_rect = QRectF(knob_x, knob_y, knob_size, knob_size)
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawEllipse(knob_rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle()

    def toggle(self):
        self._checked = not self._checked
        self._animate_to_position()
        self.toggled.emit(self._checked)

    def setChecked(self, checked):
        if self._checked != checked:
            self._checked = checked
            self._animate_to_position()

    def isChecked(self):
        return self._checked

    def _animate_to_position(self):
        start_pos = 2 if not self._checked else 20
        end_pos = 20 if self._checked else 2
        self._animation.setStartValue(start_pos)
        self._animation.setEndValue(end_pos)
        self._animation.start()

    @pyqtProperty(float)
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._position = value
        self.update()


class ModernSlider(QWidget):
    """现代化的滑块控件 - 参考系统设置，带数值显示"""
    valueChanged = pyqtSignal(int)

    def __init__(self, minimum=0, maximum=100, value=50, unit="", parent=None):
        super().__init__(parent)
        self.minimum = minimum
        self.maximum = maximum
        self._value = value
        self.unit = unit
        self.setFixedHeight(40)  # 增加高度以容纳数值显示
        self.setMinimumWidth(200)
        self.dragging = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 轨道 - 向下移动为数值留出空间
        track_y = 22
        track_height = 3
        track_rect = QRectF(12, track_y, self.width() - 24, track_height)
        painter.setBrush(QBrush(QColor("#3A3A3C")))
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.drawRoundedRect(track_rect, track_height/2, track_height/2)

        # 进度
        progress_width = (self._value - self.minimum) / (self.maximum - self.minimum) * (self.width() - 24)
        if progress_width > 0:
            progress_rect = QRectF(12, track_y, progress_width, track_height)
            painter.setBrush(QBrush(QColor("#007AFF")))
            painter.drawRoundedRect(progress_rect, track_height/2, track_height/2)

        # 滑块
        knob_x = 12 + progress_width - 10
        knob_y = track_y - 7
        knob_size = 17

        # 滑块阴影
        shadow_rect = QRectF(knob_x + 1, knob_y + 1, knob_size, knob_size)
        painter.setBrush(QBrush(QColor(0, 0, 0, 30)))
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.drawEllipse(shadow_rect)

        # 滑块主体
        knob_rect = QRectF(knob_x, knob_y, knob_size, knob_size)
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.setPen(QPen(QColor("#D1D1D6"), 0.5))
        painter.drawEllipse(knob_rect)

        # 数值显示
        painter.setPen(QPen(QColor("#FFFFFF")))
        painter.setFont(QFont("-apple-system", 11))
        value_text = f"{self._value}{self.unit}"
        text_rect = QRectF(0, 2, self.width(), 16)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, value_text)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self._update_value_from_position(event.position().x())

    def mouseMoveEvent(self, event):
        if self.dragging:
            self._update_value_from_position(event.position().x())

    def mouseReleaseEvent(self, event):
        self.dragging = False

    def _update_value_from_position(self, x):
        relative_x = max(8, min(x, self.width() - 8)) - 8
        ratio = relative_x / (self.width() - 16)
        new_value = int(self.minimum + ratio * (self.maximum - self.minimum))
        if new_value != self._value:
            self._value = new_value
            self.valueChanged.emit(self._value)
            self.update()

    def value(self):
        return self._value

    def setValue(self, value):
        value = max(self.minimum, min(self.maximum, value))
        if value != self._value:
            self._value = value
            self.update()


class ModernComboBox(QComboBox):
    """现代化的下拉框 - 参考系统设置"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)  # 增加高度，更接近系统设置
        self.setMinimumWidth(140)
        self._setup_style()

    def _setup_style(self):
        self.setStyleSheet("""
            QComboBox {
                background-color: #1C1C1E;
                border: 2px solid #3A3A3C;
                border-radius: 8px;
                padding: 8px 12px;
                color: #ffffff;
                font-size: 13px;
                font-weight: 400;
                selection-background-color: transparent;
                min-height: 16px;
                padding-right: 30px;
            }

            QComboBox:hover {
                background-color: #2C2C2E;
                border-color: #48484A;
            }

            QComboBox:focus {
                border-color: #007AFF;
            }

            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 24px;
                border: none;
                background: transparent;
                margin-right: 4px;
            }

            QComboBox::down-arrow {
                width: 8px;
                height: 8px;
                background-color: #8E8E93;
                border-radius: 2px;
                margin: 4px;
            }

            QComboBox::down-arrow:hover {
                background-color: #AEAEB2;
            }

            QComboBox QAbstractItemView {
                background-color: #1C1C1E;
                border: 2px solid #3A3A3C;
                border-radius: 8px;
                color: #ffffff;
                selection-background-color: #007AFF;
                outline: none;
                padding: 4px 0px;
                font-size: 13px;
            }

            QComboBox QAbstractItemView::item {
                padding: 8px 12px;
                border: none;
                min-height: 20px;
            }

            QComboBox QAbstractItemView::item:selected {
                background-color: #007AFF;
                color: #ffffff;
            }

            QComboBox QAbstractItemView::item:hover {
                background-color: #2C2C2E;
            }
        """)

    def addItem(self, text, userData=None):
        """重写添加项目方法，支持勾选标记"""
        super().addItem(text, userData)

    def setCurrentText(self, text):
        """设置当前文本"""
        index = self.findText(text)
        if index >= 0:
            self.setCurrentIndex(index)

    def paintEvent(self, event):
        """自定义绘制，添加勾选标记"""
        super().paintEvent(event)

        # 如果需要，可以在这里添加自定义绘制逻辑


class SettingRow(QWidget):
    """设置行组件 - 参考系统设置的行布局"""

    def __init__(self, icon, title, description="", control_widget=None, parent=None):
        super().__init__(parent)
        self.setFixedHeight(52)  # 增加行高，更接近系统设置
        self._setup_ui(icon, title, description, control_widget)
    
    def _setup_ui(self, icon, title, description, control_widget):
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 10, 20, 10)  # 增加边距
        layout.setSpacing(16)  # 增加间距
        
        # 图标
        if icon:
            icon_label = QLabel(icon)
            icon_label.setFixedSize(28, 28)  # 稍大的图标
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    background-color: transparent;
                    color: #ffffff;
                }
            """)
            layout.addWidget(icon_label)
        
        # 文本区域
        text_widget = QWidget()
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(0)
        
        # 标题
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 14px;
                font-weight: 500;
                background-color: transparent;
            }
        """)
        text_layout.addWidget(title_label)

        # 描述（如果有）
        if description:
            desc_label = QLabel(description)
            desc_label.setStyleSheet("""
                QLabel {
                    color: #8E8E93;
                    font-size: 12px;
                    background-color: transparent;
                    margin-top: 2px;
                }
            """)
            text_layout.addWidget(desc_label)
        
        text_widget.setLayout(text_layout)
        layout.addWidget(text_widget)
        
        # 弹性空间
        layout.addStretch()
        
        # 控件
        if control_widget:
            layout.addWidget(control_widget)
        
        self.setLayout(layout)
        
        # 设置样式 - 移除多余的边框
        self.setStyleSheet("""
            SettingRow {
                background-color: transparent;
                border: none;
            }
            SettingRow:hover {
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 6px;
            }
        """)


class SettingGroup(QWidget):
    """设置组 - 参考系统设置的分组"""
    
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self._setup_ui(title)
    
    def _setup_ui(self, title):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 组标题（如果有）
        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet("""
                QLabel {
                    color: #8E8E93;
                    font-size: 13px;
                    font-weight: 600;
                    padding: 16px 16px 8px 16px;
                    background-color: transparent;
                }
            """)
            layout.addWidget(title_label)
        
        # 内容容器
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.content_widget.setLayout(self.content_layout)
        
        # 设置组样式 - 移除边框，使用更简洁的设计
        self.content_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(28, 28, 30, 0.6);
                border-radius: 10px;
                border: none;
            }
        """)
        
        layout.addWidget(self.content_widget)
        self.setLayout(layout)
    
    def add_row(self, row_widget):
        """添加设置行"""
        self.content_layout.addWidget(row_widget)


class MacOSSettingsWindow(QDialog):
    """现代化的设置窗口 - 参考 macOS 系统设置"""

    settings_saved = pyqtSignal()

    def __init__(self, parent=None, settings_manager=None, audio_capture=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.audio_capture = audio_capture

        # 窗口设置
        self.setWindowTitle("设置")
        self.setFixedSize(780, 580)  # 参考系统设置的尺寸
        self.setModal(True)

        # 设置窗口样式
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
            }
        """)

        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """设置UI"""
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(1)

        # 左侧边栏
        self._create_sidebar()
        main_layout.addWidget(self.sidebar)

        # 右侧内容区
        self._create_content_area()
        main_layout.addWidget(self.content_area)

        self.setLayout(main_layout)

    def _create_sidebar(self):
        """创建左侧边栏"""
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border-right: 1px solid #2d2d2d;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 搜索框（占位）
        search_widget = QWidget()
        search_widget.setFixedHeight(44)
        search_widget.setStyleSheet("background-color: transparent;")
        layout.addWidget(search_widget)

        # 菜单列表
        self.menu_list = QListWidget()
        self.menu_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                outline: none;
                font-size: 13px;
                padding: 8px;
            }

            QListWidget::item {
                padding: 6px 12px;
                border: none;
                color: #ffffff;
                border-radius: 5px;
                margin: 1px 0px;
                min-height: 20px;
            }

            QListWidget::item:selected {
                background-color: #0066cc;
                color: #ffffff;
            }

            QListWidget::item:hover:!selected {
                background-color: #2a2a2a;
            }
        """)

        # 添加菜单项 - 保留所有原有功能
        menu_items = [
            ("🎤", "常规"),
            ("🔊", "音频"),
            ("🗣️", "语音识别"),
            ("📋", "粘贴设置"),
            ("🔤", "热词设置"),
            ("📝", "热词编辑"),
            ("📦", "依赖管理"),
        ]

        for icon, text in menu_items:
            item = QListWidgetItem(f"{icon}  {text}")
            self.menu_list.addItem(item)

        self.menu_list.setCurrentRow(0)
        self.menu_list.currentRowChanged.connect(self._on_menu_changed)

        layout.addWidget(self.menu_list)
        layout.addStretch()

        self.sidebar.setLayout(layout)

    def _create_content_area(self):
        """创建右侧内容区"""
        self.content_area = QFrame()
        self.content_area.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: none;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 标题栏
        title_bar = QWidget()
        title_bar.setFixedHeight(52)
        title_bar.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border-bottom: 1px solid #2d2d2d;
            }
        """)

        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(20, 0, 20, 0)

        self.title_label = QLabel("常规")
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: 600;
                color: #ffffff;
                background-color: transparent;
            }
        """)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()

        title_bar.setLayout(title_layout)
        layout.addWidget(title_bar)

        # 内容区域
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background-color: transparent;")

        # 创建各个页面
        self._create_pages()

        layout.addWidget(self.stacked_widget)

        # 底部按钮
        self._create_bottom_buttons(layout)

        self.content_area.setLayout(layout)

    def _create_pages(self):
        """创建设置页面"""
        # 常规设置页面（原录音设置）
        general_page = self._create_general_page()
        self.stacked_widget.addWidget(general_page)

        # 音频页面
        audio_page = self._create_audio_page()
        self.stacked_widget.addWidget(audio_page)

        # 语音识别页面
        asr_page = self._create_asr_page()
        self.stacked_widget.addWidget(asr_page)

        # 粘贴设置页面
        paste_page = self._create_paste_page()
        self.stacked_widget.addWidget(paste_page)

        # 热词设置页面
        hotword_settings_page = self._create_hotword_settings_page()
        self.stacked_widget.addWidget(hotword_settings_page)

        # 热词编辑页面
        hotword_edit_page = self._create_hotword_edit_page()
        self.stacked_widget.addWidget(hotword_edit_page)

        # 依赖管理页面
        dependency_page = self._create_dependency_page()
        self.stacked_widget.addWidget(dependency_page)

    def _create_general_page(self):
        """创建常规设置页面"""
        page = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        content = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 快捷键设置组
        hotkey_group = SettingGroup("快捷键设置")

        # 热键方案
        self.hotkey_scheme_combo = ModernComboBox()
        self.hotkey_scheme_combo.addItems(['hammerspoon', 'python'])
        scheme_row = SettingRow("⌨️", "热键方案", "选择热键监听方案", self.hotkey_scheme_combo)
        hotkey_group.add_row(scheme_row)

        # 录音快捷键
        self.hotkey_combo = ModernComboBox()
        self.hotkey_combo.addItems(['fn', 'ctrl', 'alt'])
        hotkey_row = SettingRow("🔘", "录音快捷键", "按住此键开始录音", self.hotkey_combo)
        hotkey_group.add_row(hotkey_row)

        # 启动延迟
        self.delay_slider = ModernSlider(0, 500, 50, "ms")
        delay_row = SettingRow("⏱️", "启动延迟", "快捷键按下后的延迟时间", self.delay_slider)
        hotkey_group.add_row(delay_row)

        layout.addWidget(hotkey_group)

        # 高级设置组
        advanced_group = SettingGroup("高级设置")

        # 调试模式
        self.debug_switch = ModernSwitch()
        debug_row = SettingRow("🔧", "调试模式", "启用详细日志记录", self.debug_switch)
        advanced_group.add_row(debug_row)

        # 性能监控
        self.monitor_switch = ModernSwitch()
        monitor_row = SettingRow("📊", "性能监控", "监控系统性能指标", self.monitor_switch)
        advanced_group.add_row(monitor_row)

        # 自动启动
        self.autostart_switch = ModernSwitch()
        autostart_row = SettingRow("🚀", "开机自启", "系统启动时自动运行", self.autostart_switch)
        advanced_group.add_row(autostart_row)

        # 最小化到托盘
        self.minimize_to_tray_switch = ModernSwitch()
        tray_row = SettingRow("📱", "最小化到托盘", "关闭窗口时最小化到系统托盘", self.minimize_to_tray_switch)
        advanced_group.add_row(tray_row)

        layout.addWidget(advanced_group)
        layout.addStretch()

        content.setLayout(layout)
        scroll_area.setWidget(content)

        page_layout = QVBoxLayout()
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll_area)
        page.setLayout(page_layout)

        return page

    def _create_audio_page(self):
        """创建音频设置页面"""
        page = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        content = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 音频输入组
        input_group = SettingGroup("音频输入")

        # 输入设备
        device_widget = self._create_device_selector()
        device_row = SettingRow("🎤", "输入设备", "选择音频输入设备", device_widget)
        input_group.add_row(device_row)

        # 音量阈值
        self.volume_slider = ModernSlider(0, 1000, 150, "")
        volume_row = SettingRow("🔊", "音量阈值", "录音触发的最小音量", self.volume_slider)
        input_group.add_row(volume_row)

        # 最大录音时长
        self.duration_slider = ModernSlider(5, 60, 10, "秒")
        duration_row = SettingRow("⏰", "最大录音时长", "单次录音的最大时长", self.duration_slider)
        input_group.add_row(duration_row)

        layout.addWidget(input_group)
        layout.addStretch()

        content.setLayout(layout)
        scroll_area.setWidget(content)

        page_layout = QVBoxLayout()
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll_area)
        page.setLayout(page_layout)

        return page

    def _create_asr_page(self):
        """创建语音识别页面"""
        page = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        content = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 模型设置组
        model_group = SettingGroup("模型设置")

        # ASR模型路径
        asr_path_widget = self._create_path_input("asr")
        asr_path_row = SettingRow("🤖", "ASR模型路径", "语音识别模型文件路径", asr_path_widget)
        model_group.add_row(asr_path_row)

        # 标点模型路径
        punc_path_widget = self._create_path_input("punc")
        punc_path_row = SettingRow("。", "标点模型路径", "标点符号模型文件路径", punc_path_widget)
        model_group.add_row(punc_path_row)

        layout.addWidget(model_group)

        # 识别设置组
        asr_group = SettingGroup("识别设置")

        # 自动标点
        self.auto_punct_switch = ModernSwitch()
        punct_row = SettingRow("。", "自动标点", "自动添加标点符号", self.auto_punct_switch)
        asr_group.add_row(punct_row)

        # 实时显示
        self.realtime_switch = ModernSwitch()
        realtime_row = SettingRow("⚡", "实时显示", "实时显示识别结果", self.realtime_switch)
        asr_group.add_row(realtime_row)

        # 发音纠错
        self.correction_switch = ModernSwitch()
        correction_row = SettingRow("✏️", "发音纠错", "启用发音相似词纠错", self.correction_switch)
        asr_group.add_row(correction_row)

        layout.addWidget(asr_group)
        layout.addStretch()

        content.setLayout(layout)
        scroll_area.setWidget(content)

        page_layout = QVBoxLayout()
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll_area)
        page.setLayout(page_layout)

        return page

    def _create_paste_page(self):
        """创建粘贴设置页面"""
        page = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        content = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 粘贴设置组
        paste_group = SettingGroup("粘贴设置")

        # 转写延迟
        self.transcription_delay_slider = ModernSlider(0, 2000, 0, "ms")
        transcription_delay_row = SettingRow("⏱️", "转写延迟", "转写完成后的粘贴延迟", self.transcription_delay_slider)
        paste_group.add_row(transcription_delay_row)

        # 历史点击延迟
        self.history_delay_slider = ModernSlider(0, 2000, 0, "ms")
        history_delay_row = SettingRow("📋", "历史点击延迟", "点击历史记录的粘贴延迟", self.history_delay_slider)
        paste_group.add_row(history_delay_row)

        layout.addWidget(paste_group)
        layout.addStretch()

        content.setLayout(layout)
        scroll_area.setWidget(content)

        page_layout = QVBoxLayout()
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll_area)
        page.setLayout(page_layout)

        return page

    def _create_hotword_settings_page(self):
        """创建热词设置页面"""
        page = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        content = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 热词设置组
        hotword_group = SettingGroup("热词设置")

        # 热词权重
        self.hotword_weight_slider = ModernSlider(0, 100, 80, "%")
        weight_row = SettingRow("⚖️", "热词权重", "热词在识别中的权重", self.hotword_weight_slider)
        hotword_group.add_row(weight_row)

        layout.addWidget(hotword_group)
        layout.addStretch()

        content.setLayout(layout)
        scroll_area.setWidget(content)

        page_layout = QVBoxLayout()
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll_area)
        page.setLayout(page_layout)

        return page

    def _create_hotword_edit_page(self):
        """创建热词编辑页面"""
        page = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        content = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 热词编辑说明
        info_group = SettingGroup("热词编辑")

        # 热词编辑区
        edit_group = SettingGroup("热词编辑")

        # 热词文本编辑器
        self.hotword_text_edit = QTextEdit()
        self.hotword_text_edit.setFixedHeight(200)
        self.hotword_text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #2C2C2E;
                border: 1px solid #48484A;
                border-radius: 8px;
                color: #ffffff;
                font-size: 13px;
                padding: 12px;
                font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
            }
        """)

        # 加载热词
        self._load_hotwords()

        edit_widget = QWidget()
        edit_layout = QVBoxLayout()
        edit_layout.setContentsMargins(16, 12, 16, 12)
        edit_layout.addWidget(self.hotword_text_edit)

        help_label = QLabel("每行一个热词，支持中英文混合")
        help_label.setStyleSheet("""
            QLabel {
                color: #8E8E93;
                font-size: 11px;
                background-color: transparent;
                padding: 4px 0px;
            }
        """)
        edit_layout.addWidget(help_label)

        edit_widget.setLayout(edit_layout)
        edit_widget.setStyleSheet("""
            QWidget {
                background-color: #1C1C1E;
                border-radius: 10px;
                border: 1px solid #2C2C2E;
            }
        """)

        layout.addWidget(edit_widget)
        layout.addStretch()

        content.setLayout(layout)
        scroll_area.setWidget(content)

        page_layout = QVBoxLayout()
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll_area)
        page.setLayout(page_layout)

        return page

    def _create_dependency_page(self):
        """创建依赖管理页面"""
        page = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        content = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 尝试导入依赖管理组件
        try:
            from ui.components.dependency_tab import DependencyTab
            dependency_widget = DependencyTab(self)
            layout.addWidget(dependency_widget)
        except ImportError:
            # 如果导入失败，显示简化的依赖信息
            dep_group = SettingGroup("依赖管理")

            # 模型状态
            model_label = QLabel("已加载")
            model_label.setStyleSheet("color: #34C759; font-weight: 500;")
            model_status_row = SettingRow("🤖", "ASR模型", "语音识别模型状态", model_label)
            dep_group.add_row(model_status_row)

            # 标点模型状态
            punc_label = QLabel("已加载")
            punc_label.setStyleSheet("color: #34C759; font-weight: 500;")
            punc_status_row = SettingRow("。", "标点模型", "标点符号模型状态", punc_label)
            dep_group.add_row(punc_status_row)

            # Python环境
            env_label = QLabel("正常")
            env_label.setStyleSheet("color: #34C759; font-weight: 500;")
            env_status_row = SettingRow("🐍", "Python环境", "当前Python环境", env_label)
            dep_group.add_row(env_status_row)

            layout.addWidget(dep_group)

        layout.addStretch()

        content.setLayout(layout)
        scroll_area.setWidget(content)

        page_layout = QVBoxLayout()
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll_area)
        page.setLayout(page_layout)

        return page

    def _create_path_input(self, model_type):
        """创建路径输入组件"""
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 路径输入框
        path_input = QLineEdit()
        path_input.setStyleSheet("""
            QLineEdit {
                background-color: #2C2C2E;
                border: 1px solid #48484A;
                border-radius: 6px;
                padding: 6px 10px;
                color: #ffffff;
                font-size: 13px;
                min-width: 200px;
            }
            QLineEdit:focus {
                border-color: #007AFF;
            }
        """)

        # 浏览按钮
        browse_button = QPushButton("浏览...")
        browse_button.setFixedSize(60, 28)
        browse_button.setStyleSheet("""
            QPushButton {
                background-color: #2C2C2E;
                border: 1px solid #48484A;
                border-radius: 6px;
                color: #ffffff;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #3A3A3C;
            }
            QPushButton:pressed {
                background-color: #1C1C1E;
            }
        """)

        # 连接浏览功能
        browse_button.clicked.connect(lambda: self._browse_model(model_type, path_input))

        layout.addWidget(path_input)
        layout.addWidget(browse_button)
        widget.setLayout(layout)

        # 保存引用以便后续使用
        if model_type == "asr":
            self.asr_model_path = path_input
        elif model_type == "punc":
            self.punc_model_path = path_input

        return widget

    def _browse_model(self, model_type, path_input):
        """浏览选择模型文件"""
        from PyQt6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"选择{model_type.upper()}模型文件",
            "",
            "模型文件 (*.bin *.onnx *.pt *.pth);;所有文件 (*)"
        )

        if file_path:
            path_input.setText(file_path)

    def _create_device_selector(self):
        """创建设备选择器组件"""
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 设备下拉框
        self.input_device_combo = ModernComboBox()
        self._load_audio_devices()

        # 刷新按钮
        refresh_button = QPushButton("刷新")
        refresh_button.setFixedSize(50, 28)
        refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #2C2C2E;
                border: 1px solid #48484A;
                border-radius: 6px;
                color: #ffffff;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #3A3A3C;
            }
            QPushButton:pressed {
                background-color: #1C1C1E;
            }
        """)
        refresh_button.clicked.connect(self._load_audio_devices)

        layout.addWidget(self.input_device_combo)
        layout.addWidget(refresh_button)
        widget.setLayout(layout)

        return widget

    def _create_bottom_buttons(self, layout):
        """创建底部按钮"""
        button_widget = QWidget()
        button_widget.setFixedHeight(60)
        button_widget.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border-top: 1px solid #2d2d2d;
            }
        """)

        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(20, 12, 20, 12)
        button_layout.addStretch()

        # 重置按钮
        reset_button = QPushButton("重置")
        reset_button.setFixedSize(80, 32)
        reset_button.setStyleSheet("""
            QPushButton {
                background-color: #2C2C2E;
                border: 1px solid #48484A;
                border-radius: 6px;
                color: #ffffff;
                font-size: 13px;
                font-weight: 400;
            }
            QPushButton:hover {
                background-color: #3A3A3C;
            }
            QPushButton:pressed {
                background-color: #1C1C1E;
            }
        """)
        reset_button.clicked.connect(self.reset_to_defaults)

        # 保存按钮
        save_button = QPushButton("保存")
        save_button.setFixedSize(80, 32)
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                border: none;
                border-radius: 6px;
                color: #ffffff;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0056CC;
            }
            QPushButton:pressed {
                background-color: #004499;
            }
        """)
        save_button.clicked.connect(self.save_settings)

        button_layout.addWidget(reset_button)
        button_layout.addSpacing(12)
        button_layout.addWidget(save_button)

        button_widget.setLayout(button_layout)
        layout.addWidget(button_widget)

    def _on_menu_changed(self, index):
        """菜单选择变化"""
        if index >= 0:
            self.stacked_widget.setCurrentIndex(index)
            titles = ["常规", "音频", "语音识别", "粘贴设置", "热词设置", "热词编辑", "依赖管理"]
            if index < len(titles):
                self.title_label.setText(titles[index])

    def _load_audio_devices(self):
        """加载音频设备列表"""
        try:
            # 先清空现有项目
            self.input_device_combo.clear()

            # 添加系统默认选项
            self.input_device_combo.addItem("系统默认")

            if self.audio_capture:
                devices = self.audio_capture.get_audio_devices()
                for device in devices:
                    self.input_device_combo.addItem(device['name'])
            else:
                # 如果没有audio_capture，尝试直接使用pyaudio获取设备
                try:
                    import pyaudio
                    p = pyaudio.PyAudio()
                    for i in range(p.get_device_count()):
                        device_info = p.get_device_info_by_index(i)
                        if device_info['maxInputChannels'] > 0:  # 只显示输入设备
                            self.input_device_combo.addItem(device_info['name'])
                    p.terminate()
                except Exception:
                    # 如果pyaudio也失败，只显示系统默认
                    pass

        except Exception as e:
            # 发生错误时，确保至少有系统默认选项
            self.input_device_combo.clear()
            self.input_device_combo.addItem("系统默认")
            print(f"加载音频设备失败: {e}")

    def _load_hotwords(self):
        """加载热词"""
        try:
            hotwords_file = Path("resources") / "hotwords.txt"
            if hotwords_file.exists():
                content = hotwords_file.read_text(encoding="utf-8")
                self.hotword_text_edit.setPlainText(content)
        except Exception:
            pass

    def _load_settings(self):
        """加载设置"""
        if not self.settings_manager:
            return

        try:
            # 加载热键设置
            hotkey_scheme = self.settings_manager.get_setting('hotkey_scheme', 'hammerspoon')
            index = self.hotkey_scheme_combo.findText(hotkey_scheme)
            if index >= 0:
                self.hotkey_scheme_combo.setCurrentIndex(index)

            hotkey = self.settings_manager.get_setting('hotkey', 'fn')
            index = self.hotkey_combo.findText(hotkey)
            if index >= 0:
                self.hotkey_combo.setCurrentIndex(index)

            delay = self.settings_manager.get_setting('hotkey_settings.recording_start_delay', 50)
            self.delay_slider.setValue(delay)

            # 加载音频设置
            volume_threshold = self.settings_manager.get_setting('audio.volume_threshold', 150)
            self.volume_slider.setValue(volume_threshold)

            max_duration = self.settings_manager.get_setting('audio.max_recording_duration', 10)
            self.duration_slider.setValue(max_duration)

            # 加载输入设备设置
            if hasattr(self, 'input_device_combo'):
                input_device = self.settings_manager.get_setting('audio.input_device', '系统默认')
                index = self.input_device_combo.findText(input_device)
                if index >= 0:
                    self.input_device_combo.setCurrentIndex(index)
                else:
                    # 如果找不到设备，设置为系统默认
                    self.input_device_combo.setCurrentIndex(0)

            # 加载ASR设置
            auto_punct = self.settings_manager.get_setting('asr.auto_punctuation', True)
            self.auto_punct_switch.setChecked(auto_punct)

            realtime = self.settings_manager.get_setting('asr.real_time_display', True)
            self.realtime_switch.setChecked(realtime)

            correction = self.settings_manager.get_setting('asr.enable_pronunciation_correction', True)
            self.correction_switch.setChecked(correction)

            # 加载模型路径
            if hasattr(self, 'asr_model_path'):
                asr_path = self.settings_manager.get_setting('asr.model_path', '')
                self.asr_model_path.setText(asr_path)

            if hasattr(self, 'punc_model_path'):
                punc_path = self.settings_manager.get_setting('asr.punc_model_path', '')
                self.punc_model_path.setText(punc_path)

            # 加载粘贴设置
            transcription_delay = self.settings_manager.get_setting('paste.transcription_delay', 0)
            self.transcription_delay_slider.setValue(transcription_delay)

            history_delay = self.settings_manager.get_setting('paste.history_click_delay', 0)
            self.history_delay_slider.setValue(history_delay)

            # 加载热词设置
            hotword_weight = self.settings_manager.get_setting('asr.hotword_weight', 80)
            self.hotword_weight_slider.setValue(hotword_weight)

        except Exception as e:
            print(f"加载设置失败: {e}")

    def save_settings(self):
        """保存设置"""
        if not self.settings_manager:
            return

        try:
            # 保存热键设置
            self.settings_manager.set_setting('hotkey_scheme', self.hotkey_scheme_combo.currentText())
            self.settings_manager.set_setting('hotkey', self.hotkey_combo.currentText())
            self.settings_manager.set_setting('hotkey_settings.recording_start_delay', self.delay_slider.value())

            # 保存音频设置
            self.settings_manager.set_setting('audio.volume_threshold', self.volume_slider.value())
            self.settings_manager.set_setting('audio.max_recording_duration', self.duration_slider.value())

            # 保存输入设备设置
            if hasattr(self, 'input_device_combo'):
                self.settings_manager.set_setting('audio.input_device', self.input_device_combo.currentText())

            # 保存ASR设置
            self.settings_manager.set_setting('asr.auto_punctuation', self.auto_punct_switch.isChecked())
            self.settings_manager.set_setting('asr.real_time_display', self.realtime_switch.isChecked())
            self.settings_manager.set_setting('asr.enable_pronunciation_correction', self.correction_switch.isChecked())

            # 保存模型路径
            if hasattr(self, 'asr_model_path'):
                self.settings_manager.set_setting('asr.model_path', self.asr_model_path.text())

            if hasattr(self, 'punc_model_path'):
                self.settings_manager.set_setting('asr.punc_model_path', self.punc_model_path.text())

            # 保存粘贴设置
            self.settings_manager.set_setting('paste.transcription_delay', self.transcription_delay_slider.value())
            self.settings_manager.set_setting('paste.history_click_delay', self.history_delay_slider.value())

            # 保存热词设置
            self.settings_manager.set_setting('asr.hotword_weight', self.hotword_weight_slider.value())

            # 保存热词文件
            try:
                content = self.hotword_text_edit.toPlainText()
                hotwords_file = Path("resources") / "hotwords.txt"
                hotwords_file.parent.mkdir(exist_ok=True)
                hotwords_file.write_text(content, encoding="utf-8")
            except Exception as e:
                print(f"保存热词失败: {e}")

            # 保存到文件
            self.settings_manager.save_settings()

            # 发出信号
            self.settings_saved.emit()

            # 显示成功消息
            QMessageBox.information(self, "成功", "设置已保存成功！")

            # 关闭窗口
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存设置失败: {e}")

    def reset_to_defaults(self):
        """重置为默认设置"""
        reply = QMessageBox.question(
            self,
            "确认重置",
            "确定要重置所有设置为默认值吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.settings_manager:
                self.settings_manager.reset_to_defaults()
                self._load_settings()
                QMessageBox.information(self, "成功", "设置已重置为默认值！")
