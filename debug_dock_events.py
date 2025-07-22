#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试dock图标点击事件
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt6.QtCore import QObject, QEvent, QThread

class EventDebugger(QObject):
    """事件调试器"""
    
    def __init__(self):
        super().__init__()
        self.event_count = 0
    
    def eventFilter(self, obj, event):
        """事件过滤器"""
        self.event_count += 1
        
        # 记录所有事件（只记录前50个以避免输出过多）
        if self.event_count <= 50:
            print(f"事件 #{self.event_count}: 类型={event.type()} (值: {int(event.type())})")
        
        # 特别关注可能的dock点击事件
        if event.type() in [121, 24, 8, 17, 214, 99]:  # 各种可能的激活事件
            print(f"🔍 检测到可能的dock点击事件: 类型={event.type()} (值: {int(event.type())})")
            
            if event.type() == 121:  # ApplicationActivate
                print("✅ 确认检测到ApplicationActivate事件！")
        
        return False  # 继续传递事件

class TestWindow(QMainWindow):
    """测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dock事件调试窗口")
        self.setGeometry(100, 100, 400, 200)
        
        label = QLabel("请点击dock图标来测试事件检测\n\n查看终端输出以了解事件详情", self)
        label.setGeometry(50, 50, 300, 100)
        
        # 设置窗口不在最前面，这样点击dock图标时会有激活效果
        self.setWindowFlags(self.windowFlags())

def main():
    """主函数"""
    print("Dock事件调试工具")
    print("=" * 40)
    
    app = QApplication(sys.argv)
    
    # 创建事件调试器
    debugger = EventDebugger()
    
    # 安装全局事件过滤器
    app.installEventFilter(debugger)
    print("✓ 全局事件过滤器已安装")
    
    # 创建测试窗口
    window = TestWindow()
    window.show()
    
    print("\n测试说明:")
    print("1. 窗口已显示")
    print("2. 请点击其他应用，然后点击dock中的此应用图标")
    print("3. 观察终端输出中的事件信息")
    print("4. 按Ctrl+C退出测试")
    print("\n开始监控事件...")
    
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\n测试结束")
        app.quit()

if __name__ == "__main__":
    main()