from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QComboBox, QPushButton, QGroupBox,
                            QCheckBox, QSlider, QTabWidget,
                            QLineEdit, QFileDialog, QTextEdit, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from pathlib import Path
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
            
            # 保存热词设置
            self.settings_manager.set_setting('asr.hotword_weight', 
                float(self.hotword_weight.value()))
            self.settings_manager.set_setting('asr.enable_pronunciation_correction', 
                self.enable_pronunciation_correction.isChecked())
            
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
        
        # 热词设置
        hotword_group = QGroupBox("热词设置")
        hotword_layout = QVBoxLayout()
        
        # 热词权重设置
        weight_layout = QHBoxLayout()
        weight_label = QLabel("热词权重：")
        self.hotword_weight_value_label = QLabel("80")
        self.hotword_weight_value_label.setMinimumWidth(30)
        
        self.hotword_weight = QSlider(Qt.Orientation.Horizontal)
        self.hotword_weight.setRange(10, 100)  # 10-100
        self.hotword_weight.setValue(int(self.settings_manager.get_setting('asr.hotword_weight', 80)))
        self.hotword_weight.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.hotword_weight.setTickInterval(10)
        
        # 连接滑块值变化信号
        self.hotword_weight.valueChanged.connect(
            lambda value: self.hotword_weight_value_label.setText(str(value))
        )
        
        weight_layout.addWidget(weight_label)
        weight_layout.addWidget(self.hotword_weight)
        weight_layout.addWidget(self.hotword_weight_value_label)
        
        # 添加帮助文本
        weight_help = QLabel("数值越大，热词识别优先级越高。建议值：60-90")
        weight_help.setStyleSheet("color: gray; font-size: 12px;")
        weight_help.setWordWrap(True)
        
        # 发音纠错设置
        self.enable_pronunciation_correction = QCheckBox("启用发音相似词纠错")
        self.enable_pronunciation_correction.setChecked(
            self.settings_manager.get_setting('asr.enable_pronunciation_correction', True)
        )
        
        correction_help = QLabel("自动将发音相似的词纠正为热词（如：含高→行高）")
        correction_help.setStyleSheet("color: gray; font-size: 12px;")
        correction_help.setWordWrap(True)
        
        # 热词编辑区域
        hotword_edit_label = QLabel("热词列表：")
        self.hotword_text_edit = QTextEdit()
        self.hotword_text_edit.setPlaceholderText("每行输入一个热词，以#开头的行为注释")
        self.hotword_text_edit.setMaximumHeight(150)
        self.hotword_text_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px;
                font-family: monospace;
                font-size: 13px;
            }
        """)
        
        # 热词编辑按钮
        hotword_button_layout = QHBoxLayout()
        load_hotwords_btn = QPushButton("重新加载")
        load_hotwords_btn.clicked.connect(self._load_hotwords)
        save_hotwords_btn = QPushButton("保存热词")
        save_hotwords_btn.clicked.connect(self._save_hotwords)
        
        hotword_button_layout.addWidget(load_hotwords_btn)
        hotword_button_layout.addWidget(save_hotwords_btn)
        hotword_button_layout.addStretch()
        
        hotword_edit_help = QLabel("修改后请点击'保存热词'按钮保存更改")
        hotword_edit_help.setStyleSheet("color: gray; font-size: 12px;")
        hotword_edit_help.setWordWrap(True)
        
        hotword_layout.addLayout(weight_layout)
        hotword_layout.addWidget(weight_help)
        hotword_layout.addWidget(self.enable_pronunciation_correction)
        hotword_layout.addWidget(correction_help)
        hotword_layout.addWidget(hotword_edit_label)
        hotword_layout.addWidget(self.hotword_text_edit)
        hotword_layout.addLayout(hotword_button_layout)
        hotword_layout.addWidget(hotword_edit_help)
        hotword_group.setLayout(hotword_layout)
        
        layout.addWidget(model_group)
        layout.addWidget(recognition_group)
        layout.addWidget(hotword_group)
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
        
        # 更新热词设置
        hotword_weight = int(self.settings_manager.get_setting('asr.hotword_weight', 80))
        self.hotword_weight.setValue(hotword_weight)
        self.hotword_weight_value_label.setText(str(hotword_weight))
        self.enable_pronunciation_correction.setChecked(
            self.settings_manager.get_setting('asr.enable_pronunciation_correction', True)
        )
        
        # 加载热词内容
        self._load_hotwords()

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
            print(f"❌ 加载热词失败: {e}")
            QMessageBox.warning(self, "错误", f"加载热词失败: {e}")
    
    def _save_hotwords(self):
        """保存热词到文件"""
        try:
            content = self.hotword_text_edit.toPlainText()
            hotwords_file = Path("resources") / "hotwords.txt"
            hotwords_file.parent.mkdir(exist_ok=True)
            hotwords_file.write_text(content, encoding="utf-8")
            
            # 通知用户保存成功
            QMessageBox.information(self, "成功", "热词已保存成功！\n\n重新开始录音后生效。")
            print("✓ 热词已保存")
            
            # 如果有状态管理器，重新加载热词
            if hasattr(self, 'parent') and self.parent and hasattr(self.parent, 'state_manager'):
                if hasattr(self.parent.state_manager, 'reload_hotwords'):
                    self.parent.state_manager.reload_hotwords()
                    
        except Exception as e:
            print(f"❌ 保存热词失败: {e}")
            QMessageBox.critical(self, "错误", f"保存热词失败: {e}")