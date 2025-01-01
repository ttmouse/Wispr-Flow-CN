from PyQt6.QtWidgets import QPushButton
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

class ModernButton(QPushButton):
    def __init__(self, text, parent=None, primary=False):
        super().__init__(text, parent)
        self.primary = primary
        self.setMinimumHeight(36)
        self.setFont(QFont("", 13))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                background-color: """ + ("#007AFF" if primary else "#F5F5F7") + """;
                color: """ + ("#FFFFFF" if primary else "#1D1D1F") + """;
            }
            QPushButton:hover {
                background-color: """ + ("#0051FF" if primary else "#E5E5E7") + """;
            }
            QPushButton:pressed {
                background-color: """ + ("#0041CC" if primary else "#D5D5D7") + """;
            }
            QPushButton:disabled {
                background-color: """ + ("#99C5FF" if primary else "#F5F5F7") + """;
                color: """ + ("#FFFFFF" if primary else "#8E8E93") + """;
            }
        """) 