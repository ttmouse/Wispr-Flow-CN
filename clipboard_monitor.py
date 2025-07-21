#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTextEdit, QLabel
)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QFont, QClipboard

class ClipboardMonitor(QWidget):
    """剪贴板监控浮层窗口"""
    
    def __init__(self):
        super().__init__()
        self.clipboard = QApplication.clipboard()
        self.last_text = ""
        self.init_ui()
        self.setup_timer()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("剪贴板监控")
        self.setGeometry(100, 100, 400, 300)
        
        # 设置窗口属性 - 始终置顶
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint
        )
        
        # 设置样式
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(30, 30, 30, 240);
                border-radius: 10px;
                border: 1px solid #555;
            }
            QLabel {
                color: #fff;
                font-weight: bold;
                padding: 5px;
                background-color: transparent;
            }
            QTextEdit {
                background-color: rgba(50, 50, 50, 200);
                color: #fff;
                border: 1px solid #666;
                border-radius: 5px;
                padding: 8px;
                font-family: 'Monaco', 'Consolas', monospace;
                font-size: 12px;
            }
        """)
        
        # 创建布局
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        title_label = QLabel("📋 剪贴板内容监控")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # 内容显示区域
        self.content_display = QTextEdit()
        self.content_display.setReadOnly(True)
        self.content_display.setPlainText("等待剪贴板内容...")
        layout.addWidget(self.content_display)
        
        # 状态标签
        self.status_label = QLabel("状态: 监控中...")
        self.status_label.setStyleSheet("color: #4CAF50; font-size: 10px;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
    def setup_timer(self):
        """设置定时器监控剪贴板"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_clipboard)
        self.timer.start(500)  # 每500ms检查一次
        
    def check_clipboard(self):
        """检查剪贴板内容变化"""
        try:
            current_text = self.clipboard.text()
            
            if current_text != self.last_text:
                self.last_text = current_text
                self.update_display(current_text)
                
        except Exception as e:
            self.status_label.setText(f"错误: {str(e)}")
            self.status_label.setStyleSheet("color: #f44336; font-size: 10px;")
            
    def update_display(self, text):
        """更新显示内容"""
        if text.strip():
            self.content_display.setPlainText(text)
            self.status_label.setText(f"更新时间: {self.get_current_time()}")
            self.status_label.setStyleSheet("color: #4CAF50; font-size: 10px;")
        else:
            self.content_display.setPlainText("剪贴板为空")
            self.status_label.setText("状态: 剪贴板为空")
            self.status_label.setStyleSheet("color: #FF9800; font-size: 10px;")
            
    def get_current_time(self):
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
        
    def mousePressEvent(self, event):
        """鼠标按下事件 - 用于拖拽窗口"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 拖拽窗口"""
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, 'drag_position'):
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
            
    def keyPressEvent(self, event):
        """键盘事件 - ESC键关闭窗口"""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        super().keyPressEvent(event)

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 创建剪贴板监控窗口
    monitor = ClipboardMonitor()
    monitor.show()
    
    print("剪贴板监控窗口已启动")
    print("- 窗口会实时显示剪贴板内容")
    print("- 可以拖拽窗口移动位置")
    print("- 按ESC键关闭窗口")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()