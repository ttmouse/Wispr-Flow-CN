#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的UI闪退测试脚本
用于快速测试UI交互是否会导致闪退
"""

import sys
import os
import traceback
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import Qt
from ui.components.modern_list_widget import ModernListWidget
from ui.components.history_item import HistoryItemWidget

def global_exception_handler(exc_type, exc_value, exc_traceback):
    """全局异常处理器，防止应用程序闪退"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print(f"❌ 未捕获的异常: {exc_type.__name__}: {exc_value}")
    print(f"详细信息: {error_msg}")
    
    # 对于UI相关的异常，尝试继续运行而不是崩溃
    if 'Qt' in str(exc_type) or 'PyQt' in str(exc_type):
        print("⚠️  检测到Qt/PyQt异常，尝试继续运行...")
        return
    
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

class TestMainWindow(QMainWindow):
    """测试主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UI闪退测试")
        self.setGeometry(100, 100, 400, 600)
        
        # 创建中央widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        
        # 添加说明标签
        info_label = QLabel("点击下方列表项测试是否会闪退")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)
        
        # 创建测试列表
        self.test_list = ModernListWidget()
        layout.addWidget(self.test_list)
        
        # 添加测试数据
        self.add_test_data()
        
        print("✓ 测试窗口创建完成")
    
    def add_test_data(self):
        """添加测试数据"""
        test_texts = [
            "这是第一条测试文本",
            "这是第二条测试文本，内容稍微长一些，用来测试换行功能",
            "第三条测试文本",
            "这是一条很长很长很长很长很长很长很长很长很长很长很长很长的测试文本，用来测试自动换行和大小计算功能",
            "最后一条测试文本"
        ]
        
        for text in test_texts:
            try:
                self.test_list.addItem(text)
                print(f"✓ 添加测试项: {text[:20]}...")
            except Exception as e:
                print(f"❌ 添加测试项失败: {e}")
                traceback.print_exc()
    
    def mousePressEvent(self, event):
        """处理鼠标点击事件"""
        try:
            print(f"窗口鼠标点击: {event.pos()}")
            super().mousePressEvent(event)
        except Exception as e:
            print(f"❌ 窗口鼠标点击处理失败: {e}")
            traceback.print_exc()

def main():
    """主函数"""
    print("开始UI闪退测试...")
    
    # 设置全局异常处理器
    sys.excepthook = global_exception_handler
    
    try:
        app = QApplication(sys.argv)
        app.setAttribute(Qt.ApplicationAttribute.AA_DontShowIconsInMenus, False)
        
        window = TestMainWindow()
        window.show()
        
        print("✓ 应用程序启动成功，请点击界面测试是否闪退")
        print("按 Ctrl+C 退出测试")
        
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ 启动测试失败: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()