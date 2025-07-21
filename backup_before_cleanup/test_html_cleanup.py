#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit, QLabel
from PyQt6.QtCore import Qt
from main import clean_html_tags

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HTML标签清理测试")
        self.setGeometry(100, 100, 600, 400)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 测试用例
        test_cases = [
            '<span style="background-color: #ffeb3b; color: #000; font-weight: bold; padding: 1px 3px; border-radius: 3px;">浮层</span>是一个不错的效果。',
            '支持在主界面的 <span style="background-color: #ffeb3b; color: #000; font-weight: bold; padding: 1px 3px; border-radius: 3px;">UI</span> 中高亮。',
            '不要改变复制后的文本。'
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            # 原始HTML文本
            layout.addWidget(QLabel(f"测试用例 {i} - 原始HTML:"))
            original_text = QTextEdit()
            original_text.setPlainText(test_case)
            original_text.setMaximumHeight(60)
            layout.addWidget(original_text)
            
            # 清理后的文本
            layout.addWidget(QLabel(f"测试用例 {i} - 清理后的纯文本:"))
            cleaned_text = QTextEdit()
            cleaned_text.setPlainText(clean_html_tags(test_case))
            cleaned_text.setMaximumHeight(60)
            layout.addWidget(cleaned_text)
            
            layout.addWidget(QLabel("---"))
        
        # 综合测试
        layout.addWidget(QLabel("综合测试结果:"))
        combined_html = ''.join(test_cases)
        combined_clean = clean_html_tags(combined_html)
        
        result_text = QTextEdit()
        result_text.setPlainText(f"原始: {combined_html}\n\n清理后: {combined_clean}")
        layout.addWidget(result_text)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())