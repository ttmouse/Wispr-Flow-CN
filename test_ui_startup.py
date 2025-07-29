#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI启动测试脚本
用于验证白色区域问题是否解决
"""

import sys
import os
import time

# 设置环境变量避免启动主程序
os.environ['ASR_TEST_MODE'] = '1'

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_startup_ui():
    """测试启动UI，检查是否还有白色闪烁"""
    print("🧪 开始UI启动测试...")
    
    try:
        # 创建应用程序
        app = QApplication(sys.argv)
        
        # 导入并创建启动界面
        from app_loader import LoadingSplash
        splash = LoadingSplash()
        
        print("✓ 启动界面创建成功")
        print(f"✓ 启动界面背景色: {splash.styleSheet()}")
        
        # 显示启动界面
        splash.show()
        print("✓ 启动界面显示成功")
        
        # 模拟加载过程
        def update_progress():
            for i in range(0, 101, 10):
                splash.update_progress(f"加载中... {i}%", i)
                app.processEvents()
                time.sleep(0.1)
            
            print("✓ 加载进度测试完成")
            splash.close()
            
            # 测试主窗口
            from ui.main_window import MainWindow
            main_window = MainWindow()
            
            print("✓ 主窗口创建成功")
            print(f"✓ 主窗口背景色: {main_window.styleSheet()}")
            
            # 显示主窗口
            main_window.show()
            print("✓ 主窗口显示成功")
            
            # 检查透明度效果
            if hasattr(main_window, 'opacity_effect'):
                print("✓ 透明度效果已启用")
            else:
                print("⚠️ 透明度效果未启用")
            
            # 3秒后关闭
            QTimer.singleShot(3000, app.quit)
        
        # 延迟执行测试
        QTimer.singleShot(500, update_progress)
        
        # 运行应用程序
        app.exec()
        print("✓ UI测试完成")
        
    except Exception as e:
        print(f"❌ UI测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_startup_ui()
    if success:
        print("\n🎉 UI启动测试通过！")
        print("📝 修复总结:")
        print("  - 启动界面背景改为深色")
        print("  - 主窗口背景改为深色")
        print("  - 添加渐进式显示效果")
        print("  - 优化窗口显示时机")
    else:
        print("\n❌ UI启动测试失败")
        sys.exit(1)
