from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QComboBox, QPushButton, QGroupBox,
                            QCheckBox, QSlider, QListWidget, QListWidgetItem,
                            QLineEdit, QFileDialog, QTextEdit, QMessageBox, QDialog,
                            QStackedWidget, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect, QRectF, pyqtProperty
from PyQt6.QtGui import QFont, QPalette, QColor, QPainter, QBrush, QPen, QFontMetrics
from pathlib import Path
import pyaudio


class MacOSSwitch(QWidget):
    """macOS风格的开关控件"""
    toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(36, 20)  # macOS开关的标准尺寸：宽36px，高20px
        self._checked = False
        self._position = 2  # 初始位置
        self._animation = QPropertyAnimation(self, b"position")
        self._animation.setDuration(150)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制背景轨道 - 使用macOS标准色值
        track_rect = QRectF(0, 0, self.width(), self.height())
        track_color = QColor("#0A84FF") if self._checked else QColor("#48484A")
        painter.setBrush(QBrush(track_color))
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.drawRoundedRect(track_rect, 10, 10)  # 全圆角

        # 绘制滑块 - 添加阴影效果
        knob_size = 16
        knob_x = self._position
        knob_y = 2

        # 绘制阴影
        shadow_rect = QRectF(knob_x + 0.5, knob_y + 0.5, knob_size, knob_size)
        painter.setBrush(QBrush(QColor(0, 0, 0, 30)))
        painter.drawEllipse(shadow_rect)

        # 绘制滑块
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
        start_pos = 2 if not self._checked else 18  # 调整为36px宽度的位置
        end_pos = 18 if self._checked else 2

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


class MacOSSlider(QWidget):
    """macOS风格的滑块组件 - 像素级还原"""
    valueChanged = pyqtSignal(int)

    def __init__(self, minimum=0, maximum=100, value=50, left_label="慢", right_label="快", parent=None):
        super().__init__(parent)
        self.minimum = minimum
        self.maximum = maximum
        self._value = value
        self.left_label = left_label
        self.right_label = right_label
        self.setFixedHeight(40)
        self.setMinimumWidth(200)

        # 拖拽状态
        self.dragging = False
        self.hover = False

    def value(self):
        return self._value

    def setValue(self, value):
        value = max(self.minimum, min(self.maximum, value))
        if value != self._value:
            self._value = value
            self.valueChanged.emit(value)
            self.update()

    def setRange(self, minimum, maximum):
        self.minimum = minimum
        self.maximum = maximum
        self.setValue(self._value)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 计算滑块区域
        rect = self.rect()
        label_width = 30
        slider_rect = QRect(label_width, 15, rect.width() - 2 * label_width, 10)

        # 绘制左右标签
        painter.setPen(QColor("#A0A0A0"))
        painter.setFont(QFont("SF Pro Text", 11))

        # 左标签
        painter.drawText(QRect(0, 0, label_width - 5, rect.height()),
                        Qt.AlignmentFlag.AlignCenter, self.left_label)

        # 右标签
        painter.drawText(QRect(rect.width() - label_width + 5, 0, label_width - 5, rect.height()),
                        Qt.AlignmentFlag.AlignCenter, self.right_label)

        # 绘制刻度线
        self._draw_ticks(painter, slider_rect)

        # 绘制轨道
        track_rect = QRect(slider_rect.x(), slider_rect.y() + 4, slider_rect.width(), 2)

        # 未填充部分
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#48484A")))
        painter.drawRoundedRect(track_rect, 1, 1)

        # 计算手柄位置
        progress = (self._value - self.minimum) / (self.maximum - self.minimum)
        handle_x = slider_rect.x() + progress * slider_rect.width()

        # 填充部分
        if progress > 0:
            filled_rect = QRect(track_rect.x(), track_rect.y(),
                              int(handle_x - slider_rect.x()), track_rect.height())
            painter.setBrush(QBrush(QColor("#0A84FF")))
            painter.drawRoundedRect(filled_rect, 1, 1)

        # 绘制手柄
        self._draw_handle(painter, handle_x, slider_rect.y() + 5)

    def _draw_ticks(self, painter, slider_rect):
        """绘制刻度线"""
        painter.setPen(QPen(QColor("#48484A"), 1))

        # 绘制主要刻度（5个）
        for i in range(6):
            x = slider_rect.x() + i * slider_rect.width() / 5
            painter.drawLine(int(x), slider_rect.y() + 1, int(x), slider_rect.y() + 8)

        # 绘制次要刻度
        painter.setPen(QPen(QColor("#2a2a2a"), 1))
        for i in range(11):
            if i % 2 == 1:  # 跳过主要刻度位置
                x = slider_rect.x() + i * slider_rect.width() / 10
                painter.drawLine(int(x), slider_rect.y() + 2, int(x), slider_rect.y() + 7)

    def _draw_handle(self, painter, x, y):
        """绘制手柄"""
        # 手柄大小根据状态调整
        if self.dragging:
            size = 11
        elif self.hover:
            size = 13
        else:
            size = 12

        handle_rect = QRect(int(x - size/2), int(y - size/2), size, size)

        # 阴影效果
        shadow_rect = QRect(handle_rect.x() + 1, handle_rect.y() + 1, size, size)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 30)))
        painter.drawEllipse(shadow_rect)

        # 手柄主体
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.drawEllipse(handle_rect)

        # 存储手柄位置用于鼠标事件
        self.handle_rect = handle_rect

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # 检查是否点击在手柄上
            if hasattr(self, 'handle_rect') and self.handle_rect.contains(event.pos()):
                self.dragging = True
                self.update()
            else:
                # 点击轨道，跳转到该位置
                self._update_value_from_position(event.pos().x())

    def mouseMoveEvent(self, event):
        if self.dragging:
            self._update_value_from_position(event.pos().x())
        else:
            # 检查鼠标悬停
            old_hover = self.hover
            if hasattr(self, 'handle_rect'):
                self.hover = self.handle_rect.contains(event.pos())
                if old_hover != self.hover:
                    self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            self.update()

    def leaveEvent(self, event):
        self.hover = False
        self.update()

    def _update_value_from_position(self, x):
        """根据鼠标位置更新值"""
        label_width = 30
        slider_width = self.width() - 2 * label_width
        relative_x = max(0, min(slider_width, x - label_width))
        progress = relative_x / slider_width
        new_value = self.minimum + progress * (self.maximum - self.minimum)
        self.setValue(int(new_value))


class MacOSComboBox(QComboBox):
    """macOS风格的下拉列表组件 - 像素级还原"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(32)
        self.setMinimumWidth(120)
        self._setup_style()

    def _setup_style(self):
        """设置macOS风格样式"""
        self.setStyleSheet("""
            QComboBox {
                background-color: #3a3a3a;
                border: 1px solid #4a4a4a;
                border-radius: 6px;
                padding: 6px 12px 6px 12px;
                color: #ffffff;
                font-size: 13px;
                font-weight: 400;
                selection-background-color: transparent;
            }

            QComboBox:hover {
                background-color: #404040;
                border-color: #5a5a5a;
            }

            QComboBox:pressed {
                background-color: #353535;
                border-color: #007AFF;
            }

            QComboBox::drop-down {
                border: none;
                width: 20px;
                subcontrol-origin: padding;
                subcontrol-position: top right;
            }

            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #8a8a8a;
                width: 0;
                height: 0;
                margin-right: 6px;
            }

            QComboBox QAbstractItemView {
                background-color: #2a2a2a;
                border: 1px solid #4a4a4a;
                border-radius: 8px;
                padding: 0px;
                outline: none;
                selection-background-color: #007AFF;
                selection-color: #ffffff;
                margin: 0px;
                show-decoration-selected: 0;
            }

            QComboBox QAbstractItemView::item {
                height: 28px;
                padding: 8px 12px;
                color: #ffffff;
                border: none;
                background-color: transparent;
                border-radius: 6px;
                margin: 2px 4px;
            }

            QComboBox QAbstractItemView::item:selected {
                background-color: #007AFF;
                color: #ffffff;
            }

            QComboBox QAbstractItemView::item:hover {
                background-color: #404040;
            }
        """)

    def paintEvent(self, event):
        """使用CSS样式绘制箭头"""
        super().paintEvent(event)


class MacOSComboBoxWithCheck(MacOSComboBox):
    """带勾选标记的macOS风格下拉列表"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_check_style()

    def _setup_check_style(self):
        """设置带勾选标记的样式"""
        self.setStyleSheet("""
            QComboBox {
                background-color: #3a3a3a;
                border: 1px solid #4a4a4a;
                border-radius: 6px;
                padding: 6px 12px 6px 12px;
                color: #ffffff;
                font-size: 13px;
                font-weight: 400;
                selection-background-color: transparent;
            }

            QComboBox:hover {
                background-color: #404040;
                border-color: #5a5a5a;
            }

            QComboBox:pressed {
                background-color: #353535;
                border-color: #007AFF;
            }

            QComboBox::drop-down {
                border: none;
                width: 20px;
                subcontrol-origin: padding;
                subcontrol-position: top right;
            }

            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #8a8a8a;
                width: 0;
                height: 0;
                margin-right: 6px;
            }

            QComboBox QAbstractItemView {
                background-color: #2a2a2a;
                border: 1px solid #4a4a4a;
                border-radius: 8px;
                padding: 0px;
                outline: none;
                selection-background-color: #007AFF;
                selection-color: #ffffff;
                margin: 0px;
                show-decoration-selected: 0;
            }

            QComboBox QAbstractItemView::item {
                height: 28px;
                padding: 8px 12px 8px 28px;
                color: #ffffff;
                border: none;
                background-color: transparent;
                border-radius: 6px;
                margin: 2px 4px;
            }

            QComboBox QAbstractItemView::item:selected {
                background-color: #007AFF;
                color: #ffffff;
            }

            QComboBox QAbstractItemView::item:hover {
                background-color: #404040;
            }
        """)

    def showPopup(self):
        """显示下拉菜单时添加勾选标记"""
        super().showPopup()

        # 获取下拉视图
        view = self.view()
        if view:
            # 为当前选中项添加勾选标记
            current_index = self.currentIndex()
            for i in range(self.count()):
                item_text = self.itemText(i)
                if i == current_index:
                    # 添加勾选标记
                    if not item_text.startswith("✓ "):
                        self.setItemText(i, f"✓ {item_text}")
                else:
                    # 移除勾选标记
                    if item_text.startswith("✓ "):
                        self.setItemText(i, item_text[2:])

    def hidePopup(self):
        """隐藏下拉菜单时清理勾选标记"""
        # 清理所有勾选标记
        for i in range(self.count()):
            item_text = self.itemText(i)
            if item_text.startswith("✓ "):
                self.setItemText(i, item_text[2:])

        super().hidePopup()


