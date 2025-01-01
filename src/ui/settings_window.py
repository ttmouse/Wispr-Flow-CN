from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTextEdit, 
                            QPushButton, QLabel, QHBoxLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import json
import os

class SettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setFixedSize(400, 500)
        
        # 设置为模态对话框
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        # 设置窗口标志
        self.setWindowFlags(Qt.WindowType.Window | 
                          Qt.WindowType.WindowCloseButtonHint | 
                          Qt.WindowType.WindowTitleHint)
        
        # 设置窗口样式
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                color: #1D1D1F;
                font-size: 14px;
                margin-bottom: 8px;
            }
            QTextEdit {
                border: 1px solid #E5E5E7;
                border-radius: 6px;
                padding: 12px;
                font-size: 14px;
                line-height: 1.4;
                background-color: white;
                color: #1D1D1F;
            }
            QPushButton {
                background-color: black;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #1a1a1a;
            }
            QPushButton:pressed {
                background-color: #333333;
            }
        """)
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 高频词说明
        description = QLabel("请输入高频词（每行一个）：")
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # 高频词输入框
        self.words_edit = QTextEdit()
        self.words_edit.setPlaceholderText("例如：\n人工智能\n机器学习\n深度学习")
        self.words_edit.setAcceptRichText(False)
        self.words_edit.setMinimumHeight(300)
        self.words_edit.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.words_edit.setReadOnly(False)
        self.words_edit.setEnabled(True)
        layout.addWidget(self.words_edit)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #E5E5E7;
                color: #1D1D1F;
            }
            QPushButton:hover {
                background-color: #D5D5D7;
            }
            QPushButton:pressed {
                background-color: #C5C5C7;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def showEvent(self, event):
        """窗口显示时设置焦点"""
        super().showEvent(event)
        # 确保窗口在最前面并获得焦点
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        self.activateWindow()
        self.raise_()
        # 设置焦点到输入框
        self.words_edit.setFocus()
        QDialog.showEvent(self, event)
    
    def load_settings(self):
        """加载设置"""
        try:
            if os.path.exists("settings.json"):
                with open("settings.json", "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    words = settings.get("high_frequency_words", [])
                    self.words_edit.setText("\n".join(words))
        except Exception as e:
            print(f"加载设置失败: {e}")
    
    def save_settings(self):
        """保存设置"""
        try:
            # 获取并处理高频词
            text = self.words_edit.toPlainText()
            words = [word.strip() for word in text.split("\n") if word.strip()]
            
            # 保存设置
            settings = {
                "high_frequency_words": words
            }
            
            with open("settings.json", "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            self.accept()
        except Exception as e:
            print(f"保存设置失败: {e}")
    
    @staticmethod
    def get_high_frequency_words():
        """获取高频词列表"""
        try:
            if os.path.exists("settings.json"):
                with open("settings.json", "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    return settings.get("high_frequency_words", [])
        except Exception as e:
            print(f"读取高频词失败: {e}")
        return []