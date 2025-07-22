#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dock菜单功能测试脚本
测试dock图标右键菜单中的"显示窗口"功能
"""

import sys
import os
import time
import subprocess
from pathlib import Path

def test_dock_menu_functionality():
    """测试dock菜单功能"""
    print("🧪 Dock菜单功能测试")
    print("=" * 50)
    
    print("\n📋 测试说明:")
    print("1. 应用程序将启动并显示在dock中")
    print("2. 请右键点击dock图标查看菜单")
    print("3. 菜单中应包含'显示窗口'选项")
    print("4. 点击'显示窗口'应能打开主窗口")
    print("5. 按Ctrl+C停止测试")
    
    # 启动应用程序
    print("\n步骤1: 启动应用程序")
    try:
        process = subprocess.Popen(
            [sys.executable, "src/main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        print(f"✓ 应用程序已启动，PID: {process.pid}")
        
        # 等待应用程序完全启动
        print("\n步骤2: 等待应用程序初始化...")
        time.sleep(3)
        
        # 检查应用程序是否正常运行
        if process.poll() is None:
            print("✓ 应用程序正在运行")
            print("\n🎯 请手动测试dock菜单功能:")
            print("   1. 在dock中找到应用程序图标")
            print("   2. 右键点击图标")
            print("   3. 查看是否显示包含'显示窗口'的菜单")
            print("   4. 点击'显示窗口'测试功能")
            print("\n⏳ 测试进行中... (按Ctrl+C结束)")
            
            # 保持运行状态，让用户手动测试
            try:
                while process.poll() is None:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n\n🛑 用户中断测试")
                
        else:
            print("❌ 应用程序启动失败")
            return False
            
    except Exception as e:
        print(f"❌ 启动应用程序时出错: {e}")
        return False
        
    finally:
        # 清理进程
        try:
            if 'process' in locals() and process.poll() is None:
                print("\n🧹 正在清理进程...")
                process.terminate()
                time.sleep(2)
                if process.poll() is None:
                    process.kill()
                print("✓ 进程已清理")
        except Exception as e:
            print(f"⚠️ 清理进程时出错: {e}")
    
    print("\n✅ 测试完成")
    print("\n📝 预期结果:")
    print("   - dock图标应显示应用程序")
    print("   - 右键dock图标应显示菜单")
    print("   - 菜单应包含'显示窗口'选项")
    print("   - 点击'显示窗口'应打开主窗口")
    
    return True

if __name__ == "__main__":
    # 添加src目录到Python路径
    src_path = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_path))
    
    try:
        test_dock_menu_functionality()
    except KeyboardInterrupt:
        print("\n\n🛑 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        sys.exit(1)