class MacOSSettingsCard(QWidget):
    """macOS风格的设置卡片组件"""

    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.title = title
        self.setFixedHeight(80)
        self._setup_style()
        self._setup_layout()

    def _setup_style(self):
        """设置卡片样式"""
        self.setStyleSheet("""
            MacOSSettingsCard {
                background-color: #3a3a3a;
                border-radius: 12px;
                border: 1px solid #4a4a4a;
            }
        """)

    def _setup_layout(self):
        """设置布局"""
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(20, 16, 20, 16)
        self.layout.setSpacing(16)
        self.setLayout(self.layout)

    def add_content(self, widget):
        """添加内容到卡片"""
        self.layout.addWidget(widget)


class MacOSSliderCard(MacOSSettingsCard):
    """macOS风格的滑块设置卡片"""

    def __init__(self, title, description, min_val, max_val, current_val,
                 unit="ms", suggestion="", parent=None):
        super().__init__(title, parent)
        self.title = title
        self.description = description
        self.unit = unit
        self.suggestion = suggestion
        self._create_content(min_val, max_val, current_val)

    def _create_content(self, min_val, max_val, current_val):
        """创建滑块卡片内容"""
        # 左侧内容区域
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        # 标题
        title_label = QLabel(self.title)
        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 15px;
                font-weight: 600;
                background-color: transparent;
            }
        """)

        # 描述和建议
        desc_text = self.description
        if self.suggestion:
            desc_text += f"  {self.suggestion}"

        desc_label = QLabel(desc_text)
        desc_label.setStyleSheet("""
            QLabel {
                color: #8a8a8a;
                font-size: 12px;
                background-color: transparent;
            }
        """)
        desc_label.setWordWrap(True)

        left_layout.addWidget(title_label)
        left_layout.addWidget(desc_label)
        left_widget.setLayout(left_layout)

        # 中间滑块
        self.slider = MacOSSlider(min_val, max_val, current_val, "", "")
        self.slider.setFixedWidth(300)

        # 右侧数值显示
        self.value_label = QLabel(f"{current_val}{self.unit}")
        self.value_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 15px;
                font-weight: 500;
                background-color: transparent;
                min-width: 50px;
            }
        """)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # 连接信号
        self.slider.valueChanged.connect(
            lambda value: self.value_label.setText(f"{value}{self.unit}")
        )

        # 添加到布局
        self.layout.addWidget(left_widget, 1)
        self.layout.addWidget(self.slider)
        self.layout.addWidget(self.value_label)


