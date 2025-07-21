#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪贴板监控窗口演示脚本

此脚本演示如何在主应用程序中集成和使用剪贴板监控窗口。
演示内容包括：
1. 创建剪贴板监控窗口
2. 模拟剪贴板内容变化
3. 展示窗口功能
"""

import sys
import os
import time
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtGui import QFont

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ui.clipboard_monitor_window import ClipboardMonitorWindow
from clipboard_manager import ClipboardManager

class DemoMainWindow(QMainWindow):
    """演示主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("剪贴板监控演示")
        self.setGeometry(100, 100, 400, 300)
        
        # 初始化剪贴板管理器
        self.clipboard_manager = ClipboardManager(debug_mode=True)
        self.clipboard_monitor_window = None
        
        # 设置UI
        self.setup_ui()
        
        # 演示数据
        self.demo_texts = [
            "演示文本 1: Hello, Clipboard Monitor!",
            "演示文本 2: 这是一个中文测试文本",
            "演示文本 3: Mixed content with 中英文混合内容",
            "演示文本 4: Code snippet: print('Hello World')",
            "演示文本 5: 长文本演示 - " + "这是一个很长的文本内容，用来测试剪贴板监控窗口对长文本的显示效果。" * 3,
            "演示文本 6: JSON格式\n{\n  \"name\": \"test\",\n  \"value\": 123\n}",
            "演示文本 7: 特殊字符 !@#$%^&*()_+-=[]{}|;':,.<>?",
            "演示文本 8: 最后一个演示文本"
        ]
        self.current_demo_index = 0
        
        # 自动演示定时器
        self.demo_timer = QTimer()
        self.demo_timer.timeout.connect(self.next_demo_text)
        
    def setup_ui(self):
        """设置用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("📋 剪贴板监控窗口演示")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2c3e50; margin: 10px;")
        layout.addWidget(title_label)
        
        # 说明文本
        info_label = QLabel(
            "这个演示展示了剪贴板监控窗口的功能：\n"
            "• 实时监控剪贴板内容变化\n"
            "• 显示内容更新时间和长度\n"
            "• 支持各种文本格式\n"
            "• 提供便捷的操作按钮"
        )
        info_label.setStyleSheet("color: #34495e; margin: 10px; line-height: 1.5;")
        layout.addWidget(info_label)
        
        # 按钮区域
        button_style = """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """
        
        # 打开监控窗口按钮
        self.open_button = QPushButton("🪟 打开剪贴板监控窗口")
        self.open_button.setStyleSheet(button_style)
        self.open_button.clicked.connect(self.open_clipboard_monitor)
        layout.addWidget(self.open_button)
        
        # 开始演示按钮
        self.demo_button = QPushButton("🎬 开始自动演示")
        self.demo_button.setStyleSheet(button_style.replace("#3498db", "#27ae60").replace("#2980b9", "#229954").replace("#21618c", "#1e8449"))
        self.demo_button.clicked.connect(self.start_demo)
        layout.addWidget(self.demo_button)
        
        # 停止演示按钮
        self.stop_button = QPushButton("⏹️ 停止演示")
        self.stop_button.setStyleSheet(button_style.replace("#3498db", "#e74c3c").replace("#2980b9", "#c0392b").replace("#21618c", "#a93226"))
        self.stop_button.clicked.connect(self.stop_demo)
        self.stop_button.setEnabled(False)
        layout.addWidget(self.stop_button)
        
        # 手动测试按钮
        self.manual_button = QPushButton("✋ 手动设置剪贴板内容")
        self.manual_button.setStyleSheet(button_style.replace("#3498db", "#f39c12").replace("#2980b9", "#e67e22").replace("#21618c", "#d68910"))
        self.manual_button.clicked.connect(self.manual_test)
        layout.addWidget(self.manual_button)
        
        # 状态标签
        self.status_label = QLabel("准备就绪 - 点击按钮开始演示")
        self.status_label.setStyleSheet("color: #7f8c8d; font-style: italic; margin: 10px;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
    def open_clipboard_monitor(self):
        """打开剪贴板监控窗口"""
        try:
            if self.clipboard_monitor_window is None:
                self.clipboard_monitor_window = ClipboardMonitorWindow(
                    clipboard_manager=self.clipboard_manager
                )
            
            self.clipboard_monitor_window.show()
            self.clipboard_monitor_window.raise_()
            self.clipboard_monitor_window.activateWindow()
            
            self.status_label.setText("✅ 剪贴板监控窗口已打开")
            print("✓ 剪贴板监控窗口已打开")
            
        except Exception as e:
            self.status_label.setText(f"❌ 打开窗口失败: {str(e)}")
            print(f"❌ 打开剪贴板监控窗口失败: {e}")
            import traceback
            print(traceback.format_exc())
    
    def start_demo(self):
        """开始自动演示"""
        self.current_demo_index = 0
        self.demo_timer.start(3000)  # 每3秒更新一次
        
        self.demo_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        self.status_label.setText("🎬 自动演示已开始 - 每3秒更新一次剪贴板内容")
        print("🎬 开始自动演示")
        
        # 立即设置第一个演示文本
        self.next_demo_text()
    
    def stop_demo(self):
        """停止自动演示"""
        self.demo_timer.stop()
        
        self.demo_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        self.status_label.setText("⏹️ 自动演示已停止")
        print("⏹️ 自动演示已停止")
    
    def next_demo_text(self):
        """设置下一个演示文本"""
        if self.current_demo_index < len(self.demo_texts):
            text = self.demo_texts[self.current_demo_index]
            self.clipboard_manager.copy_to_clipboard(text)
            
            self.status_label.setText(
                f"📝 演示 {self.current_demo_index + 1}/{len(self.demo_texts)}: "
                f"{text[:30]}{'...' if len(text) > 30 else ''}"
            )
            
            print(f"📝 设置演示文本 {self.current_demo_index + 1}: {text[:50]}{'...' if len(text) > 50 else ''}")
            
            self.current_demo_index += 1
        else:
            # 演示完成，自动停止
            self.stop_demo()
            self.status_label.setText("🎉 演示完成！")
            print("🎉 演示完成")
    
    def manual_test(self):
        """手动测试"""
        import datetime
        test_text = f"手动测试文本 - {datetime.datetime.now().strftime('%H:%M:%S')}"
        self.clipboard_manager.copy_to_clipboard(test_text)
        
        self.status_label.setText(f"✋ 手动设置: {test_text}")
        print(f"✋ 手动设置剪贴板内容: {test_text}")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止演示
        if self.demo_timer.isActive():
            self.demo_timer.stop()
        
        # 关闭剪贴板监控窗口
        if self.clipboard_monitor_window:
            self.clipboard_monitor_window.close()
        
        event.accept()
        print("👋 演示窗口已关闭")

def main():
    """主函数"""
    print("🚀 启动剪贴板监控演示...")
    
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("剪贴板监控演示")
    app.setApplicationDisplayName("剪贴板监控演示")
    
    try:
        # 创建演示窗口
        demo_window = DemoMainWindow()
        demo_window.show()
        
        print("✅ 演示窗口已启动")
        print("📌 使用说明:")
        print("   1. 点击 '打开剪贴板监控窗口' 按钮")
        print("   2. 点击 '开始自动演示' 查看自动演示")
        print("   3. 或点击 '手动设置剪贴板内容' 进行手动测试")
        print("   4. 观察剪贴板监控窗口的实时更新")
        
        # 运行应用程序
        return app.exec()
        
    except Exception as e:
        print(f"❌ 演示启动失败: {e}")
        import traceback
        print(traceback.format_exc())
        return 1

if __name__ == "__main__":
    exit_code = main()
    print(f"🏁 演示结束，退出码: {exit_code}")
    sys.exit(exit_code)