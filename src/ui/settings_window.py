from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QComboBox, QPushButton, QGroupBox,
                            QCheckBox, QSlider, QTabWidget,
                            QLineEdit, QFileDialog)
from PyQt6.QtCore import Qt, pyqtSignal

class SettingsWindow(QWidget):
    # 定义信号
    settings_changed = pyqtSignal(str, object)  # 当任何设置改变时发出信号
    settings_saved = pyqtSignal()  # 当设置保存时发出信号

    def __init__(self, parent=None, settings_manager=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setWindowTitle("设置")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        # 设置窗口标志
        self.setWindowFlags(
            Qt.WindowType.Window |  # 独立窗口
            Qt.WindowType.WindowStaysOnTopHint  # 保持在最前
        )
        
        # 创建主布局
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 创建标签页
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # 添加各个设置页
        tab_widget.addTab(self._create_general_tab(), "常规")
        tab_widget.addTab(self._create_audio_tab(), "音频")
        tab_widget.addTab(self._create_asr_tab(), "语音识别")
        
        # 创建按钮布局
        button_layout = QHBoxLayout()
        
        # 添加重置按钮
        reset_button = QPushButton("重置为默认")
        reset_button.clicked.connect(self._reset_settings)
        button_layout.addWidget(reset_button)
        
        # 添加保存按钮
        button_layout.addStretch()
        save_button = QPushButton("保存")
        save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(save_button)
        
        layout.addLayout(button_layout)

    def save_settings(self):
        """保存设置"""
        try:
            # 保存快捷键设置
            self.settings_manager.set_hotkey(self.hotkey_combo.currentText())
            
            # 保存音频设置
            self.settings_manager.set_setting('audio.input_device', 
                self.input_device.currentText() if self.input_device.currentText() != "系统默认" else None)
            # 将0-20的值转换为0-1000范围后保存
            volume_value = int(self.volume_threshold.value() * 1000 / 20)
            self.settings_manager.set_setting('audio.volume_threshold', volume_value)
            
            # 保存ASR设置
            self.settings_manager.set_setting('asr.model_path', 
                self.asr_model_path.text())
            self.settings_manager.set_setting('asr.punc_model_path', 
                self.punc_model_path.text())
            self.settings_manager.set_setting('asr.auto_punctuation', 
                self.auto_punctuation.isChecked())
            
            self.settings_saved.emit()
            print("✓ 设置已保存")
        except Exception as e:
            print(f"❌ 保存设置失败: {e}")

    def closeEvent(self, event):
        """窗口关闭事件"""
        # 可以在这里添加关闭前的确认或其他逻辑
        event.accept()

    def _create_general_tab(self):
        """创建常规设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 快捷键设置组
        hotkey_group = QGroupBox("快捷键设置")
        hotkey_layout = QVBoxLayout()
        
        description = QLabel("选择录音快捷键：")
        self.hotkey_combo = QComboBox()
        self.hotkey_combo.addItems(['fn', 'ctrl', 'alt'])
        current_hotkey = self.settings_manager.get_hotkey()
        self.hotkey_combo.setCurrentText(current_hotkey)
        
        help_text = QLabel("按住所选按键开始录音，释放按键结束录音")
        help_text.setStyleSheet("color: gray;")
        
        hotkey_layout.addWidget(description)
        hotkey_layout.addWidget(self.hotkey_combo)
        hotkey_layout.addWidget(help_text)
        hotkey_group.setLayout(hotkey_layout)
        
        layout.addWidget(hotkey_group)
        layout.addStretch()
        tab.setLayout(layout)
        return tab

    def _create_audio_tab(self):
        """创建音频设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 音频设备设置
        device_group = QGroupBox("音频设备")
        device_layout = QVBoxLayout()
        
        self.input_device = QComboBox()
        # TODO: 添加可用的音频设备列表
        self.input_device.addItem("系统默认")
        current_device = self.settings_manager.get_setting('audio.input_device')
        if current_device:
            self.input_device.setCurrentText(current_device)
        
        device_layout.addWidget(QLabel("输入设备："))
        device_layout.addWidget(self.input_device)
        device_group.setLayout(device_layout)
        
        # 音频控制设置
        control_group = QGroupBox("音频控制")
        control_layout = QVBoxLayout()
        
        # 创建音量阈值滑块和标签的水平布局
        volume_layout = QHBoxLayout()
        volume_label = QLabel("音量阈值：")
        self.volume_value_label = QLabel("6")  # 显示当前值的标签
        self.volume_value_label.setMinimumWidth(30)  # 设置最小宽度确保对齐
        
        # 创建滑块
        self.volume_threshold = QSlider(Qt.Orientation.Horizontal)
        self.volume_threshold.setRange(0, 20)  # 0-20 对应 0-0.02
        self.volume_threshold.setValue(int(self.settings_manager.get_setting('audio.volume_threshold') * 20 / 1000))
        self.volume_threshold.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.volume_threshold.setTickInterval(1)  # 每0.001一个刻度
        
        # 连接滑块值变化信号
        self.volume_threshold.valueChanged.connect(
            lambda value: self.volume_value_label.setText(str(value))
        )
        
        # 添加控件到布局
        volume_layout.addWidget(volume_label)
        volume_layout.addWidget(self.volume_threshold)
        volume_layout.addWidget(self.volume_value_label)
        
        # 添加帮助文本
        help_text = QLabel("数值越小，麦克风越灵敏。建议值：5-7\n"
                          "当音量低于阈值时会被视为静音。默认值：6")
        help_text.setStyleSheet("color: gray; font-size: 12px;")
        help_text.setWordWrap(True)  # 允许文本换行
        
        control_layout.addLayout(volume_layout)
        control_layout.addWidget(help_text)
        control_group.setLayout(control_layout)
        
        layout.addWidget(device_group)
        layout.addWidget(control_group)
        layout.addStretch()
        tab.setLayout(layout)
        return tab

    def _create_asr_tab(self):
        """创建语音识别设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 模型设置
        model_group = QGroupBox("模型设置")
        model_layout = QVBoxLayout()
        
        # ASR模型路径
        asr_layout = QHBoxLayout()
        self.asr_model_path = QLineEdit()
        self.asr_model_path.setText(self.settings_manager.get_setting('asr.model_path'))
        asr_browse = QPushButton("浏览...")
        asr_browse.clicked.connect(lambda: self._browse_model('asr'))
        asr_layout.addWidget(QLabel("ASR模型路径："))
        asr_layout.addWidget(self.asr_model_path)
        asr_layout.addWidget(asr_browse)
        
        # 标点符号模型路径
        punc_layout = QHBoxLayout()
        self.punc_model_path = QLineEdit()
        self.punc_model_path.setText(self.settings_manager.get_setting('asr.punc_model_path'))
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
        
        self.auto_punctuation = QCheckBox("自动添加标点")
        self.auto_punctuation.setChecked(self.settings_manager.get_setting('asr.auto_punctuation'))
        
        self.real_time_display = QCheckBox("实时显示识别结果")
        self.real_time_display.setChecked(self.settings_manager.get_setting('asr.real_time_display'))
        
        recognition_layout.addWidget(self.auto_punctuation)
        recognition_layout.addWidget(self.real_time_display)
        recognition_group.setLayout(recognition_layout)
        
        layout.addWidget(model_group)
        layout.addWidget(recognition_group)
        layout.addStretch()
        tab.setLayout(layout)
        return tab

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

    def _reset_settings(self):
        """重置所有设置为默认值"""
        if self.settings_manager.reset_to_defaults():
            self._load_settings()

    def _load_settings(self):
        """从设置管理器加载设置到UI"""
        # 更新所有UI控件的值
        self.hotkey_combo.setCurrentText(self.settings_manager.get_hotkey())
        
        # 更新音频设置
        current_device = self.settings_manager.get_setting('audio.input_device')
        if current_device:
            self.input_device.setCurrentText(current_device)
        # 将0-1000的值转换为0-20范围
        saved_value = self.settings_manager.get_setting('audio.volume_threshold')
        slider_value = int(saved_value * 20 / 1000)
        self.volume_threshold.setValue(slider_value)
        
        # 更新ASR设置
        self.asr_model_path.setText(self.settings_manager.get_setting('asr.model_path'))
        self.punc_model_path.setText(self.settings_manager.get_setting('asr.punc_model_path'))
        self.auto_punctuation.setChecked(self.settings_manager.get_setting('asr.auto_punctuation'))