class MacOSSwitchCard(MacOSSettingsCard):
    """macOS风格的开关设置卡片"""

    def __init__(self, title, description, checked=False, parent=None):
        super().__init__(title, parent)
        self.title = title
        self.description = description
        self._create_content(checked)

    def _create_content(self, checked):
        """创建开关卡片内容"""
        # 左侧内容区域
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        # 标题
        title_label = QLabel(self.title)
        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 15px;
                font-weight: 600;
                background-color: transparent;
            }
        """)

        # 描述
        desc_label = QLabel(self.description)
        desc_label.setStyleSheet("""
            QLabel {
                color: #8a8a8a;
                font-size: 12px;
                background-color: transparent;
            }
        """)
        desc_label.setWordWrap(True)

        left_layout.addWidget(title_label)
        left_layout.addWidget(desc_label)
        left_widget.setLayout(left_layout)

        # 右侧开关
        self.switch = MacOSSwitch()
        self.switch.setChecked(checked)

        # 添加到布局
        self.layout.addWidget(left_widget, 1)
        self.layout.addWidget(self.switch)


# 导入依赖管理组件
try:
    from .components.dependency_tab import DependencyTab
except ImportError:
    # 如果导入失败，创建一个占位符组件
    class DependencyTab(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            layout = QVBoxLayout()
            layout.addWidget(QLabel("依赖管理功能暂不可用"))
            self.setLayout(layout)

class MacOSSettingsWindow(QDialog):
    """macOS风格的设置窗口"""
    # 定义信号
    settings_changed = pyqtSignal(str, object)  # 当任何设置改变时发出信号
    settings_saved = pyqtSignal()  # 当设置保存时发出信号

    def __init__(self, parent=None, settings_manager=None, audio_capture=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.audio_capture = audio_capture
        self.audio = None
        
        # 设置窗口基本属性 - 严格按照macOS系统设置规范
        self.setWindowTitle("设置")
        self.setMinimumSize(960, 680)  # 240px左侧栏 + 720px内容区
        self.setModal(True)

        # 设置窗口背景色 - 使用macOS Dark Mode标准色值
        self.setStyleSheet("QDialog { background-color: #1C1C1E; }")
        
        # 初始化UI
        self._setup_ui()
    
    def _load_settings(self):
        """从设置管理器加载设置到UI控件"""
        try:
            settings = self.settings_manager
            
            # 加载热键方案 - 修复属性名称错误
            if hasattr(self, 'hotkey_scheme_combo'):
                hotkey_scheme = settings.get_setting('hotkey_scheme', 'hammerspoon')
                index = self.hotkey_scheme_combo.findText(hotkey_scheme)
                if index >= 0:
                    self.hotkey_scheme_combo.setCurrentIndex(index)
            
            # 加载快捷键
            if hasattr(self, 'hotkey_combo'):
                shortcut = settings.get_setting('hotkey', 'fn')
                index = self.hotkey_combo.findText(shortcut)
                if index >= 0:
                    self.hotkey_combo.setCurrentIndex(index)
            
            # 加载音频设备
            input_device = settings.get_setting('input_device', '系统默认')
            index = self.input_device.findText(input_device)
            if index >= 0:
                self.input_device.setCurrentIndex(index)
            else:
                # 如果找不到设备，尝试部分匹配
                for i in range(self.input_device.count()):
                    if input_device in self.input_device.itemText(i):
                        self.input_device.setCurrentIndex(i)
                        break
            
            # 加载音量阈值
            if hasattr(self, 'volume_threshold'):
                volume_threshold = settings.get_setting('audio.volume_threshold', 150)
                # 将0-1000的值转换为0-20范围
                slider_value = int(volume_threshold * 20 / 1000)
                self.volume_threshold.setValue(slider_value)
            
            # 加载最大录音时长
            max_record_time = settings.get_setting('audio.max_recording_duration', 10)
            if hasattr(self, 'recording_duration'):
                self.recording_duration.setValue(int(max_record_time))
            
            # 加载ASR模型路径
            if hasattr(self, 'asr_model_path'):
                asr_model_path = settings.get_setting('asr.model_path', '')
                self.asr_model_path.setText(asr_model_path)

            # 加载标点模型路径
            if hasattr(self, 'punc_model_path'):
                punc_model_path = settings.get_setting('asr.punc_model_path', '')
                self.punc_model_path.setText(punc_model_path)

            # 加载自动标点设置
            if hasattr(self, 'auto_punctuation'):
                auto_punctuation = settings.get_setting('asr.auto_punctuation', True)
                self.auto_punctuation.setChecked(auto_punctuation)

            # 加载实时显示设置
            if hasattr(self, 'real_time_display'):
                real_time_display = settings.get_setting('asr.real_time_display', True)
                self.real_time_display.setChecked(real_time_display)
            
            # 加载粘贴延迟设置
            if hasattr(self, 'transcription_delay'):
                paste_delay = settings.get_setting('paste.transcription_delay', 0)
                self.transcription_delay.setValue(int(paste_delay))

            if hasattr(self, 'history_delay'):
                history_paste_delay = settings.get_setting('paste.history_click_delay', 0)
                self.history_delay.setValue(int(history_paste_delay))

            # 加载热词权重
            if hasattr(self, 'hotword_weight'):
                hotword_weight = settings.get_setting('asr.hotword_weight', 80)
                self.hotword_weight.setValue(int(hotword_weight))

            # 加载发音校正设置
            if hasattr(self, 'pronunciation_correction'):
                pronunciation_correction = settings.get_setting('asr.enable_pronunciation_correction', True)
                self.pronunciation_correction.setChecked(pronunciation_correction)
            
        except Exception as e:
            import logging
            logging.error(f"加载设置失败: {e}")
    
    def save_settings(self):
        """保存所有设置"""
        try:
            settings = self.settings_manager
            
            # 保存热键方案
            if hasattr(self, 'hotkey_scheme_combo'):
                settings.set_setting('hotkey_scheme', self.hotkey_scheme_combo.currentText())
            
            # 保存快捷键
            if hasattr(self, 'hotkey_combo'):
                settings.set_setting('hotkey', self.hotkey_combo.currentText())

            # 保存热键延迟设置
            if hasattr(self, 'recording_start_delay'):
                settings.set_setting('hotkey_settings.recording_start_delay', self.recording_start_delay.value())
            
            # 保存音频设备
            if hasattr(self, 'input_device'):
                device_text = self.input_device.currentText()
                if device_text.startswith("系统默认"):
                    device_name = None
                else:
                    device_name = device_text
                settings.set_setting('audio.input_device', device_name)

            # 保存音量阈值
            if hasattr(self, 'volume_threshold'):
                # 将滑块值转换为正确的范围
                volume_value = int(self.volume_threshold.value() * 1000 / 20)
                settings.set_setting('audio.volume_threshold', volume_value)
            
            # 保存最大录音时长
            if hasattr(self, 'recording_duration'):
                settings.set_setting('audio.max_recording_duration', self.recording_duration.value())
            
            # 保存ASR模型路径
            if hasattr(self, 'asr_model_path'):
                settings.set_setting('asr.model_path', self.asr_model_path.text())

            # 保存标点模型路径
            if hasattr(self, 'punc_model_path'):
                settings.set_setting('asr.punc_model_path', self.punc_model_path.text())

            # 保存自动标点设置
            if hasattr(self, 'auto_punctuation'):
                settings.set_setting('asr.auto_punctuation', self.auto_punctuation.isChecked())

            # 保存实时显示设置
            if hasattr(self, 'real_time_display'):
                settings.set_setting('asr.real_time_display', self.real_time_display.isChecked())
            
            # 保存粘贴延迟设置
            if hasattr(self, 'transcription_delay'):
                settings.set_setting('paste.transcription_delay', self.transcription_delay.value())
            if hasattr(self, 'history_delay'):
                settings.set_setting('paste.history_click_delay', self.history_delay.value())
            
            # 保存热词权重
            if hasattr(self, 'hotword_weight'):
                settings.set_setting('asr.hotword_weight', self.hotword_weight.value())
            
            # 保存发音校正设置
            if hasattr(self, 'pronunciation_correction'):
                settings.set_setting('asr.enable_pronunciation_correction', self.pronunciation_correction.isChecked())

            # 保存热词
            if hasattr(self, 'hotword_text_edit'):
                try:
                    content = self.hotword_text_edit.toPlainText()
                    hotwords_file = Path("resources") / "hotwords.txt"
                    hotwords_file.parent.mkdir(exist_ok=True)
                    hotwords_file.write_text(content, encoding="utf-8")

                    # 重新加载热词
                    if hasattr(self.parent, 'state_manager'):
                        if hasattr(self.parent.state_manager, 'reload_hotwords'):
                            self.parent.state_manager.reload_hotwords()
                except Exception as e:
                    import logging
                    logging.error(f"保存热词失败: {e}")
                    QMessageBox.warning(self, "警告", f"保存热词失败: {e}")

            # 保存设置到文件
            settings.save_settings()

            # 发出设置已保存的信号，通知主应用程序应用新设置
            self.settings_saved.emit()

            # 通知用户保存成功
            QMessageBox.information(self, "成功", "设置已保存成功！")

            # 关闭窗口
            self.accept()
            
        except Exception as e:
            import logging
            logging.error(f"保存设置失败: {e}")
            QMessageBox.critical(self, "错误", f"保存设置失败: {e}")
    
    def reset_to_defaults(self):
        """重置所有设置为默认值"""
        reply = QMessageBox.question(
            self, 
            "确认重置", 
            "确定要将所有设置重置为默认值吗？\n\n此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 重置热键方案
                self.hotkey_scheme_combo.setCurrentText('python')
                
                # 重置快捷键
                self.shortcut_edit.setText('F1')
                
                # 重置快捷键延迟
                if hasattr(self, 'shortcut_delay'):
                    self.shortcut_delay.setValue(100)  # 0.1秒 = 100毫秒

                # 重置音频设备为第一个（通常是系统默认）
                if self.input_device.count() > 0:
                    self.input_device.setCurrentIndex(0)

                # 重置音量阈值
                if hasattr(self, 'volume_threshold'):
                    self.volume_threshold.setValue(1)  # 对应0.01的阈值
                
                # 重置最大录音时长
                if hasattr(self, 'recording_duration'):
                    self.recording_duration.setValue(10)
                
                # 重置模型路径
                self.asr_model_path.setText('')
                self.punc_model_path.setText('')
                
                # 重置自动标点
                self.auto_punctuation.setChecked(True)
                
                # 重置实时显示
                self.real_time_display.setChecked(True)
                
                # 重置粘贴延迟
                if hasattr(self, 'transcription_delay'):
                    self.transcription_delay.setValue(0)
                if hasattr(self, 'history_delay'):
                    self.history_delay.setValue(0)

                # 重置热词权重
                if hasattr(self, 'hotword_weight'):
                    self.hotword_weight.setValue(80)

                # 重置发音校正
                if hasattr(self, 'pronunciation_correction'):
                    self.pronunciation_correction.setChecked(True)
                
                QMessageBox.information(self, "成功", "设置已重置为默认值！")
                
            except Exception as e:
                import logging
                logging.error(f"重置设置失败: {e}")
                QMessageBox.critical(self, "错误", f"重置设置失败: {e}")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 清理音频资源
        self._cleanup_audio()
        super().closeEvent(event)
        
    def _setup_ui(self):
        """设置UI布局"""
        # 创建主布局 - 参考macOS系统设置
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(1)  # 1px分隔线
        self.setLayout(main_layout)
        
        # 创建左侧菜单
        self._create_sidebar()
        main_layout.addWidget(self.sidebar)
        
        # 创建右侧内容区域
        self._create_content_area()
        main_layout.addWidget(self.content_area)
        
        # 创建底部按钮区域
        self._create_bottom_buttons()
        
        # 设置样式
        self._setup_styles()
        
        # 加载设置
        self._load_settings()
        
    def _setup_styles(self):
        """设置macOS深色主题样式 - 严格按照设计规范"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1C1C1E;
                color: #FFFFFF;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
            }
            
            QFrame#sidebar {
                background-color: #1C1C1E;
                border-right: 1px solid #3A3A3C;
            }

            QListWidget#menuList {
                background-color: transparent;
                border: none;
                outline: none;
                font-size: 14px;
                padding: 16px 0px;
            }

            QListWidget#menuList::item {
                padding: 8px 16px;
                border: none;
                color: #A0A0A0;
                font-weight: 500;
                font-size: 14px;
                min-height: 28px;
            }

            QListWidget#menuList::item:selected {
                background-color: #0A84FF;
                color: #FFFFFF;
                border-radius: 6px;
                margin: 1px 8px;
                font-weight: 600;
            }

            QListWidget#menuList::item:hover:!selected {
                background-color: #2C2C2E;
                color: #FFFFFF;
                border-radius: 6px;
                margin: 1px 8px;
            }
            
            QFrame#contentArea {
                background-color: #1C1C1E;
                border: none;
                max-width: 720px;
            }

            QFrame#navFrame {
                background-color: transparent;
                border: none;
                border-bottom: 1px solid #3a3a3a;
            }

            QLabel#titleLabel {
                font-size: 20px;
                font-weight: 600;
                color: #FFFFFF;
                margin: 0px;
                padding: 0px;
                background-color: transparent;
            }

            QPushButton#backButton {
                background-color: transparent;
                border: none;
                color: #8a8a8a;
                font-size: 20px;
                font-weight: 300;
                border-radius: 14px;
                padding: 0px;
            }

            QPushButton#backButton:hover {
                background-color: #404040;
                color: #ffffff;
            }

            QPushButton#backButton:pressed {
                background-color: #505050;
            }
            
            QLabel {
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 400;
                line-height: 1.5;
            }

            QLabel[class="help-text"] {
                color: #A0A0A0;
                font-size: 12px;
                font-weight: 400;
                line-height: 1.4;
            }
            
            QGroupBox {
                font-size: 20px;
                font-weight: 600;
                color: #FFFFFF;
                border: none;
                margin-top: 24px;
                margin-bottom: 8px;
                padding-top: 0px;
                background-color: transparent;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 0px;
                padding: 0px 0px 8px 0px;
                background-color: transparent;
                color: #FFFFFF;
                border: none;
                font-weight: 600;
                font-size: 20px;
            }
            
            QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox {
                padding: 4px 10px;
                border: 1px solid #48484A;
                border-radius: 6px;
                background-color: #3A3A3C;
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 400;
                min-height: 28px;
            }

            QComboBox:focus, QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: #0A84FF;
                background-color: #3A3A3C;
                outline: none;
            }

            QComboBox:hover, QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover {
                border-color: #6A6A6C;
                background-color: #3A3A3C;
            }

            QComboBox::drop-down {
                border: none;
                width: 20px;
            }

            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #8a8a8a;
                margin-right: 6px;
            }
            
            QSpinBox::up-button, QDoubleSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #3d3d3d;
                border-bottom: 1px solid #3d3d3d;
                border-top-right-radius: 8px;
                background-color: #3a3a3a;
            }
            
            QSpinBox::down-button, QDoubleSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 20px;
                border-left: 1px solid #3d3d3d;
                border-top: 1px solid #3d3d3d;
                border-bottom-right-radius: 8px;
                background-color: #3a3a3a;
            }
            
            QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 4px solid #e0e0e0;
                width: 0;
                height: 0;
            }
            
            QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #e0e0e0;
                width: 0;
                height: 0;
            }
            
            QComboBox::drop-down {
                border: none;
                background-color: transparent;
                width: 30px;
                subcontrol-origin: padding;
                subcontrol-position: top right;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #8C8C8C;
                width: 0;
                height: 0;
                margin-right: 8px;
                margin-top: 2px;
            }
            
            QComboBox:hover::down-arrow {
                border-top-color: #ffffff;
            }
            
            QComboBox:focus::down-arrow {
                border-top-color: #007AFF;
            }
            
            QComboBox QAbstractItemView {
                background-color: #2c2c2c;
                color: #ffffff;
                border: 1px solid #404040;
                border-radius: 8px;
                selection-background-color: #007AFF;
                selection-color: #ffffff;
                padding: 4px;
                outline: none;
            }
            
            QComboBox QAbstractItemView::item {
                padding: 10px 12px;
                border-radius: 4px;
                margin: 1px;
                color: #ffffff;
            }
            
            QComboBox QAbstractItemView::item:hover {
                background-color: #404040;
            }
            
            QComboBox QAbstractItemView::item:selected {
                background-color: #007AFF;
                color: #ffffff;
            }
            
            QSlider::groove:horizontal {
                border: none;
                height: 4px;
                background-color: #48484A;
                border-radius: 2px;
                margin: 5px 0;
            }

            QSlider::sub-page:horizontal {
                background-color: #0A84FF;
                border-radius: 2px;
                margin: 0px;
            }

            QSlider::add-page:horizontal {
                background-color: #48484A;
                border-radius: 2px;
                margin: 0px;
            }

            QSlider::handle:horizontal {
                background-color: #FFFFFF;
                border: 1px solid rgba(0, 0, 0, 0.1);
                width: 14px;
                height: 14px;
                border-radius: 7px;
                margin: -5px 0;
            }

            QSlider::handle:horizontal:hover {
                background-color: #FFFFFF;
                border: 1px solid rgba(0, 0, 0, 0.15);
                width: 16px;
                height: 16px;
                border-radius: 8px;
                margin: -6px 0;
            }

            QSlider::handle:horizontal:pressed {
                background-color: #f8f8f8;
                border: 0.5px solid #a0a0a0;
                width: 11px;
                height: 11px;
                border-radius: 5.5px;
                margin: -4.5px 0;
            }
            
            QSlider::tick-mark:horizontal {
                background: #666666;
                width: 1px;
                height: 4px;
            }
            
            QCheckBox {
                font-size: 14px;
                color: #ffffff;
                spacing: 10px;
                padding: 4px 2px;
                font-weight: 500;
            }
            
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 1px solid #3A3A3C;
                border-radius: 4px;
                background-color: #2C2C2E;
            }

            QCheckBox::indicator:hover {
                border-color: #0A84FF;
                background-color: #2C2C2E;
            }

            QCheckBox::indicator:checked {
                background-color: #0A84FF;
                border-color: #0A84FF;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTAiIHZpZXdCb3g9IjAgMCAxMiAxMCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEuNSA0LjVMNC41IDcuNUwxMC41IDEuNSIgc3Ryb2tlPSIjRkZGRkZGIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
            }

            QCheckBox::indicator:checked:hover {
                background-color: #0A84FF;
                border-color: #0A84FF;
            }
            
            QCheckBox::indicator:disabled {
                border-color: #404040;
                background-color: #1a1a1a;
            }
            
            QCheckBox:disabled {
                color: #666666;
            }
            
            QTextEdit {
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                background-color: #333333;
                color: #ffffff;
                font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
                font-size: 13px;
                padding: 12px;
                line-height: 1.4;
            }
            
            QTextEdit:focus {
                border-color: #007AFF;
                background-color: #3a3a3a;
                outline: none;
            }
            
            QPushButton {
                background-color: #3A3A3C;
                color: #FFFFFF;
                border: 1px solid #48484A;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 14px;
                font-weight: 500;
                min-height: 28px;
            }

            QPushButton:hover {
                background-color: #48484A;
                border-color: #6A6A6C;
                color: #FFFFFF;
            }

            QPushButton:pressed {
                background-color: #2C2C2E;
                border-color: #0A84FF;
            }
            
            QPushButton#saveButton {
                background-color: #0A84FF;
                border-color: #0A84FF;
                color: #FFFFFF;
                font-weight: 600;
            }
            
            QPushButton#saveButton:hover {
                background-color: #0056CC;
                border-color: #0056CC;
            }
            
            QPushButton#resetButton {
                background-color: #333333;
                border-color: #3d3d3d;
                color: #e0e0e0;
            }
            
            QPushButton#resetButton:hover {
                background-color: #3a3a3a;
                border-color: #4d4d4d;
                color: #ffffff;
            }
            
            QScrollArea {
                border: none;
                background-color: transparent;
            }

            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }

            QStackedWidget#stackedWidget {
                background-color: transparent;
                border: none;
            }

            QStackedWidget#stackedWidget > QWidget {
                background-color: transparent;
                border: none;
            }
            
            QScrollBar:vertical {
                background-color: transparent;
                width: 8px;
                border-radius: 4px;
                margin: 2px;
            }

            QScrollBar::handle:vertical {
                background-color: #5a5a5a;
                border-radius: 4px;
                min-height: 20px;
                margin: 0px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #6a6a6a;
            }

            QScrollBar::handle:vertical:pressed {
                background-color: #4a4a4a;
            }

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }

            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #5d5d5d;
            }
            
            QScrollBar::handle:vertical:pressed {
                background-color: #6d6d6d;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        
    def _create_sidebar(self):
        """创建左侧菜单栏 - 参考macOS系统设置"""
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(240)  # 增加宽度，更接近系统设置
        self.sidebar.setObjectName("sidebar")

        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(0, 0, 0, 0)  # 移除边距
        sidebar_layout.setSpacing(0)
        self.sidebar.setLayout(sidebar_layout)
        
        # 创建菜单列表
        self.menu_list = QListWidget()
        self.menu_list.setObjectName("menuList")
        
        # 添加菜单项
        menu_items = [
            ("常规", "general"),
            ("音频", "audio"),
            ("语音识别", "asr"),
            ("粘贴设置", "paste"),
            ("热词设置", "hotwords"),
            ("热词编辑", "hotwords_edit"),
            ("依赖管理", "dependency")
        ]
        
        for text, key in menu_items:
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, key)
            self.menu_list.addItem(item)
        
        # 设置默认选中第一项
        self.menu_list.setCurrentRow(0)
        
        # 连接选择变化信号
        self.menu_list.currentRowChanged.connect(self._on_menu_changed)
        
        sidebar_layout.addWidget(self.menu_list)
        
    def _on_menu_changed(self, index):
        """处理菜单选择变化"""
        if index >= 0:
            # 更新右侧内容区域
            self.stacked_widget.setCurrentIndex(index)
            
            # 更新标题
            menu_titles = ["常规", "音频", "语音识别", "粘贴设置", "热词设置", "热词编辑", "依赖管理"]
            if index < len(menu_titles):
                self.title_label.setText(menu_titles[index])
        
    def _create_content_area(self):
        """创建右侧内容区域 - 参考macOS系统设置设计"""
        self.content_area = QFrame()
        self.content_area.setObjectName("contentArea")

        # 主内容布局 - 参考macOS系统设置间距
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        self.content_area.setLayout(content_layout)

        # 创建导航栏 - 参考macOS系统设置
        nav_frame = QFrame()
        nav_frame.setObjectName("navFrame")
        nav_frame.setFixedHeight(60)  # macOS导航栏标准高度
        nav_layout = QHBoxLayout()
        nav_layout.setContentsMargins(30, 16, 30, 16)
        nav_layout.setSpacing(12)
        nav_frame.setLayout(nav_layout)

        # 返回按钮（可选，暂时隐藏）
        self.back_button = QPushButton("‹")
        self.back_button.setObjectName("backButton")
        self.back_button.setFixedSize(28, 28)
        self.back_button.setVisible(False)  # 默认隐藏
        nav_layout.addWidget(self.back_button)

        # 标题标签 - 居中显示
        self.title_label = QLabel("常规")
        self.title_label.setObjectName("titleLabel")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addStretch()
        nav_layout.addWidget(self.title_label)
        nav_layout.addStretch()

        # 占位符（保持对称）
        placeholder = QWidget()
        placeholder.setFixedSize(28, 28)
        nav_layout.addWidget(placeholder)

        content_layout.addWidget(nav_frame)

        # 直接创建堆叠窗口部件，不使用滚动区域
        # 让每个页面自己管理滚动
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setObjectName("stackedWidget")

        # 创建各个设置页面
        self._create_settings_pages()

        content_layout.addWidget(self.stacked_widget)
        
    def _create_settings_pages(self):
        """创建各个设置页面"""
        # 常规设置页面
        general_page = self._create_general_page()
        self.stacked_widget.addWidget(general_page)
        
        # 音频设置页面
        audio_page = self._create_audio_page()
        self.stacked_widget.addWidget(audio_page)
        
        # 语音识别页面
        asr_page = self._create_asr_page()
        self.stacked_widget.addWidget(asr_page)
        
        # 粘贴设置页面
        paste_page = self._create_paste_settings_page()
        self.stacked_widget.addWidget(paste_page)

        # 热词设置页面
        hotwords_page = self._create_hotword_settings_page()
        self.stacked_widget.addWidget(hotwords_page)
        
        # 热词编辑页面
        hotwords_edit_page = self._create_hotwords_edit_page()
        self.stacked_widget.addWidget(hotwords_edit_page)
        
        # 依赖管理页面
        dependency_page = self._create_dependency_page()
        self.stacked_widget.addWidget(dependency_page)
        
    def _create_bottom_buttons(self):
        """创建底部按钮区域"""
        # 在内容区域底部添加按钮
        content_layout = self.content_area.layout()
        
        # 创建按钮框架
        button_frame = QFrame()
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 20, 0, 0)
        button_layout.setSpacing(10)
        
        # 重置按钮
        reset_button = QPushButton("重置为默认")
        reset_button.setObjectName("resetButton")
        reset_button.clicked.connect(self.reset_to_defaults)
        
        # 保存按钮
        save_button = QPushButton("保存")
        save_button.setObjectName("saveButton")
        save_button.clicked.connect(self.save_settings)
        
        button_layout.addStretch()
        button_layout.addWidget(reset_button)
        button_layout.addWidget(save_button)
        
        button_frame.setLayout(button_layout)
        content_layout.addWidget(button_frame)
    
    def _create_general_page(self):
        """创建常规设置页面 - 像素级还原macOS系统设置"""
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
        """)

        # 创建内容页面 - 严格按照macOS设计规范
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)  # 左对齐文字距左侧边界20px
        layout.setSpacing(0)

        # 信息卡片
        info_card = self._create_info_card(
            "🎤",
            "录音设置",
            "配置录音快捷键、延迟和音频参数，确保最佳的语音识别体验。"
        )
        layout.addWidget(info_card)
        layout.addSpacing(24)  # 分组模块上下间距24px

        # 快捷键设置分组
        hotkey_group = self._create_setting_group("快捷键设置", [
            self._create_setting_item_with_icon(
                "⌨️", "热键方案", self._create_scheme_combo(), has_arrow=False
            ),
            self._create_setting_item_with_icon(
                "🔘", "录音快捷键", self._create_hotkey_combo(), has_arrow=False
            ),
            self._create_setting_item_with_icon(
                "⏱️", "启动延迟", self._create_delay_slider(), has_arrow=False
            )
        ])
        layout.addWidget(hotkey_group)
        layout.addSpacing(24)  # 分组模块上下间距24px

        # 高级设置分组
        advanced_group = self._create_setting_group("高级设置", [
            self._create_setting_item_with_icon(
                "🔧", "调试模式", self._create_debug_switch(), has_arrow=False
            ),
            self._create_setting_item_with_icon(
                "📊", "性能监控", self._create_monitor_switch(), has_arrow=False
            )
        ])
        layout.addWidget(advanced_group)

        layout.addStretch()
        page.setLayout(layout)

        # 将页面设置到滚动区域
        scroll_area.setWidget(page)
        return scroll_area

    def _create_info_card(self, icon, title, description):
        """创建信息卡片"""
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background-color: #1E3A8A;
                border-radius: 10px;
                padding: 16px;
            }
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # 图标
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                background-color: transparent;
                min-width: 32px;
                max-width: 32px;
            }
        """)

        # 文本内容
        text_widget = QWidget()
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 15px;
                font-weight: 600;
                background-color: transparent;
            }
        """)

        desc_label = QLabel(description)
        desc_label.setStyleSheet("""
            QLabel {
                color: #A8C8EC;
                font-size: 12px;
                font-weight: 400;
                background-color: transparent;
            }
        """)
        desc_label.setWordWrap(True)

        text_layout.addWidget(title_label)
        text_layout.addWidget(desc_label)
        text_widget.setLayout(text_layout)

        layout.addWidget(icon_label)
        layout.addWidget(text_widget)
        layout.addStretch()

        card.setLayout(layout)
        return card

    def _create_setting_group(self, title, items):
        """创建设置分组"""
        group_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 分组标题 - 一级模块标题20px，Semibold
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 20px;
                font-weight: 600;
                padding: 0 0 8px 0;
                background-color: transparent;
            }
        """)
        layout.addWidget(title_label)

        # 设置项容器 - 参考macOS系统设置
        items_container = QWidget()
        items_container.setStyleSheet("""
            QWidget {
                background-color: #2C2C2E;
                border: 1px solid #3A3A3C;
                border-radius: 8px;
            }
        """)

        items_layout = QVBoxLayout()
        items_layout.setContentsMargins(0, 0, 0, 0)
        items_layout.setSpacing(0)  # 设置项之间无间距，通过分隔线分隔

        for i, item in enumerate(items):
            items_layout.addWidget(item)
            # 添加分隔线（除了最后一项）
            if i < len(items) - 1:
                separator = self._create_group_separator()
                items_layout.addWidget(separator)

        items_container.setLayout(items_layout)
        layout.addWidget(items_container)

        group_widget.setLayout(layout)
        return group_widget

    def _create_setting_item(self, label_text, control_widget, help_text=None):
        """创建单个设置项 - macOS风格"""
        item_widget = QWidget()
        item_widget.setFixedHeight(44)  # macOS标准设置项高度
        item_widget.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border-radius: 0px;
            }
            QWidget:hover {
                background-color: rgba(255, 255, 255, 0.05);
            }
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(16, 0, 16, 0)  # 左右16px边距
        layout.setSpacing(0)

        # 左侧标签 - 设置项标题14-16px，Regular
        label = QLabel(label_text)
        label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 400;
                background-color: transparent;
            }
        """)

        # 右侧控件
        control_widget.setStyleSheet(control_widget.styleSheet() + """
            background-color: transparent;
        """)

        layout.addWidget(label)
        layout.addStretch()
        layout.addWidget(control_widget)

        item_widget.setLayout(layout)
        return item_widget

    def _create_separator(self):
        """创建分隔线"""
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border: none;
            }
        """)
        return separator

    def _create_setting_item_with_icon(self, icon, label_text, control_widget, has_arrow=False):
        """创建带图标的设置项 - 像素级还原macOS"""
        item_widget = QWidget()
        item_widget.setFixedHeight(44)
        item_widget.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border-radius: 0px;
            }
            QWidget:hover {
                background-color: rgba(255, 255, 255, 0.05);
            }
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        # 图标
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                background-color: transparent;
                min-width: 24px;
                max-width: 24px;
                text-align: center;
            }
        """)

        # 标签
        label = QLabel(label_text)
        label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 400;
                background-color: transparent;
            }
        """)

        layout.addWidget(icon_label)
        layout.addWidget(label)
        layout.addStretch()
        layout.addWidget(control_widget)

        # 箭头
        if has_arrow:
            arrow_label = QLabel("›")
            arrow_label.setStyleSheet("""
                QLabel {
                    color: #666666;
                    font-size: 16px;
                    font-weight: 300;
                    background-color: transparent;
                    min-width: 12px;
                    max-width: 12px;
                }
            """)
            layout.addWidget(arrow_label)

        item_widget.setLayout(layout)
        return item_widget

    def _create_group_separator(self):
        """创建分组内的分隔线 - 参考macOS系统设置"""
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet("""
            QFrame {
                background-color: #48484A;
                border: none;
                margin: 0 16px;
            }
        """)
        return separator

    def _create_scheme_combo(self):
        """创建热键方案下拉框 - macOS风格"""
        self.hotkey_scheme_combo = MacOSComboBox()
        self.hotkey_scheme_combo.addItems(['hammerspoon', 'python'])
        self.hotkey_scheme_combo.setFixedWidth(140)
        current_scheme = self.settings_manager.get_hotkey_scheme() if self.settings_manager else 'python'
        self.hotkey_scheme_combo.setCurrentText(current_scheme)
        return self.hotkey_scheme_combo

    def _create_hotkey_combo(self):
        """创建快捷键下拉框 - macOS风格"""
        self.hotkey_combo = MacOSComboBox()
        self.hotkey_combo.addItems(['fn', 'ctrl', 'alt'])
        self.hotkey_combo.setFixedWidth(100)
        current_hotkey = self.settings_manager.get_hotkey() if self.settings_manager else 'fn'
        self.hotkey_combo.setCurrentText(current_hotkey)
        return self.hotkey_combo

    def _create_delay_slider(self):
        """创建延迟滑块 - macOS风格"""
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # 使用macOS风格滑块
        self.recording_start_delay = MacOSSlider(
            minimum=50,
            maximum=500,
            value=50,
            left_label="快",
            right_label="慢"
        )
        self.recording_start_delay.setFixedWidth(180)

        delay_value = self.settings_manager.get_setting('hotkey_settings.recording_start_delay', 50) if self.settings_manager else 50
        self.recording_start_delay.setValue(int(delay_value))

        # 数值标签
        self.start_delay_value_label = QLabel("50ms")
        self.start_delay_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.start_delay_value_label.setStyleSheet("""
            QLabel {
                color: #A0A0A0;
                font-size: 12px;
                background-color: transparent;
            }
        """)

        self.recording_start_delay.valueChanged.connect(
            lambda value: self.start_delay_value_label.setText(f"{value}ms")
        )

        layout.addWidget(self.recording_start_delay)
        layout.addWidget(self.start_delay_value_label)
        container.setLayout(layout)
        return container

    def _create_volume_slider(self):
        """创建音量阈值滑块 - macOS风格"""
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # 使用macOS风格滑块
        self.volume_threshold = MacOSSlider(
            minimum=0,
            maximum=20,
            value=3,
            left_label="低",
            right_label="高"
        )
        self.volume_threshold.setFixedWidth(180)

        current_threshold = self.settings_manager.get_setting('audio.volume_threshold', 150) if self.settings_manager else 150
        slider_value = int(current_threshold * 20 / 1000)
        self.volume_threshold.setValue(slider_value)

        # 数值标签
        self.volume_value_label = QLabel("3")
        self.volume_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.volume_value_label.setStyleSheet("""
            QLabel {
                color: #8a8a8a;
                font-size: 11px;
                background-color: transparent;
            }
        """)

        self.volume_threshold.valueChanged.connect(
            lambda value: self.volume_value_label.setText(str(value))
        )

        layout.addWidget(self.volume_threshold)
        layout.addWidget(self.volume_value_label)
        container.setLayout(layout)
        return container


    
    def _create_audio_page(self):
        """创建音频设置页面 - 像素级还原macOS系统设置"""
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        # 创建内容页面
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)

        # 创建设置项容器
        settings_container = QWidget()
        settings_layout = QVBoxLayout()
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setSpacing(1)
        settings_container.setLayout(settings_layout)

        # 音频设备设置项 - macOS风格（带勾选标记）
        self.input_device = MacOSComboBoxWithCheck()
        self.input_device.setFixedWidth(220)
        self._update_audio_devices()
        device_container = QWidget()
        device_layout = QHBoxLayout()
        device_layout.setContentsMargins(0, 0, 0, 0)
        device_layout.setSpacing(8)
        device_layout.addWidget(self.input_device)

        refresh_button = QPushButton("刷新")
        refresh_button.setFixedSize(50, 24)
        refresh_button.clicked.connect(self._update_audio_devices)
        device_layout.addWidget(refresh_button)
        device_container.setLayout(device_layout)

        device_item = self._create_setting_item(
            "输入设备",
            device_container,
            help_text="选择要使用的麦克风设备"
        )
        settings_layout.addWidget(device_item)

        # 分隔线
        separator1 = self._create_separator()
        settings_layout.addWidget(separator1)

        # 音量阈值设置项
        volume_item = self._create_setting_item(
            "音量阈值",
            self._create_volume_slider(),
            help_text="数值越小，麦克风越灵敏"
        )
        settings_layout.addWidget(volume_item)

        # 分隔线
        separator2 = self._create_separator()
        settings_layout.addWidget(separator2)

        # 录音时长设置项
        duration_item = self._create_setting_item(
            "最大录音时长",
            self._create_duration_slider(),
            help_text="设置录音的最大时长，超过此时长将自动停止录音"
        )
        settings_layout.addWidget(duration_item)

        layout.addWidget(settings_container)
        layout.addStretch()
        page.setLayout(layout)

        # 将页面设置到滚动区域
        scroll_area.setWidget(page)
        return scroll_area

    def _create_paste_settings_page(self):
        """创建粘贴设置页面 - 像素级还原macOS"""
        page = QWidget()
        page.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)

        # 页面标题
        title = QLabel("粘贴设置")
        title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 28px;
                font-weight: 700;
                background-color: transparent;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title)

        # 粘贴延迟设置分组
        group_title = QLabel("粘贴延迟设置")
        group_title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 20px;
                font-weight: 600;
                background-color: transparent;
                margin-top: 20px;
                margin-bottom: 15px;
            }
        """)
        layout.addWidget(group_title)

        # 转录完成后延迟卡片
        self.paste_delay_card = MacOSSliderCard(
            title="转录完成后延迟：",
            description="转录完成后等待多长时间再执行粘贴操作。数值越大，粘贴越稳定，但响应稍慢。",
            min_val=0,
            max_val=100,
            current_val=20,
            unit="ms",
            suggestion="建议值：20-50ms"
        )
        layout.addWidget(self.paste_delay_card)

        # 历史记录点击后延迟卡片
        self.history_delay_card = MacOSSliderCard(
            title="历史记录点击后延迟：",
            description="点击历史记录项后等待多长时间再执行粘贴操作。数值越大，粘贴越稳定，但响应稍慢。",
            min_val=0,
            max_val=150,
            current_val=30,
            unit="ms",
            suggestion="建议值：30-80ms"
        )
        layout.addWidget(self.history_delay_card)

        layout.addStretch()
        page.setLayout(layout)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidget(page)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("")  # 使用主窗口的滚动条样式

        return scroll_area

    def _create_hotword_settings_page(self):
        """创建热词设置页面 - 像素级还原macOS"""
        page = QWidget()
        page.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)

        # 页面标题
        title = QLabel("热词设置")
        title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 28px;
                font-weight: 700;
                background-color: transparent;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title)

        # 热词权重分组
        weight_group_title = QLabel("热词权重")
        weight_group_title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 20px;
                font-weight: 600;
                background-color: transparent;
                margin-top: 20px;
                margin-bottom: 15px;
            }
        """)
        layout.addWidget(weight_group_title)

        # 热词权重滑块卡片
        self.hotword_weight_card = MacOSSliderCard(
            title="热词权重：",
            description="数值越大，热词识别优先级越高。",
            min_val=0,
            max_val=100,
            current_val=80,
            unit="",
            suggestion="建议值：60-90"
        )
        layout.addWidget(self.hotword_weight_card)

        # 发音纠错分组
        correction_group_title = QLabel("发音纠错")
        correction_group_title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 20px;
                font-weight: 600;
                background-color: transparent;
                margin-top: 20px;
                margin-bottom: 15px;
            }
        """)
        layout.addWidget(correction_group_title)

        # 发音相似词纠错开关卡片
        self.pronunciation_correction_card = MacOSSwitchCard(
            title="启用发音相似词纠错",
            description="自动将发音相似的词纠正为热词（如：含高→行高）",
            checked=True
        )
        layout.addWidget(self.pronunciation_correction_card)

        layout.addStretch()
        page.setLayout(layout)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidget(page)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("")  # 使用主窗口的滚动条样式

        return scroll_area

    def _create_duration_slider(self):
        """创建录音时长滑块 - macOS风格"""
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # 使用macOS风格滑块
        self.recording_duration = MacOSSlider(
            minimum=5,
            maximum=60,
            value=10,
            left_label="短",
            right_label="长"
        )
        self.recording_duration.setFixedWidth(180)

        duration_value = self.settings_manager.get_setting('audio.max_recording_duration', 10) if self.settings_manager else 10
        self.recording_duration.setValue(int(duration_value))

        # 数值标签
        self.duration_value_label = QLabel("10秒")
        self.duration_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.duration_value_label.setStyleSheet("""
            QLabel {
                color: #8a8a8a;
                font-size: 11px;
                background-color: transparent;
            }
        """)

        self.recording_duration.valueChanged.connect(
            lambda value: self.duration_value_label.setText(f"{value}秒")
        )

        layout.addWidget(self.recording_duration)
        layout.addWidget(self.duration_value_label)
        container.setLayout(layout)
        return container

    def _create_debug_switch(self):
        """创建调试模式开关"""
        switch = MacOSSwitch()
        debug_enabled = self.settings_manager.get_setting('general.debug_mode', False) if self.settings_manager else False
        switch.setChecked(debug_enabled)
        return switch

    def _create_monitor_switch(self):
        """创建性能监控开关"""
        switch = MacOSSwitch()
        monitor_enabled = self.settings_manager.get_setting('general.performance_monitor', False) if self.settings_manager else False
        switch.setChecked(monitor_enabled)
        return switch

    def _wrap_with_scroll(self, content_widget):
        """为页面内容添加滚动区域包装"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        scroll_area.setWidget(content_widget)
        return scroll_area

    def _create_asr_page(self):
        """创建语音识别设置页面 - macOS风格"""
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        # 创建内容页面
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 模型设置
        model_group = QGroupBox("模型设置")
        model_layout = QVBoxLayout()
        model_layout.setContentsMargins(16, 16, 16, 16)
        model_layout.setSpacing(8)
        
        # ASR模型路径
        asr_layout = QHBoxLayout()
        self.asr_model_path = QLineEdit()
        asr_path = self.settings_manager.get_setting('asr.model_path') if self.settings_manager else ''
        self.asr_model_path.setText(asr_path)
        asr_browse = QPushButton("浏览...")
        asr_browse.clicked.connect(lambda: self._browse_model('asr'))
        asr_layout.addWidget(QLabel("ASR模型路径："))
        asr_layout.addWidget(self.asr_model_path)
        asr_layout.addWidget(asr_browse)
        
        # 标点符号模型路径
        punc_layout = QHBoxLayout()
        self.punc_model_path = QLineEdit()
        punc_path = self.settings_manager.get_setting('asr.punc_model_path') if self.settings_manager else ''
        self.punc_model_path.setText(punc_path)
        punc_browse = QPushButton("浏览...")
        punc_browse.clicked.connect(lambda: self._browse_model('punc'))
        punc_layout.addWidget(QLabel("标点模型路径："))
        punc_layout.addWidget(self.punc_model_path)
        punc_layout.addWidget(punc_browse)
        
        model_layout.addLayout(asr_layout)
        model_layout.addLayout(punc_layout)
        model_group.setLayout(model_layout)
        
        # 识别设置
        recognition_group = QGroupBox("识别设置")
        recognition_layout = QVBoxLayout()
        recognition_layout.setContentsMargins(16, 16, 16, 16)
        recognition_layout.setSpacing(8)
        
        self.auto_punctuation = QCheckBox("自动添加标点")
        auto_punc = self.settings_manager.get_setting('asr.auto_punctuation', True) if self.settings_manager else True
        self.auto_punctuation.setChecked(auto_punc)
        
        self.real_time_display = QCheckBox("实时显示识别结果")
        real_time = self.settings_manager.get_setting('asr.real_time_display', True) if self.settings_manager else True
        self.real_time_display.setChecked(real_time)
        
        recognition_layout.addWidget(self.auto_punctuation)
        recognition_layout.addWidget(self.real_time_display)
        recognition_group.setLayout(recognition_layout)
        
        layout.addWidget(model_group)
        layout.addWidget(recognition_group)
        layout.addStretch()
        page.setLayout(layout)

        # 将页面设置到滚动区域
        scroll_area.setWidget(page)
        return scroll_area
    
    def _create_paste_page(self):
        """创建粘贴设置页面"""
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # 粘贴延迟设置组
        paste_group = QGroupBox("粘贴延迟设置")
        paste_layout = QVBoxLayout()
        paste_layout.setContentsMargins(16, 16, 16, 16)
        paste_layout.setSpacing(8)
        
        # 转录完成后粘贴延迟
        transcription_layout = QHBoxLayout()
        transcription_label = QLabel("转录完成后延迟：")
        self.transcription_delay_value_label = QLabel("0ms")
        self.transcription_delay_value_label.setMinimumWidth(50)
        
        self.transcription_delay = QSlider(Qt.Orientation.Horizontal)
        self.transcription_delay.setRange(0, 200)
        trans_delay = self.settings_manager.get_setting('paste.transcription_delay', 0) if self.settings_manager else 0
        self.transcription_delay.setValue(int(trans_delay))
        self.transcription_delay.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.transcription_delay.setTickInterval(20)
        
        self.transcription_delay.valueChanged.connect(
            lambda value: self.transcription_delay_value_label.setText(f"{value}ms")
        )
        
        transcription_layout.addWidget(transcription_label)
        transcription_layout.addWidget(self.transcription_delay)
        transcription_layout.addWidget(self.transcription_delay_value_label)
        
        transcription_help = QLabel("转录完成后等待多长时间再执行粘贴操作。数值越大，粘贴越稳定，但响应稍慢。建议值：20-50ms")
        transcription_help.setProperty("class", "help-text")
        transcription_help.setWordWrap(True)
        
        paste_layout.addLayout(transcription_layout)
        paste_layout.addWidget(transcription_help)
        
        # 历史记录点击后粘贴延迟
        history_layout = QHBoxLayout()
        history_label = QLabel("历史记录点击后延迟：")
        self.history_delay_value_label = QLabel("0ms")
        self.history_delay_value_label.setMinimumWidth(50)
        
        self.history_delay = QSlider(Qt.Orientation.Horizontal)
        self.history_delay.setRange(0, 200)
        hist_delay = self.settings_manager.get_setting('paste.history_click_delay', 0) if self.settings_manager else 0
        self.history_delay.setValue(int(hist_delay))
        self.history_delay.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.history_delay.setTickInterval(20)
        
        self.history_delay.valueChanged.connect(
            lambda value: self.history_delay_value_label.setText(f"{value}ms")
        )
        
        history_layout.addWidget(history_label)
        history_layout.addWidget(self.history_delay)
        history_layout.addWidget(self.history_delay_value_label)
        
        history_help = QLabel("点击历史记录项后等待多长时间再执行粘贴操作。数值越大，粘贴越稳定，但响应稍慢。建议值：30-80ms")
        history_help.setProperty("class", "help-text")
        history_help.setWordWrap(True)
        
        paste_layout.addLayout(history_layout)
        paste_layout.addWidget(history_help)
        
        paste_group.setLayout(paste_layout)
        
        layout.addWidget(paste_group)
        layout.addStretch()
        page.setLayout(layout)
        return self._wrap_with_scroll(page)
    
    def _create_hotwords_page(self):
        """创建热词设置页面"""
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # 热词权重设置
        weight_group = QGroupBox("热词权重")
        weight_layout = QVBoxLayout()
        weight_layout.setContentsMargins(16, 16, 16, 16)
        weight_layout.setSpacing(8)
        
        weight_slider_layout = QHBoxLayout()
        weight_label = QLabel("热词权重：")
        self.hotword_weight_value_label = QLabel("80")
        self.hotword_weight_value_label.setMinimumWidth(30)
        
        self.hotword_weight = QSlider(Qt.Orientation.Horizontal)
        self.hotword_weight.setRange(10, 100)
        weight_value = int(self.settings_manager.get_setting('asr.hotword_weight', 80)) if self.settings_manager else 80
        self.hotword_weight.setValue(weight_value)
        self.hotword_weight.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.hotword_weight.setTickInterval(10)
        
        self.hotword_weight.valueChanged.connect(
            lambda value: self.hotword_weight_value_label.setText(str(value))
        )
        
        weight_slider_layout.addWidget(weight_label)
        weight_slider_layout.addWidget(self.hotword_weight)
        weight_slider_layout.addWidget(self.hotword_weight_value_label)
        
        weight_help = QLabel("数值越大，热词识别优先级越高。建议值：60-90")
        weight_help.setProperty("class", "help-text")
        weight_help.setWordWrap(True)
        
        weight_layout.addLayout(weight_slider_layout)
        weight_layout.addWidget(weight_help)
        weight_group.setLayout(weight_layout)
        
        # 发音纠错设置
        correction_group = QGroupBox("发音纠错")
        correction_layout = QVBoxLayout()
        correction_layout.setContentsMargins(16, 16, 16, 16)
        correction_layout.setSpacing(8)
        
        self.enable_pronunciation_correction = QCheckBox("启用发音相似词纠错")
        correction_enabled = self.settings_manager.get_setting('asr.enable_pronunciation_correction', True) if self.settings_manager else True
        self.enable_pronunciation_correction.setChecked(correction_enabled)
        
        correction_help = QLabel("自动将发音相似的词纠正为热词（如：含高→行高）")
        correction_help.setProperty("class", "help-text")
        correction_help.setWordWrap(True)
        
        correction_layout.addWidget(self.enable_pronunciation_correction)
        correction_layout.addWidget(correction_help)
        correction_group.setLayout(correction_layout)
        
        layout.addWidget(weight_group)
        layout.addWidget(correction_group)
        layout.addStretch()
        page.setLayout(layout)
        return self._wrap_with_scroll(page)
    
    def _create_hotwords_edit_page(self):
        """创建热词编辑页面"""
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # 热词编辑区域
        hotword_edit_group = QGroupBox("热词列表")
        hotword_edit_layout = QVBoxLayout()
        hotword_edit_layout.setContentsMargins(16, 16, 16, 16)
        hotword_edit_layout.setSpacing(8)
        
        self.hotword_text_edit = QTextEdit()
        self.hotword_text_edit.setPlaceholderText("每行输入一个热词，以#开头的行为注释")
        self.hotword_text_edit.setMinimumHeight(300)
        self.hotword_text_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px;
                font-family: monospace;
                font-size: 13px;
            }
        """)
        
        hotword_edit_help = QLabel("修改后点击底部的'保存'按钮保存所有设置，重新开始录音后生效")
        hotword_edit_help.setProperty("class", "help-text")
        hotword_edit_help.setWordWrap(True)

        hotword_edit_layout.addWidget(self.hotword_text_edit)
        hotword_edit_layout.addWidget(hotword_edit_help)
        hotword_edit_group.setLayout(hotword_edit_layout)
        
        layout.addWidget(hotword_edit_group)
        layout.addStretch()
        page.setLayout(layout)

        # 自动加载热词
        self._load_hotwords()

        return self._wrap_with_scroll(page)
    
    def _create_dependency_page(self):
        """创建依赖管理页面"""
        try:
            dependency_tab = DependencyTab(self)
            return dependency_tab
        except Exception as e:
            import logging
            logging.error(f"创建依赖管理标签页失败: {e}")
            
            # 创建错误提示页面
            error_page = QWidget()
            layout = QVBoxLayout()
            
            error_label = QLabel(f"依赖管理功能暂不可用\n\n错误信息: {e}")
            error_label.setWordWrap(True)
            error_label.setStyleSheet("color: #666; padding: 20px;")
            layout.addWidget(error_label)
            
            retry_btn = QPushButton("重试")
            retry_btn.clicked.connect(lambda: self._create_dependency_page())
            layout.addWidget(retry_btn)
            
            layout.addStretch()
            error_page.setLayout(layout)
            
            return error_page
    
    def _browse_model(self, model_type):
        """浏览选择模型文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"选择{model_type.upper()}模型文件",
            "",
            "Model Files (*.pth *.pt *.bin);;All Files (*.*)"
        )
        if file_path:
            if model_type == 'asr':
                self.asr_model_path.setText(file_path)
            else:
                self.punc_model_path.setText(file_path)
    
    def _get_audio_devices(self):
        """获取系统中所有可用的音频输入设备"""
        devices = []
        
        try:
            # 清理之前的实例
            self._cleanup_audio()
            
            # 创建新的 PyAudio 实例
            self.audio = pyaudio.PyAudio()
            
            # 获取默认输入设备信息
            try:
                default_device = self.audio.get_default_input_device_info()
                default_name = default_device['name']
                devices.append(f"系统默认 ({default_name})")
            except Exception as e:
                import logging
                logging.error(f"获取默认设备失败: {e}")
                default_name = None
                devices.append("系统默认")
            
            # 获取所有设备信息
            for i in range(self.audio.get_device_count()):
                try:
                    device_info = self.audio.get_device_info_by_index(i)
                    # 只添加输入设备（maxInputChannels > 0）
                    if device_info['maxInputChannels'] > 0:
                        name = device_info['name']
                        if default_name is None or name != default_name:  # 避免重复添加默认设备
                            devices.append(name)
                except Exception as e:
                    import logging
                    logging.error(f"获取设备 {i} 信息失败: {e}")
                    continue
                    
        except Exception as e:
            import logging
            logging.error(f"获取音频设备列表失败: {e}")
            if not devices:  # 如果还没有添加任何设备
                devices = ["系统默认"]
            
        return devices
    
    def _update_audio_devices(self):
        """更新音频设备列表"""
        try:
            # 保存当前选择的设备
            current_device = self.input_device.currentText() if hasattr(self, 'input_device') else ""
            
            # 清空并重新加载设备列表
            self.input_device.clear()
            devices = self._get_audio_devices()
            self.input_device.addItems(devices)
            
            # 尝试恢复之前选择的设备
            device_found = False
            
            # 首先尝试完全匹配
            for i in range(self.input_device.count()):
                device_name = self.input_device.itemText(i)
                if device_name == current_device:
                    self.input_device.setCurrentText(device_name)
                    device_found = True
                    break
            
            # 如果没找到，尝试部分匹配（去除"系统默认"前缀后的名称）
            if not device_found and current_device:
                current_device_name = current_device.replace("系统默认 (", "").replace(")", "")
                for i in range(self.input_device.count()):
                    device_name = self.input_device.itemText(i)
                    if current_device_name in device_name:
                        self.input_device.setCurrentText(device_name)
                        device_found = True
                        break
            
            # 如果仍然没找到，使用第一个设备（通常是系统默认）
            if not device_found:
                self.input_device.setCurrentIndex(0)
            
        except Exception as e:
            import logging
            logging.error(f"更新设备列表失败: {e}")
            # 确保至少有一个选项
            if self.input_device.count() == 0:
                self.input_device.addItem("系统默认")
    
    def _load_hotwords(self):
        """从文件加载热词到文本编辑框"""
        try:
            hotwords_file = Path("resources") / "hotwords.txt"
            if hotwords_file.exists():
                content = hotwords_file.read_text(encoding="utf-8")
                self.hotword_text_edit.setText(content)
            else:
                self.hotword_text_edit.setText("# 热词列表\n# 每行一个热词，以#开头的行为注释\n")
        except Exception as e:
            import logging
            logging.error(f"加载热词失败: {e}")
            QMessageBox.warning(self, "错误", f"加载热词失败: {e}")
    

    def _cleanup_audio(self):
        """清理音频资源"""
        if self.audio:
            try:
                self.audio.terminate()
            except Exception as e:
                import logging
                logging.error(f"清理音频资源失败: {e}")
            finally:
                self.audio = None