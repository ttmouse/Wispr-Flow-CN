#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试HTML渲染效果
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HTML渲染测试")
        self.setGeometry(100, 100, 600, 400)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 测试不同的文本格式
        test_texts = [
            "普通文本",
            "<span style='background-color: #ffeb3b; color: #000; font-weight: bold; padding: 1px 3px; border-radius: 3px;'>浮层</span>是一个很好的功能",
            "这个<span style='background-color: #ffeb3b; color: #000; font-weight: bold; padding: 1px 3px; border-radius: 3px;'>浮层</span>很漂亮",
            "<b>加粗文本</b>",
            "<i>斜体文本</i>",
            "<span style='color: red;'>红色文本</span>"
        ]
        
        for i, text in enumerate(test_texts):
            # PlainText 标签
            plain_label = QLabel(f"PlainText {i+1}: {text}")
            plain_label.setTextFormat(Qt.TextFormat.PlainText)
            layout.addWidget(plain_label)
            
            # RichText 标签
            rich_label = QLabel(f"RichText {i+1}: {text}")
            rich_label.setTextFormat(Qt.TextFormat.RichText)
            layout.addWidget(rich_label)
            
            # 分隔线
            separator = QLabel("-" * 50)
            layout.addWidget(separator)

def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()