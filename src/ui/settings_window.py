from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                            QLabel, QComboBox, QPushButton, QGroupBox)
from PyQt6.QtCore import Qt, pyqtSignal

class SettingsWindow(QDialog):
    # 定义信号
    hotkey_changed = pyqtSignal(str)  # 当快捷键改变时发出信号

    def __init__(self, parent=None, current_hotkey='fn'):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(300)
        
        # 创建主布局
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 创建快捷键设置组
        hotkey_group = QGroupBox("快捷键设置")
        hotkey_layout = QVBoxLayout()
        
        # 添加说明标签
        description = QLabel("选择录音快捷键：")
        description.setWordWrap(True)
        hotkey_layout.addWidget(description)
        
        # 创建下拉框
        self.hotkey_combo = QComboBox()
        self.hotkey_combo.addItems(['fn', 'ctrl', 'alt'])
        # 设置当前值
        self.hotkey_combo.setCurrentText(current_hotkey)
        hotkey_layout.addWidget(self.hotkey_combo)
        
        # 添加说明文本
        help_text = QLabel("按住所选按键开始录音，释放按键结束录音")
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: gray;")
        hotkey_layout.addWidget(help_text)
        
        hotkey_group.setLayout(hotkey_layout)
        layout.addWidget(hotkey_group)
        
        # 创建按钮布局
        button_layout = QHBoxLayout()
        
        # 添加确定和取消按钮
        ok_button = QPushButton("确定")
        cancel_button = QPushButton("取消")
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        # 连接信号
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        self.hotkey_combo.currentTextChanged.connect(self._on_hotkey_changed)
    
    def _on_hotkey_changed(self, value):
        """当快捷键选择改变时触发"""
        self.hotkey_changed.emit(value)
    
    def get_current_hotkey(self):
        """获取当前选择的快捷键"""
        return self.hotkey_combo.currentText()