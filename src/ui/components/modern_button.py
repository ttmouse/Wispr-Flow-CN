from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon

class ModernButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setFixedSize(64, 64)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 设置图标
        self.setIcon(QIcon("resources/mic.png"))
        self.setIconSize(QSize(24, 24))
        
        # 设置样式
        self.setStyleSheet("""
            QPushButton {
                background-color: black;
                border-radius: 32px;
                border: none;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #1a1a1a;
            }
            QPushButton:pressed {
                background-color: #333333;
            }
        """)
    
    def set_recording_state(self, is_recording):
        """设置录音状态"""
        if is_recording:
            self.setIcon(QIcon("resources/mic-recording.svg"))
            self.setStyleSheet("""
                QPushButton {
                    background-color: #D32F2F;
                    border-radius: 32px;
                    border: none;
                    padding: 0;
                }
                QPushButton:hover {
                    background-color: #B71C1C;
                }
                QPushButton:pressed {
                    background-color: #961717;
                }
            """)
        else:
            self.setIcon(QIcon("resources/mic.png"))
            self.setStyleSheet("""
                QPushButton {
                    background-color: black;
                    border-radius: 32px;
                    border: none;
                    padding: 0;
                }
                QPushButton:hover {
                    background-color: #1a1a1a;
                }
                QPushButton:pressed {
                    background-color: #333333;
                }
            """) 