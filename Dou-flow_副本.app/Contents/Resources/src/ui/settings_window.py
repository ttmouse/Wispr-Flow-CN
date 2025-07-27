from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QComboBox, QPushButton, QGroupBox,
                            QCheckBox, QSlider, QTabWidget,
                            QLineEdit, QFileDialog)
from PyQt6.QtCore import Qt, pyqtSignal
import pyaudio

class SettingsWindow(QWidget):
    # 定义信号
    settings_changed = pyqtSignal(str, object)  # 当任何设置改变时发出信号
    settings_saved = pyqtSignal()  # 当设置保存时发出信号

    def __init__(self, parent=None, settings_manager=None, audio_capture=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.audio_capture = audio_capture  # 添加对 AudioCapture 实例的引用
        self.audio = None  # PyAudio 实例
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
            device_text = self.input_device.currentText()
            # 如果是系统默认设备，提取实际的设备名称
            if device_text.startswith("系统默认 ("):
                device_name = None  # 使用 None 表示系统默认设备
            else:
                device_name = device_text
                
            # 更新音频设备
            if self.audio_capture:
                self.audio_capture.set_device(device_name)
                
            self.settings_manager.set_setting('audio.input_device', device_name)
            
            # 将0-20的值转换为0-1000范围后保存
            volume_value = int(self.volume_threshold.value() * 1000 / 20)
            self.settings_manager.set_setting('audio.volume_threshold', volume_value)
            
            # 保存录音时长设置
            self.settings_manager.set_setting('audio.max_recording_duration', self.recording_duration.value())
            
            # 保存ASR设置
            self.settings_manager.set_setting('asr.model_path', 
                self.asr_model_path.text())
            self.settings_manager.set_setting('asr.punc_model_path', 
                self.punc_model_path.text())
            self.settings_manager.set_setting('asr.auto_punctuation', 
                self.auto_punctuation.isChecked())
            
            self.settings_saved.emit()
            print("✓ 设置已保存")
            
            # 关闭设置窗口
            self.close()
            
        except Exception as e:
            print(f"❌ 保存设置失败: {e}")

    def closeEvent(self, event):
        """窗口关闭事件"""
        self._cleanup_audio()
        event.accept()

    def _cleanup_audio(self):
        """清理音频资源"""
        if self.audio:
            try:
                self.audio.terminate()
            except Exception as e:
                print(f"清理音频资源失败: {e}")
            finally:
                self.audio = None

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
        self._update_audio_devices()  # 加载可用的音频设备列表
        
        # 添加刷新按钮
        device_header_layout = QHBoxLayout()
        device_header_layout.addWidget(QLabel("输入设备："))
        refresh_button = QPushButton("刷新")
        refresh_button.setFixedWidth(60)
        refresh_button.clicked.connect(self._update_audio_devices)
        device_header_layout.addWidget(refresh_button)
        
        device_layout.addLayout(device_header_layout)
        device_layout.addWidget(self.input_device)
        
        # 添加设备说明
        device_help = QLabel("选择要使用的麦克风设备，设备更改后需要重新开始录音")
        device_help.setStyleSheet("color: gray; font-size: 12px;")
        device_help.setWordWrap(True)
        device_layout.addWidget(device_help)
        
        device_group.setLayout(device_layout)
        
        # 音频控制设置
        control_group = QGroupBox("音频控制")
        control_layout = QVBoxLayout()
        
        # 创建音量阈值滑块和标签的水平布局
        volume_layout = QHBoxLayout()
        volume_label = QLabel("音量阈值：")
        self.volume_value_label = QLabel("3")  # 显示当前值的标签
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
        help_text = QLabel("数值越小，麦克风越灵敏。建议值：2-4\n"
                          "当音量低于阈值时会被视为静音。默认值：3")
        help_text.setStyleSheet("color: gray; font-size: 12px;")
        help_text.setWordWrap(True)  # 允许文本换行
        
        control_layout.addLayout(volume_layout)
        control_layout.addWidget(help_text)
        
        # 录音时长设置
        duration_layout = QHBoxLayout()
        duration_label = QLabel("最大录音时长：")
        self.duration_value_label = QLabel("10秒")  # 显示当前值的标签
        self.duration_value_label.setMinimumWidth(50)  # 设置最小宽度确保对齐
        
        # 创建滑块
        self.recording_duration = QSlider(Qt.Orientation.Horizontal)
        self.recording_duration.setRange(5, 60)  # 5-60秒
        self.recording_duration.setValue(self.settings_manager.get_setting('audio.max_recording_duration', 10))
        self.recording_duration.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.recording_duration.setTickInterval(5)  # 每5秒一个刻度
        
        # 连接滑块值变化信号
        self.recording_duration.valueChanged.connect(
            lambda value: self.duration_value_label.setText(f"{value}秒")
        )
        
        # 添加控件到布局
        duration_layout.addWidget(duration_label)
        duration_layout.addWidget(self.recording_duration)
        duration_layout.addWidget(self.duration_value_label)
        
        # 添加帮助文本
        duration_help_text = QLabel("设置录音的最大时长，超过此时长将自动停止录音。建议值：10-30秒")
        duration_help_text.setStyleSheet("color: gray; font-size: 12px;")
        duration_help_text.setWordWrap(True)  # 允许文本换行
        
        control_layout.addLayout(duration_layout)
        control_layout.addWidget(duration_help_text)
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
        
        # 更新录音时长设置
        duration_value = self.settings_manager.get_setting('audio.max_recording_duration', 10)
        self.recording_duration.setValue(duration_value)
        self.duration_value_label.setText(f"{duration_value}秒")
        
        # 更新ASR设置
        self.asr_model_path.setText(self.settings_manager.get_setting('asr.model_path'))
        self.punc_model_path.setText(self.settings_manager.get_setting('asr.punc_model_path'))
        self.auto_punctuation.setChecked(self.settings_manager.get_setting('asr.auto_punctuation'))

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
                print(f"获取默认设备失败: {e}")
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
                            print(f"发现输入设备: {name}")
                except Exception as e:
                    print(f"获取设备 {i} 信息失败: {e}")
                    continue
                    
        except Exception as e:
            print(f"获取音频设备列表失败: {e}")
            if not devices:  # 如果还没有添加任何设备
                devices = ["系统默认"]
            
        return devices

    def _update_audio_devices(self):
        """更新音频设备列表"""
        try:
            # 保存当前选择的设备
            current_device = self.input_device.currentText()
            
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
            if not device_found:
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
            
            print("✓ 设备列表已更新")
            
        except Exception as e:
            print(f"❌ 更新设备列表失败: {e}")
            # 确保至少有一个选项
            if self.input_device.count() == 0:
                self.input_device.addItem("系统默认")