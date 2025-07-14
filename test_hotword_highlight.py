#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试热词高亮效果
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt
from ui.components.modern_list import ModernListWidget

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("热词高亮测试")
        self.setGeometry(100, 100, 600, 400)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 创建现代化列表组件
        self.list_widget = ModernListWidget()
        layout.addWidget(self.list_widget)
        
        # 添加测试文本（包含HTML高亮）
        test_texts = [
            "普通文本没有高亮",
            '<span style="background-color: #ffeb3b; color: #000; font-weight: bold; padding: 1px 3px; border-radius: 3px;">浮层</span>是一个很好的功能。',
            '胡晨，<span style="background-color: #ffeb3b; color: #000; font-weight: bold; padding: 1px 3px; border-radius: 3px;">胡晨</span>。',
            '先帮我实现这个。',
            '这个<span style="background-color: #ffeb3b; color: #000; font-weight: bold; padding: 1px 3px; border-radius: 3px;">浮层</span>效果应该正确显示。'
        ]
        
        for text in test_texts:
            self.list_widget.addItem(text)

def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()