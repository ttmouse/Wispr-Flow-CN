#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试列表展示功能的脚本
用于验证重构后的组件是否正常工作
"""

import sys
import os
sys.path.append('src')

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt6.QtCore import Qt
from ui.components.modern_list_widget import ModernListWidget
from ui.components.history_manager import HistoryManager

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("列表展示测试")
        self.setGeometry(100, 100, 400, 600)
        
        # 创建历史记录管理器
        history_file = os.path.join(os.path.expanduser("~"), ".asr_funasr", "test_history.json")
        self.history_manager = HistoryManager(history_file)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # 创建列表组件
        self.list_widget = ModernListWidget()
        layout.addWidget(self.list_widget)
        
        # 创建测试按钮
        self.add_button = QPushButton("添加测试记录")
        self.add_button.clicked.connect(self.add_test_record)
        layout.addWidget(self.add_button)
        
        self.clear_button = QPushButton("清空列表")
        self.clear_button.clicked.connect(self.clear_list)
        layout.addWidget(self.clear_button)
        
        # 测试数据
        self.test_texts = [
            "这是一条短文本",
            "这是一条比较长的文本，用来测试自动换行功能是否正常工作，看看在不同宽度下的显示效果",
            "包含<b>HTML标签</b>的文本测试",
            "多行文本测试\n第二行内容\n第三行内容",
            "特殊字符测试：！@#￥%……&*（）——+｜【】{}；'："
        ]
        self.current_index = 0
    
    def add_test_record(self):
        """添加测试记录"""
        if self.current_index < len(self.test_texts):
            text = self.test_texts[self.current_index]
            
            # 使用历史记录管理器添加
            if self.history_manager.add_history_item(text):
                self.list_widget.addItem(text)
                print(f"添加记录: {text[:30]}...")
            else:
                print(f"跳过重复记录: {text[:30]}...")
            
            self.current_index += 1
        else:
            print("所有测试记录已添加完毕")
    
    def clear_list(self):
        """清空列表"""
        self.list_widget.clear()
        self.history_manager.clear_history()
        self.current_index = 0
        print("列表已清空")

def main():
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()