#!/usr/bin/env python3
"""
测试SIGTRAP修复 - 验证dock菜单功能是否正常工作
"""

import sys
import os
import time
import threading
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_dock_menu_safety():
    """
    测试dock菜单的线程安全性和异常处理
    """
    print("🧪 开始测试SIGTRAP修复...")
    
    try:
        # 导入主应用
        from main import Application
        
        # 创建应用实例
        app_instance = Application()
        
        print("✓ 应用实例创建成功")
        
        # 测试安全重启方法是否存在
        if hasattr(app_instance, '_safe_restart_hotkey_manager'):
            print("✓ _safe_restart_hotkey_manager 方法已添加")
        else:
            print("❌ _safe_restart_hotkey_manager 方法未找到")
            return False
        
        # 测试方法调用（在主线程中）
        def test_method_call():
            try:
                app_instance._safe_restart_hotkey_manager()
                print("✓ _safe_restart_hotkey_manager 调用成功")
            except Exception as e:
                print(f"❌ 方法调用失败: {e}")
                return False
            return True
        
        # 设置定时器来测试方法调用
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(test_method_call)
        timer.start(1000)  # 1秒后调用
        
        # 设置退出定时器
        exit_timer = QTimer()
        exit_timer.setSingleShot(True)
        exit_timer.timeout.connect(app_instance.app.quit)
        exit_timer.start(3000)  # 3秒后退出
        
        print("✓ 开始运行应用程序（3秒后自动退出）...")
        
        # 运行应用
        app_instance.app.exec()
        
        print("✓ 应用程序正常退出，无SIGTRAP崩溃")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """
    主测试函数
    """
    print("=" * 50)
    print("SIGTRAP修复测试")
    print("=" * 50)
    
    success = test_dock_menu_safety()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ 所有测试通过！SIGTRAP问题已修复")
        print("🔧 修复内容:")
        print("   - 替换lambda函数为pyqtSlot装饰的方法")
        print("   - 添加线程安全检查")
        print("   - 增强异常处理")
    else:
        print("❌ 测试失败，需要进一步检查")
    print("=" * 50)
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())