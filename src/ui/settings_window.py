from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QComboBox, QPushButton, QGroupBox,
                            QCheckBox, QSlider, QListWidget, QListWidgetItem,
                            QLineEdit, QFileDialog, QTextEdit, QMessageBox, QDialog,
                            QStackedWidget, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor
from pathlib import Path
import pyaudio

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
        
        # 设置窗口基本属性
        self.setWindowTitle("设置")
        self.setMinimumSize(800, 600)
        self.setModal(True)
        
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
        super().closeEvent(event)  # PyAudio 实例
        
        # 设置窗口属性
        self.setWindowTitle("设置")
        self.setMinimumSize(800, 600)
        self.resize(900, 700)
        
        # 设置窗口标志
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowStaysOnTopHint
        )
        
        # 初始化UI
        self._setup_ui()
        self._setup_styles()
        self._load_settings()
        
    def _setup_ui(self):
        """设置UI布局"""
        # 创建主布局
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
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
        """设置macOS深色主题样式"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            
            QFrame#sidebar {
                background-color: #2b2b2b;
                border-right: 1px solid #3d3d3d;
            }
            
            QListWidget#menuList {
                background-color: transparent;
                border: none;
                outline: none;
                font-size: 14px;
                padding: 8px 0px;
            }
            
            QListWidget#menuList::item {
                padding: 14px 20px;
                border: none;
                color: #e0e0e0;
                font-weight: 500;
            }
            
            QListWidget#menuList::item:selected {
                background-color: #007AFF;
                color: #ffffff;
                border-radius: 8px;
                margin: 2px 8px;
                font-weight: 600;
            }
            
            QListWidget#menuList::item:hover {
                background-color: #3d3d3d;
                color: #ffffff;
                border-radius: 8px;
                margin: 2px 8px;
            }
            
            QFrame#contentArea {
                background-color: #2b2b2b;
                border-radius: 10px;
                border: 1px solid #3d3d3d;
            }
            
            QLabel#titleLabel {
                font-size: 22px;
                font-weight: 700;
                color: #ffffff;
                margin-bottom: 16px;
                padding: 0px 4px;
            }
            
            QLabel {
                color: #ffffff;
                font-size: 14px;
                font-weight: 500;
                line-height: 1.5;
            }
            
            QLabel[class="help-text"] {
                color: #b0b0b0;
                font-size: 12px;
                font-weight: 400;
            }
            
            QGroupBox {
                font-size: 16px;
                font-weight: 700;
                color: #ffffff;
                border: 1.5px solid #3d3d3d;
                border-radius: 12px;
                margin-top: 16px;
                padding-top: 16px;
                background-color: #262626;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 4px 16px;
                background-color: #2b2b2b;
                color: #ffffff;
                border-radius: 6px;
                font-weight: 700;
            }
            
            QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox {
                padding: 12px 16px;
                border: 1.5px solid #3d3d3d;
                border-radius: 8px;
                background-color: #333333;
                color: #ffffff;
                font-size: 14px;
                font-weight: 500;
                min-height: 22px;
            }
            
            QComboBox:focus, QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: #007AFF;
                background-color: #3a3a3a;
                outline: none;
            }
            
            QComboBox:hover, QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover {
                border-color: #5a5a5a;
                background-color: #3a3a3a;
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
                height: 6px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #404040, stop:1 #2a2a2a);
                border-radius: 3px;
                margin: 8px 0;
            }
            
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #007AFF, stop:1 #0056CC);
                border-radius: 3px;
                margin: 0px;
            }
            
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f8f8);
                border: 2px solid #e0e0e0;
                width: 20px;
                height: 20px;
                border-radius: 12px;
                margin: -8px 0;
            }
            
            QSlider::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f0f0f0);
                border: 2px solid #007AFF;
                transform: scale(1.1);
            }
            
            QSlider::handle:horizontal:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f8f8, stop:1 #e8e8e8);
                border: 2px solid #0056CC;
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
                width: 18px;
                height: 18px;
                border: 2px solid #5a5a5a;
                border-radius: 4px;
                background-color: #2c2c2c;
            }
            
            QCheckBox::indicator:hover {
                border-color: #007AFF;
                background-color: #353535;
            }
            
            QCheckBox::indicator:checked {
                background-color: #007AFF;
                border-color: #007AFF;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTAiIHZpZXdCb3g9IjAgMCAxMiAxMCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEuNSA0LjVMNC41IDcuNUwxMC41IDEuNSIgc3Ryb2tlPSIjRkZGRkZGIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
            }
            
            QCheckBox::indicator:checked:hover {
                background-color: #0056CC;
                border-color: #0056CC;
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
                background-color: #333333;
                color: #ffffff;
                border: 1.5px solid #3d3d3d;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
                min-height: 18px;
            }
            
            QPushButton:hover {
                background-color: #3a3a3a;
                border-color: #5a5a5a;
                color: #ffffff;
            }
            
            QPushButton:pressed {
                background-color: #2a2a2a;
                border-color: #007AFF;
            }
            
            QPushButton#saveButton {
                background-color: #007AFF;
                border-color: #007AFF;
                color: #ffffff;
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
            
            QScrollBar:vertical {
                background-color: transparent;
                width: 10px;
                border-radius: 5px;
                margin: 0px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #4d4d4d;
                border-radius: 5px;
                min-height: 30px;
                margin: 2px;
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
        """创建左侧菜单栏"""
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setObjectName("sidebar")
        
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(0, 20, 0, 20)
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
        """创建右侧内容区域"""
        self.content_area = QFrame()
        self.content_area.setObjectName("contentArea")
        
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)
        self.content_area.setLayout(content_layout)
        
        # 创建标题标签
        self.title_label = QLabel("常规")
        self.title_label.setObjectName("titleLabel")
        content_layout.addWidget(self.title_label)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setObjectName("scrollArea")
        
        # 创建堆叠窗口部件
        self.stacked_widget = QStackedWidget()
        
        # 创建各个设置页面
        self._create_settings_pages()
        
        scroll_area.setWidget(self.stacked_widget)
        content_layout.addWidget(scroll_area)
        
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
        paste_page = self._create_paste_page()
        self.stacked_widget.addWidget(paste_page)
        
        # 热词设置页面
        hotwords_page = self._create_hotwords_page()
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
        """创建常规设置页面"""
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # 热键方案设置组
        scheme_group = QGroupBox("热键方案设置")
        scheme_layout = QVBoxLayout()
        scheme_layout.setContentsMargins(16, 16, 16, 16)
        scheme_layout.setSpacing(8)
        
        scheme_description = QLabel("选择热键监听方案：")
        self.hotkey_scheme_combo = QComboBox()
        self.hotkey_scheme_combo.addItems(['hammerspoon', 'python'])
        current_scheme = self.settings_manager.get_hotkey_scheme() if self.settings_manager else 'python'
        self.hotkey_scheme_combo.setCurrentText(current_scheme)
        
        scheme_help_text = QLabel("Hammerspoon方案：更稳定，需要安装Hammerspoon\nPython方案：原生实现，可能在某些情况下不稳定")
        scheme_help_text.setProperty("class", "help-text")
        scheme_help_text.setWordWrap(True)
        
        scheme_layout.addWidget(scheme_description)
        scheme_layout.addWidget(self.hotkey_scheme_combo)
        scheme_layout.addWidget(scheme_help_text)
        scheme_group.setLayout(scheme_layout)
        
        # 快捷键设置组
        hotkey_group = QGroupBox("快捷键设置")
        hotkey_layout = QVBoxLayout()
        hotkey_layout.setContentsMargins(16, 16, 16, 16)
        hotkey_layout.setSpacing(8)
        
        description = QLabel("选择录音快捷键：")
        self.hotkey_combo = QComboBox()
        self.hotkey_combo.addItems(['fn', 'ctrl', 'alt'])
        current_hotkey = self.settings_manager.get_hotkey() if self.settings_manager else 'fn'
        self.hotkey_combo.setCurrentText(current_hotkey)
        
        help_text = QLabel("按住所选按键开始录音，释放按键结束录音")
        help_text.setProperty("class", "help-text")
        
        hotkey_layout.addWidget(description)
        hotkey_layout.addWidget(self.hotkey_combo)
        hotkey_layout.addWidget(help_text)
        hotkey_group.setLayout(hotkey_layout)
        
        # 快捷键延迟设置组
        delay_group = QGroupBox("快捷键延迟设置")
        delay_layout = QVBoxLayout()
        delay_layout.setContentsMargins(16, 16, 16, 16)
        delay_layout.setSpacing(8)
        
        # 录制启动延迟设置
        start_delay_layout = QHBoxLayout()
        start_delay_label = QLabel("录制启动延迟：")
        self.start_delay_value_label = QLabel("50ms")
        self.start_delay_value_label.setMinimumWidth(50)
        
        self.recording_start_delay = QSlider(Qt.Orientation.Horizontal)
        self.recording_start_delay.setRange(50, 500)
        delay_value = self.settings_manager.get_setting('hotkey_settings.recording_start_delay', 50) if self.settings_manager else 50
        self.recording_start_delay.setValue(int(delay_value))
        self.recording_start_delay.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.recording_start_delay.setTickInterval(50)
        
        self.recording_start_delay.valueChanged.connect(
            lambda value: self.start_delay_value_label.setText(f"{value}ms")
        )
        
        start_delay_layout.addWidget(start_delay_label)
        start_delay_layout.addWidget(self.recording_start_delay)
        start_delay_layout.addWidget(self.start_delay_value_label)
        
        delay_help_text = QLabel("按下快捷键后等待多长时间才开始录制，用于避免组合快捷键误触发。\n数值越小启动越快，但可能误触发；数值越大越安全，但启动较慢。建议值：50-150ms")
        delay_help_text.setProperty("class", "help-text")
        delay_help_text.setWordWrap(True)
        
        delay_layout.addLayout(start_delay_layout)
        delay_layout.addWidget(delay_help_text)
        delay_group.setLayout(delay_layout)
        
        layout.addWidget(scheme_group)
        layout.addWidget(hotkey_group)
        layout.addWidget(delay_group)
        layout.addStretch()
        page.setLayout(layout)
        return page
    
    def _create_audio_page(self):
        """创建音频设置页面"""
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # 音频设备设置
        device_group = QGroupBox("音频设备")
        device_layout = QVBoxLayout()
        device_layout.setContentsMargins(16, 16, 16, 16)
        device_layout.setSpacing(8)
        
        self.input_device = QComboBox()
        self._update_audio_devices()
        
        device_header_layout = QHBoxLayout()
        device_header_layout.addWidget(QLabel("输入设备："))
        refresh_button = QPushButton("刷新")
        refresh_button.setFixedWidth(60)
        refresh_button.clicked.connect(self._update_audio_devices)
        device_header_layout.addWidget(refresh_button)
        
        device_layout.addLayout(device_header_layout)
        device_layout.addWidget(self.input_device)
        
        device_help = QLabel("选择要使用的麦克风设备，设备更改后需要重新开始录音")
        device_help.setProperty("class", "help-text")
        device_help.setWordWrap(True)
        device_layout.addWidget(device_help)
        
        device_group.setLayout(device_layout)
        
        # 音频控制设置
        control_group = QGroupBox("音频控制")
        control_layout = QVBoxLayout()
        control_layout.setContentsMargins(16, 16, 16, 16)
        control_layout.setSpacing(8)
        
        # 音量阈值设置
        volume_layout = QHBoxLayout()
        volume_label = QLabel("音量阈值：")
        self.volume_value_label = QLabel("3")
        self.volume_value_label.setMinimumWidth(30)
        
        self.volume_threshold = QSlider(Qt.Orientation.Horizontal)
        self.volume_threshold.setRange(0, 20)
        current_threshold = self.settings_manager.get_setting('audio.volume_threshold', 150) if self.settings_manager else 150
        slider_value = int(current_threshold * 20 / 1000)
        self.volume_threshold.setValue(slider_value)
        self.volume_value_label.setText(str(slider_value))
        self.volume_threshold.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.volume_threshold.setTickInterval(1)
        
        self.volume_threshold.valueChanged.connect(
            lambda value: self.volume_value_label.setText(str(value))
        )
        
        volume_layout.addWidget(volume_label)
        volume_layout.addWidget(self.volume_threshold)
        volume_layout.addWidget(self.volume_value_label)
        
        help_text = QLabel("数值越小，麦克风越灵敏。建议值：2-4\n当音量低于阈值时会被视为静音。默认值：3")
        help_text.setProperty("class", "help-text")
        help_text.setWordWrap(True)
        
        control_layout.addLayout(volume_layout)
        control_layout.addWidget(help_text)
        
        # 录音时长设置
        duration_layout = QHBoxLayout()
        duration_label = QLabel("最大录音时长：")
        self.duration_value_label = QLabel("10秒")
        self.duration_value_label.setMinimumWidth(50)
        
        self.recording_duration = QSlider(Qt.Orientation.Horizontal)
        self.recording_duration.setRange(5, 60)
        duration_value = self.settings_manager.get_setting('audio.max_recording_duration', 10) if self.settings_manager else 10
        self.recording_duration.setValue(int(duration_value))
        self.recording_duration.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.recording_duration.setTickInterval(5)
        
        self.recording_duration.valueChanged.connect(
            lambda value: self.duration_value_label.setText(f"{value}秒")
        )
        
        duration_layout.addWidget(duration_label)
        duration_layout.addWidget(self.recording_duration)
        duration_layout.addWidget(self.duration_value_label)
        
        duration_help_text = QLabel("设置录音的最大时长，超过此时长将自动停止录音。建议值：10-30秒")
        duration_help_text.setProperty("class", "help-text")
        duration_help_text.setWordWrap(True)
        
        control_layout.addLayout(duration_layout)
        control_layout.addWidget(duration_help_text)
        control_group.setLayout(control_layout)
        
        layout.addWidget(device_group)
        layout.addWidget(control_group)
        layout.addStretch()
        page.setLayout(layout)
        return page
    
    def _create_asr_page(self):
        """创建语音识别设置页面"""
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
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
        return page
    
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
        return page
    
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
        return page
    
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
        
        return page
    
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