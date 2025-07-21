#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试行高修复效果
验证文本长度不影响行高，只有换行才影响行高
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from src.ui.components.modern_list import TextLabel, HistoryItemWidget

class LineHeightTestWindow(QMainWindow):
    """行高测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("行高修复效果测试")
        self.setGeometry(100, 100, 600, 800)
        
        # 创建主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 添加标题
        title = QLabel("行高修复效果测试")
        title.setFont(QFont("PingFang SC", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # 测试不同长度的文本
        test_texts = [
            "短文本",
            "这是一个中等长度的文本，用来测试行高是否一致。",
            "这是一个很长的文本，包含了更多的字符，但仍然是单行显示，用来验证文本长度不会影响行高，只有换行才会影响行高。",
            "这是一个会换行的长文本，当文本超过容器宽度时会自动换行到下一行，这种情况下行高应该会增加，因为实际占用了多行空间。这个文本足够长，应该会在正常宽度下换行显示。",
            "单字",
            "两个字",
            "这是另一个测试文本，长度适中。"
        ]
        
        # 添加说明
        explanation = QLabel("预期效果：相同行数的文本应该有相同的高度，与文字数量无关")
        explanation.setFont(QFont("PingFang SC", 12))
        explanation.setStyleSheet("color: #666; margin: 10px 0;")
        layout.addWidget(explanation)
        
        # 创建测试组件
        for i, text in enumerate(test_texts):
            # 添加分组标签
            label = QLabel(f"测试 {i+1}: {len(text)} 个字符")
            label.setFont(QFont("PingFang SC", 10))
            label.setStyleSheet("color: #999; margin-top: 10px;")
            layout.addWidget(label)
            
            # 创建历史记录项组件
            item_widget = HistoryItemWidget(text)
            item_widget.setFixedWidth(550)  # 固定宽度以便观察换行效果
            layout.addWidget(item_widget)
            
            # 显示计算出的高度
            height_info = QLabel(f"计算高度: {item_widget.sizeHint().height()}px")
            height_info.setFont(QFont("Monaco", 9))
            height_info.setStyleSheet("color: #333; margin-bottom: 5px;")
            layout.addWidget(height_info)
        
        layout.addStretch()
        
        # 添加结果说明
        result_label = QLabel("观察结果：\n" +
                            "✓ 单行文本（无论长短）应该有相同高度\n" +
                            "✓ 多行文本的高度应该根据行数成比例增加\n" +
                            "✓ 文字数量不应该影响单行文本的高度")
        result_label.setFont(QFont("PingFang SC", 11))
        result_label.setStyleSheet("color: #333; background: #f0f0f0; padding: 10px; border-radius: 5px;")
        layout.addWidget(result_label)

def main():
    """启动测试窗口"""
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    test_window = LineHeightTestWindow()
    test_window.show()
    
    return app, test_window

if __name__ == '__main__':
    app, window = main()
    sys.exit(app.exec())