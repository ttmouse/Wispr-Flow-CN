#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试加载期间拖拽禁用功能
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget, QLabel, QPushButton
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

# 导入项目模块
try:
    from ui.main_window import MainWindow
    from settings_manager import SettingsManager
except ImportError:
    # 备用导入路径
    from src.ui.main_window import MainWindow
    from src.settings_manager import SettingsManager

def global_exception_handler(exc_type, exc_value, exc_traceback):
    """全局异常处理器"""
    import traceback
    print(f"\n❌ 全局异常捕获:")
    print(f"异常类型: {exc_type.__name__}")
    print(f"异常信息: {exc_value}")
    print(f"异常堆栈:")
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    print("\n" + "="*50)

class TestLoadingWindow(QWidget):
    """测试加载期间拖拽的窗口"""
    
    def __init__(self):
        super().__init__()
        self.settings_manager = SettingsManager()
        self.main_window = None
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("测试加载期间拖拽禁用")
        self.setGeometry(100, 100, 400, 300)
        
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel("加载期间拖拽测试")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # 说明
        info = QLabel(
            "点击下面的按钮启动主窗口\n"
            "在主窗口加载过程中尝试拖拽标题栏\n"
            "应该看到禁用拖拽的警告信息\n"
            "等加载完成后拖拽应该正常工作"
        )
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("color: #666; margin: 20px;")
        layout.addWidget(info)
        
        # 启动按钮
        start_btn = QPushButton("启动主窗口测试")
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        start_btn.clicked.connect(self.start_main_window_test)
        layout.addWidget(start_btn)
        
        # 状态标签
        self.status_label = QLabel("准备就绪")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #333; margin: 10px;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
    def start_main_window_test(self):
        """启动主窗口测试"""
        try:
            self.status_label.setText("正在启动主窗口...")
            print("\n🚀 开始启动主窗口测试")
            print("📝 测试说明:")
            print("   1. 主窗口启动后，立即尝试拖拽标题栏")
            print("   2. 在加载期间应该看到拖拽禁用的警告")
            print("   3. 等待加载完成后再次尝试拖拽")
            print("   4. 加载完成后拖拽应该正常工作")
            print("\n" + "="*50)
            
            # 创建主窗口
            self.main_window = MainWindow(self.settings_manager)
            
            # 显示主窗口
            self.main_window.show()
            
            self.status_label.setText("主窗口已启动，请测试拖拽功能")
            print("✓ 主窗口已启动，请在加载期间尝试拖拽标题栏")
            
        except Exception as e:
            error_msg = f"启动主窗口失败: {e}"
            self.status_label.setText(error_msg)
            print(f"❌ {error_msg}")
            import traceback
            print(traceback.format_exc())

def main():
    """主函数"""
    # 设置全局异常处理
    sys.excepthook = global_exception_handler
    
    print("🧪 启动加载期间拖拽禁用测试")
    print("📋 测试目标: 验证界面加载期间拖拽事件被正确禁用")
    print("\n" + "="*50)
    
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    test_window = TestLoadingWindow()
    test_window.show()
    
    print("✓ 测试窗口已启动")
    print("💡 请点击按钮启动主窗口测试")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()