#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪贴板监控窗口测试脚本

此脚本用于测试剪贴板监控窗口的功能：
1. 测试窗口创建和显示
2. 测试剪贴板内容监控
3. 测试历史记录功能
"""

import sys
import os
import time
import subprocess
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ui.clipboard_monitor_window import ClipboardMonitorWindow
from clipboard_manager import ClipboardManager

def test_clipboard_monitor():
    """测试剪贴板监控窗口"""
    print("🧪 开始测试剪贴板监控窗口...")
    
    # 创建Qt应用程序
    app = QApplication(sys.argv)
    
    try:
        # 初始化剪贴板管理器
        print("📋 初始化剪贴板管理器...")
        clipboard_manager = ClipboardManager(debug_mode=True)
        
        # 创建剪贴板监控窗口
        print("🪟 创建剪贴板监控窗口...")
        monitor_window = ClipboardMonitorWindow(clipboard_manager=clipboard_manager)
        
        # 显示窗口
        print("👁️ 显示剪贴板监控窗口...")
        monitor_window.show()
        monitor_window.raise_()
        monitor_window.activateWindow()
        
        # 测试剪贴板内容变化
        def test_clipboard_changes():
            print("📝 测试剪贴板内容变化...")
            test_texts = [
                "测试文本 1 - Hello World!",
                "测试文本 2 - 剪贴板监控测试",
                "测试文本 3 - 这是一个长一点的测试文本，用来验证剪贴板监控窗口的显示效果",
                "测试文本 4 - Test clipboard monitoring functionality",
                "测试文本 5 - 最后一个测试文本"
            ]
            
            for i, text in enumerate(test_texts, 1):
                print(f"  📄 设置剪贴板内容 {i}: {text[:30]}...")
                clipboard_manager.copy_to_clipboard(text)
                time.sleep(2)  # 等待2秒让监控窗口更新
        
        # 延迟执行剪贴板测试
        QTimer.singleShot(2000, test_clipboard_changes)
        
        # 设置自动退出
        QTimer.singleShot(15000, app.quit)  # 15秒后自动退出
        
        print("✅ 剪贴板监控窗口测试启动成功")
        print("📌 窗口将显示15秒，期间会自动测试剪贴板内容变化")
        print("🔍 请观察窗口是否正确显示剪贴板内容和历史记录")
        
        # 运行应用程序
        return app.exec()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(traceback.format_exc())
        return 1

if __name__ == "__main__":
    exit_code = test_clipboard_monitor()
    print(f"🏁 测试完成，退出码: {exit_code}")
    sys.exit(exit_code)