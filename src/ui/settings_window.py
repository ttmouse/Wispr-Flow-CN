from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QComboBox, QPushButton, QGroupBox,
                            QCheckBox, QSlider, QTabWidget,
                            QLineEdit, QFileDialog, QTextEdit, QMessageBox, QDialog)
from PyQt6.QtCore import Qt, pyqtSignal
from pathlib import Path
import pyaudio

class SettingsWindow(QDialog):
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
        tab_widget.addTab(self._create_paste_tab(), "粘贴设置")
        tab_widget.addTab(self._create_hotwords_settings_tab(), "热词设置")
        tab_widget.addTab(self._create_hotwords_edit_tab(), "热词编辑")
        
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
            # 收集所有设置到字典中
            settings_to_save = {}
            
            # 检查热键方案是否发生变化
            old_scheme = self.settings_manager.get_hotkey_scheme()
            new_scheme = None
            scheme_changed = False
            
            # 收集热键方案设置
            try:
                scheme_value = self.hotkey_scheme_combo.currentText()
                new_scheme = scheme_value
                scheme_changed = (old_scheme != new_scheme)
                settings_to_save['hotkey_scheme'] = scheme_value
            except Exception as e:
                import logging
                logging.error(f"收集热键方案设置失败: {e}")
                raise
            
            # 收集快捷键设置
            try:
                hotkey_value = self.hotkey_combo.currentText()
                settings_to_save['hotkey'] = hotkey_value
            except Exception as e:
                import logging
                logging.error(f"收集快捷键设置失败: {e}")
                raise
            
            # 收集音频设备设置
            try:
                device_text = self.input_device.currentText()
                
                # 如果是系统默认设备，提取实际的设备名称
                if device_text.startswith("系统默认 ("):
                    device_name = None  # 使用 None 表示系统默认设备
                else:
                    device_name = device_text
                
                settings_to_save['audio.input_device'] = device_name
            except Exception as e:
                import logging
                logging.error(f"收集音频设备设置失败: {e}")
                # 不抛出异常，继续收集其他设置
            
            # 收集音频控制设置
            try:
                # 将0-20的值转换为0-1000范围后保存
                volume_value = int(self.volume_threshold.value() * 1000 / 20)
                settings_to_save['audio.volume_threshold'] = volume_value
                
                # 收集录音时长设置
                duration_value = self.recording_duration.value()
                settings_to_save['audio.max_recording_duration'] = duration_value
            except Exception as e:
                import logging
                logging.error(f"收集音频控制设置失败: {e}")
                raise
            
            # 收集ASR设置
            try:
                asr_model_path = self.asr_model_path.text()
                punc_model_path = self.punc_model_path.text()
                auto_punctuation = self.auto_punctuation.isChecked()
                
                settings_to_save['asr.model_path'] = asr_model_path
                settings_to_save['asr.punc_model_path'] = punc_model_path
                settings_to_save['asr.auto_punctuation'] = auto_punctuation
            except Exception as e:
                import logging
                logging.error(f"收集ASR设置失败: {e}")
                raise
            
            # 收集热词设置
            try:
                hotword_weight = self.hotword_weight.value()  # 保持为int类型
                pronunciation_correction = self.enable_pronunciation_correction.isChecked()
                
                # 确保热词权重是有效的整数值
                if not isinstance(hotword_weight, int) or hotword_weight < 10 or hotword_weight > 100:
                    raise ValueError(f"热词权重值无效: {hotword_weight}，应该是10-100之间的整数")
                
                settings_to_save['asr.hotword_weight'] = hotword_weight
                settings_to_save['asr.enable_pronunciation_correction'] = pronunciation_correction
            except Exception as e:
                import logging
                logging.error(f"收集热词设置失败: {e}")
                import traceback
                logging.error(f"热词设置错误详情: {traceback.format_exc()}")
                raise
            
            # 收集粘贴延迟设置
            try:
                transcription_delay = self.transcription_delay.value()
                history_delay = self.history_delay.value()
                
                settings_to_save['paste.transcription_delay'] = transcription_delay
                settings_to_save['paste.history_click_delay'] = history_delay
            except Exception as e:
                import logging
                logging.error(f"收集粘贴延迟设置失败: {e}")
                raise
            
            # 收集快捷键延迟设置
            try:
                recording_start_delay = self.recording_start_delay.value()
                settings_to_save['hotkey_settings.recording_start_delay'] = recording_start_delay
            except Exception as e:
                import logging
                logging.error(f"收集快捷键延迟设置失败: {e}")
                raise
            
            # 批量保存所有设置
            if not self.settings_manager.set_multiple_settings(settings_to_save):
                raise Exception("批量保存设置失败")
            
            # 应用音频设备设置
            try:
                device_text = self.input_device.currentText()
                if device_text.startswith("系统默认 ("):
                    device_name = None
                else:
                    device_name = device_text
                
                if self.audio_capture:
                    success = self.audio_capture.set_device(device_name)
                    if not success:
                        import logging
                        logging.warning("音频设备设置失败，但设置已保存")
                else:
                    import logging
                    logging.warning("audio_capture 实例不存在")
            except Exception as e:
                import logging
                logging.error(f"应用音频设备设置失败: {e}")
                # 不抛出异常，因为设置已经保存成功
            
            # 如果热键方案发生变化，应用新的热键管理器
            if scheme_changed:
                try:
                    # 获取主应用实例并应用新的热键方案
                    parent_window = self.parent()
                    if parent_window and hasattr(parent_window, 'app_instance'):
                        app_instance = parent_window.app_instance
                        if app_instance and hasattr(app_instance, 'apply_settings'):
                            # 使用apply_settings方法来应用新的热键方案
                            app_instance.apply_settings()
                            import logging
                            logging.info(f"热键方案已从 {old_scheme} 切换到 {new_scheme}，新方案已立即应用")
                        else:
                            import logging
                            logging.info(f"热键方案已从 {old_scheme} 切换到 {new_scheme}，将在下次启动时生效")
                    else:
                        import logging
                        logging.info(f"热键方案已从 {old_scheme} 切换到 {new_scheme}，将在下次启动时生效")
                except Exception as e:
                    import logging
                    logging.error(f"应用新热键方案失败: {e}")
                    # 不抛出异常，因为设置已经保存成功
            
            # 发出保存完成信号（使用线程安全的方式）
            try:
                # 使用 QTimer.singleShot 确保信号在主线程中发射
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(0, self._emit_settings_saved_signal)
            except Exception as e:
                import logging
                logging.error(f"发出保存信号失败: {e}")
                # 不抛出异常，因为设置已经保存成功
            
            # 直接关闭设置窗口，不显示成功提示
            try:
                self.close()
            except Exception as e:
                import logging
                logging.error(f"关闭窗口失败: {e}")
                # 不抛出异常
            
        except Exception as e:
            import traceback
            import logging
            error_msg = f"保存设置失败: {e}\n{traceback.format_exc()}"
            logging.error(error_msg)
            
            # 显示错误对话框
            try:
                QMessageBox.critical(self, "保存失败", f"保存设置时发生错误:\n\n{str(e)}\n\n请检查控制台输出获取详细信息。")
            except Exception as dialog_error:
                logging.error(f"显示错误对话框失败: {dialog_error}")

    def _emit_settings_saved_signal(self):
        """发出设置保存完成信号"""
        try:
            self.settings_saved.emit()
        except Exception as e:
            import logging
            logging.error(f"发出设置保存信号失败: {e}")

    def closeEvent(self, event):
        """窗口关闭事件"""
        try:
            # 清理音频资源
            self._cleanup_audio()
            
            # 断开所有信号连接，防止悬空指针
            try:
                self.settings_changed.disconnect()
            except:
                pass
            try:
                self.settings_saved.disconnect()
            except:
                pass
            
        except Exception as e:
            import logging
            logging.error(f"关闭设置窗口时出错: {e}")
        finally:
            event.accept()

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

    def _create_general_tab(self):
        """创建常规设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 热键方案设置组
        scheme_group = QGroupBox("热键方案设置")
        scheme_layout = QVBoxLayout()
        
        scheme_description = QLabel("选择热键监听方案：")
        self.hotkey_scheme_combo = QComboBox()
        self.hotkey_scheme_combo.addItems(['hammerspoon', 'python'])
        current_scheme = self.settings_manager.get_hotkey_scheme()
        self.hotkey_scheme_combo.setCurrentText(current_scheme)
        
        scheme_help_text = QLabel("Hammerspoon方案：更稳定，需要安装Hammerspoon\nPython方案：原生实现，可能在某些情况下不稳定")
        scheme_help_text.setStyleSheet("color: gray; font-size: 12px;")
        scheme_help_text.setWordWrap(True)
        
        scheme_layout.addWidget(scheme_description)
        scheme_layout.addWidget(self.hotkey_scheme_combo)
        scheme_layout.addWidget(scheme_help_text)
        scheme_group.setLayout(scheme_layout)
        
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
        
        # 快捷键延迟设置组
        delay_group = QGroupBox("快捷键延迟设置")
        delay_layout = QVBoxLayout()
        
        # 录制启动延迟设置
        start_delay_layout = QHBoxLayout()
        start_delay_label = QLabel("录制启动延迟：")
        self.start_delay_value_label = QLabel("50ms")  # 显示当前值的标签
        self.start_delay_value_label.setMinimumWidth(50)  # 设置最小宽度确保对齐
        
        # 创建滑块
        self.recording_start_delay = QSlider(Qt.Orientation.Horizontal)
        self.recording_start_delay.setRange(50, 500)  # 50-500ms
        self.recording_start_delay.setValue(self.settings_manager.get_setting('hotkey_settings.recording_start_delay', 50))
        self.recording_start_delay.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.recording_start_delay.setTickInterval(50)  # 每50ms一个刻度
        
        # 连接滑块值变化信号
        self.recording_start_delay.valueChanged.connect(
            lambda value: self.start_delay_value_label.setText(f"{value}ms")
        )
        
        # 添加控件到布局
        start_delay_layout.addWidget(start_delay_label)
        start_delay_layout.addWidget(self.recording_start_delay)
        start_delay_layout.addWidget(self.start_delay_value_label)
        
        # 添加帮助文本
        delay_help_text = QLabel("按下快捷键后等待多长时间才开始录制，用于避免组合快捷键误触发。\n数值越小启动越快，但可能误触发；数值越大越安全，但启动较慢。建议值：50-150ms")
        delay_help_text.setStyleSheet("color: gray; font-size: 12px;")
        delay_help_text.setWordWrap(True)  # 允许文本换行
        
        delay_layout.addLayout(start_delay_layout)
        delay_layout.addWidget(delay_help_text)
        delay_group.setLayout(delay_layout)
        
        layout.addWidget(scheme_group)
        layout.addWidget(hotkey_group)
        layout.addWidget(delay_group)
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
        # 修复音量阈值初始化：正确的计算公式
        current_threshold = self.settings_manager.get_setting('audio.volume_threshold', 150)
        slider_value = int(current_threshold * 20 / 1000)
        self.volume_threshold.setValue(slider_value)
        # 更新显示标签
        self.volume_value_label.setText(str(slider_value))
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
        self.auto_punctuation.setChecked(self.settings_manager.get_setting('asr.auto_punctuation', True))
        
        self.real_time_display = QCheckBox("实时显示识别结果")
        self.real_time_display.setChecked(self.settings_manager.get_setting('asr.real_time_display', True))
        
        recognition_layout.addWidget(self.auto_punctuation)
        recognition_layout.addWidget(self.real_time_display)
        recognition_group.setLayout(recognition_layout)
        
        layout.addWidget(model_group)
        layout.addWidget(recognition_group)
        layout.addStretch()
        tab.setLayout(layout)
        return tab

    def _create_paste_tab(self):
        """创建粘贴设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 粘贴延迟设置组
        paste_group = QGroupBox("粘贴延迟设置")
        paste_layout = QVBoxLayout()
        
        # 转录完成后粘贴延迟
        transcription_layout = QHBoxLayout()
        transcription_label = QLabel("转录完成后延迟：")
        self.transcription_delay_value_label = QLabel("0ms")
        self.transcription_delay_value_label.setMinimumWidth(50)
        
        self.transcription_delay = QSlider(Qt.Orientation.Horizontal)
        self.transcription_delay.setRange(0, 200)  # 0-200毫秒
        self.transcription_delay.setValue(self.settings_manager.get_setting('paste.transcription_delay', 0))
        self.transcription_delay.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.transcription_delay.setTickInterval(20)
        
        # 连接滑块值变化信号
        self.transcription_delay.valueChanged.connect(
            lambda value: self.transcription_delay_value_label.setText(f"{value}ms")
        )
        
        transcription_layout.addWidget(transcription_label)
        transcription_layout.addWidget(self.transcription_delay)
        transcription_layout.addWidget(self.transcription_delay_value_label)
        
        # 添加帮助文本
        transcription_help = QLabel("转录完成后等待多长时间再执行粘贴操作。数值越大，粘贴越稳定，但响应稍慢。建议值：20-50ms")
        transcription_help.setStyleSheet("color: gray; font-size: 12px;")
        transcription_help.setWordWrap(True)
        
        paste_layout.addLayout(transcription_layout)
        paste_layout.addWidget(transcription_help)
        
        # 历史记录点击后粘贴延迟
        history_layout = QHBoxLayout()
        history_label = QLabel("历史记录点击后延迟：")
        self.history_delay_value_label = QLabel("0ms")
        self.history_delay_value_label.setMinimumWidth(50)
        
        self.history_delay = QSlider(Qt.Orientation.Horizontal)
        self.history_delay.setRange(0, 200)  # 0-200毫秒
        self.history_delay.setValue(self.settings_manager.get_setting('paste.history_click_delay', 0))
        self.history_delay.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.history_delay.setTickInterval(20)
        
        # 连接滑块值变化信号
        self.history_delay.valueChanged.connect(
            lambda value: self.history_delay_value_label.setText(f"{value}ms")
        )
        
        history_layout.addWidget(history_label)
        history_layout.addWidget(self.history_delay)
        history_layout.addWidget(self.history_delay_value_label)
        
        # 添加帮助文本
        history_help = QLabel("点击历史记录项后等待多长时间再执行粘贴操作。数值越大，粘贴越稳定，但响应稍慢。建议值：30-80ms")
        history_help.setStyleSheet("color: gray; font-size: 12px;")
        history_help.setWordWrap(True)
        
        paste_layout.addLayout(history_layout)
        paste_layout.addWidget(history_help)
        
        paste_group.setLayout(paste_layout)
        
        layout.addWidget(paste_group)
        layout.addStretch()
        tab.setLayout(layout)
        return tab

    def _create_hotwords_settings_tab(self):
        """创建热词设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 热词权重设置
        weight_group = QGroupBox("热词权重")
        weight_layout = QVBoxLayout()
        
        weight_slider_layout = QHBoxLayout()
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
        
        weight_slider_layout.addWidget(weight_label)
        weight_slider_layout.addWidget(self.hotword_weight)
        weight_slider_layout.addWidget(self.hotword_weight_value_label)
        
        # 添加帮助文本
        weight_help = QLabel("数值越大，热词识别优先级越高。建议值：60-90")
        weight_help.setStyleSheet("color: gray; font-size: 12px;")
        weight_help.setWordWrap(True)
        
        weight_layout.addLayout(weight_slider_layout)
        weight_layout.addWidget(weight_help)
        weight_group.setLayout(weight_layout)
        
        # 发音纠错设置
        correction_group = QGroupBox("发音纠错")
        correction_layout = QVBoxLayout()
        
        self.enable_pronunciation_correction = QCheckBox("启用发音相似词纠错")
        self.enable_pronunciation_correction.setChecked(
            self.settings_manager.get_setting('asr.enable_pronunciation_correction', True)
        )
        
        correction_help = QLabel("自动将发音相似的词纠正为热词（如：含高→行高）")
        correction_help.setStyleSheet("color: gray; font-size: 12px;")
        correction_help.setWordWrap(True)
        
        correction_layout.addWidget(self.enable_pronunciation_correction)
        correction_layout.addWidget(correction_help)
        correction_group.setLayout(correction_layout)
        
        layout.addWidget(weight_group)
        layout.addWidget(correction_group)
        layout.addStretch()
        tab.setLayout(layout)
        return tab

    def _create_hotwords_edit_tab(self):
        """创建热词编辑标签页"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 热词编辑区域
        hotword_edit_group = QGroupBox("热词列表")
        hotword_edit_layout = QVBoxLayout()
        
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
        
        # 热词编辑按钮
        hotword_button_layout = QHBoxLayout()
        save_hotwords_btn = QPushButton("保存热词")
        save_hotwords_btn.clicked.connect(self._save_hotwords)
        
        hotword_button_layout.addWidget(save_hotwords_btn)
        hotword_button_layout.addStretch()
        
        hotword_edit_help = QLabel("修改后请点击'保存热词'按钮保存更改，重新开始录音后生效")
        hotword_edit_help.setStyleSheet("color: gray; font-size: 12px;")
        hotword_edit_help.setWordWrap(True)
        
        hotword_edit_layout.addWidget(self.hotword_text_edit)
        hotword_edit_layout.addLayout(hotword_button_layout)
        hotword_edit_layout.addWidget(hotword_edit_help)
        hotword_edit_group.setLayout(hotword_edit_layout)
        
        layout.addWidget(hotword_edit_group)
        layout.addStretch()
        tab.setLayout(layout)
        
        # 自动加载热词
        self._load_hotwords()
        
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
        
        # 更新热键方案设置
        current_scheme = self.settings_manager.get_hotkey_scheme()
        self.hotkey_scheme_combo.setCurrentText(current_scheme)
        
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
        self.asr_model_path.setText(self.settings_manager.get_setting('asr.model_path', ''))
        self.punc_model_path.setText(self.settings_manager.get_setting('asr.punc_model_path', ''))
        self.auto_punctuation.setChecked(self.settings_manager.get_setting('asr.auto_punctuation', True))
        self.real_time_display.setChecked(self.settings_manager.get_setting('asr.real_time_display', True))
        
        # 更新热词设置
        hotword_weight = int(self.settings_manager.get_setting('asr.hotword_weight', 80))
        self.hotword_weight.setValue(hotword_weight)
        self.hotword_weight_value_label.setText(str(hotword_weight))
        self.enable_pronunciation_correction.setChecked(
            self.settings_manager.get_setting('asr.enable_pronunciation_correction', True)
        )
        
        # 更新粘贴延迟设置
        transcription_delay = self.settings_manager.get_setting('paste.transcription_delay', 30)
        history_delay = self.settings_manager.get_setting('paste.history_click_delay', 50)
        self.transcription_delay.setValue(transcription_delay)
        self.history_delay.setValue(history_delay)
        self.transcription_delay_value_label.setText(f"{transcription_delay}ms")
        self.history_delay_value_label.setText(f"{history_delay}ms")
        
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
    
    def _save_hotwords(self):
        """保存热词到文件"""
        try:
            content = self.hotword_text_edit.toPlainText()
            hotwords_file = Path("resources") / "hotwords.txt"
            hotwords_file.parent.mkdir(exist_ok=True)
            hotwords_file.write_text(content, encoding="utf-8")
            
            # 通知用户保存成功
            QMessageBox.information(self, "成功", "热词已保存成功！\n\n重新开始录音后生效。")
            
            # 如果有状态管理器，重新加载热词
            if hasattr(self, 'parent') and self.parent and hasattr(self.parent, 'state_manager'):
                if hasattr(self.parent.state_manager, 'reload_hotwords'):
                    self.parent.state_manager.reload_hotwords()
                    
        except Exception as e:
            import logging
            logging.error(f"保存热词失败: {e}")
            QMessageBox.critical(self, "错误", f"保存热词失败: {e}")