#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试拖拽修复功能
验证事件过滤器是否能正确阻止初始化期间的标题栏交互
"""

import sys
import os
import time
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from ui.main_window import MainWindow
    from settings_manager import SettingsManager
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在项目根目录运行此脚本")
    sys.exit(1)

class TestWindow(QWidget):
    """测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.main_window = None
        self.setup_ui()
        
    def setup_ui(self):
        """设置测试界面"""
        self.setWindowTitle("拖拽修复测试")
        self.setGeometry(100, 100, 400, 300)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # 标题
        title = QLabel("拖拽功能修复测试")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # 说明文字
        info = QLabel(
            "此测试验证事件过滤器是否能正确阻止\n"
            "初始化期间的标题栏拖拽操作。\n\n"
            "测试步骤：\n"
            "1. 点击下方按钮启动主窗口\n"
            "2. 在加载过程中尝试拖拽标题栏\n"
            "3. 观察是否显示禁用提示\n"
            "4. 等待加载完成后再次尝试拖拽\n"
            "5. 确认拖拽功能正常工作"
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #666; line-height: 1.4;")
        layout.addWidget(info)
        
        # 启动按钮
        self.start_button = QPushButton("启动主窗口测试")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056CC;
            }
            QPushButton:pressed {
                background-color: #004499;
            }
        """)
        self.start_button.clicked.connect(self.start_test)
        layout.addWidget(self.start_button)
        
        # 状态标签
        self.status_label = QLabel("点击按钮开始测试")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #999; font-style: italic;")
        layout.addWidget(self.status_label)
        
    def start_test(self):
        """开始测试"""
        try:
            self.start_button.setEnabled(False)
            self.status_label.setText("正在启动主窗口...")
            
            # 创建设置管理器（简化版）
            settings_manager = SettingsManager()
            
            # 创建主窗口
            self.main_window = MainWindow()
            
            # 手动设置初始化状态为False来模拟加载过程
            self.main_window._initialization_complete = False
            
            # 显示主窗口
            self.main_window.show()
            
            self.status_label.setText("主窗口已启动，请尝试拖拽标题栏")
            
            # 模拟初始化过程，3秒后完成初始化
            QTimer.singleShot(3000, self.complete_initialization)
            
            print("\n🧪 测试开始")
            print("📋 请按照以下步骤进行测试：")
            print("   1. 现在尝试拖拽主窗口的标题栏（应该被阻止）")
            print("   2. 观察控制台是否显示禁用提示")
            print("   3. 等待3秒后再次尝试拖拽（应该正常工作）")
            print("   4. 确认拖拽功能恢复正常")
            
        except Exception as e:
            print(f"❌ 测试启动失败: {e}")
            import traceback
            traceback.print_exc()
            self.start_button.setEnabled(True)
            self.status_label.setText("测试启动失败")
    
    def complete_initialization(self):
        """完成初始化"""
        if self.main_window:
            self.main_window._initialization_complete = True
            self.status_label.setText("初始化完成，现在可以正常拖拽了")
            print("\n✅ 初始化完成！")
            print("📋 现在请再次尝试拖拽标题栏，应该可以正常工作")

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序属性
    app.setApplicationName("拖拽修复测试")
    app.setApplicationVersion("1.0")
    
    # 创建测试窗口
    test_window = TestWindow()
    test_window.show()
    
    print("🚀 拖拽修复测试程序已启动")
    print("📝 此测试验证事件过滤器是否能正确处理初始化期间的事件")
    
    # 运行应用程序
    sys.exit(app.exec())

if __name__ == "__main__":
    main()