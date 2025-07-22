#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dock图标点击功能测试脚本
测试修复后的dock图标点击是否能正常显示主窗口
"""

import sys
import os
import time
import subprocess
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_dock_click_functionality():
    """测试dock图标点击功能"""
    print("\n=== Dock图标点击功能测试 ===")
    
    try:
        # 1. 启动应用程序
        print("\n步骤1: 启动应用程序")
        app_process = subprocess.Popen(
            [sys.executable, "src/main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        print("✓ 应用程序已启动，PID:", app_process.pid)
        
        # 等待应用程序完全启动
        print("等待应用程序完全启动...")
        time.sleep(3)
        
        # 2. 检查应用程序是否正在运行
        if app_process.poll() is None:
            print("✓ 应用程序正在运行")
        else:
            print("❌ 应用程序启动失败")
            stdout, stderr = app_process.communicate()
            print(f"标准输出: {stdout}")
            print(f"错误输出: {stderr}")
            return False
        
        # 3. 模拟dock图标点击
        print("\n步骤2: 模拟dock图标点击")
        print("请手动点击dock中的应用程序图标来测试功能")
        print("观察是否有以下日志输出:")
        print("  🔍 检测到 Dock 图标点击事件，准备显示窗口")
        print("  ✓ 窗口已显示")
        
        # 4. 监控应用程序输出
        print("\n步骤3: 监控应用程序输出（30秒）")
        print("请在30秒内点击dock图标进行测试...")
        
        start_time = time.time()
        dock_click_detected = False
        window_shown = False
        
        while time.time() - start_time < 30:
            # 检查进程是否还在运行
            if app_process.poll() is not None:
                print("❌ 应用程序意外退出")
                break
            
            # 读取输出（非阻塞）
            try:
                # 使用select来非阻塞读取（仅在Unix系统上可用）
                import select
                if select.select([app_process.stdout], [], [], 0.1)[0]:
                    line = app_process.stdout.readline()
                    if line:
                        print(f"[应用输出] {line.strip()}")
                        if "检测到 Dock 图标点击事件" in line:
                            dock_click_detected = True
                            print("✓ 检测到dock图标点击事件！")
                        elif "窗口已显示" in line:
                            window_shown = True
                            print("✓ 窗口显示成功！")
            except ImportError:
                # Windows系统或其他不支持select的系统
                time.sleep(0.1)
            except:
                time.sleep(0.1)
        
        # 5. 测试结果
        print("\n=== 测试结果 ===")
        if dock_click_detected and window_shown:
            print("✅ Dock图标点击功能正常工作")
            result = True
        elif dock_click_detected:
            print("⚠️  检测到dock点击事件，但窗口显示可能有问题")
            result = False
        else:
            print("❌ 未检测到dock图标点击事件")
            print("可能的原因:")
            print("  1. 事件处理器未正确设置")
            print("  2. 事件类型检测有误")
            print("  3. macOS权限问题")
            result = False
        
        # 6. 清理
        print("\n步骤4: 清理进程")
        try:
            app_process.terminate()
            app_process.wait(timeout=5)
            print("✓ 应用程序已正常退出")
        except subprocess.TimeoutExpired:
            app_process.kill()
            print("⚠️  强制终止应用程序")
        
        return result
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def check_macos_permissions():
    """检查macOS相关权限"""
    print("\n=== macOS权限检查 ===")
    
    if sys.platform != 'darwin':
        print("⚠️  当前不是macOS系统，跳过权限检查")
        return True
    
    try:
        # 检查辅助功能权限
        result = subprocess.run([
            'osascript', '-e',
            'tell application "System Events" to return UI elements enabled'
        ], capture_output=True, text=True)
        
        if result.returncode == 0 and 'true' in result.stdout.lower():
            print("✓ 辅助功能权限已授权")
        else:
            print("❌ 辅助功能权限未授权")
            print("请在 系统偏好设置 > 安全性与隐私 > 隐私 > 辅助功能 中授权")
            return False
        
        # 检查自动化权限
        result = subprocess.run([
            'osascript', '-e',
            'tell application "System Events" to return "test"'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ 自动化权限已授权")
        else:
            print("❌ 自动化权限未授权")
            print("请在 系统偏好设置 > 安全性与隐私 > 隐私 > 自动化 中授权")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 权限检查失败: {e}")
        return False

def main():
    """主函数"""
    print("Dock图标点击功能测试工具")
    print("=" * 50)
    
    # 检查权限
    if not check_macos_permissions():
        print("\n❌ 权限检查失败，请先解决权限问题")
        return
    
    # 测试dock点击功能
    success = test_dock_click_functionality()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 测试完成：Dock图标点击功能正常")
    else:
        print("❌ 测试完成：Dock图标点击功能存在问题")
        print("\n建议检查:")
        print("1. handle_mac_events方法是否正确设置")
        print("2. 事件类型121是否正确")
        print("3. _show_window_internal方法是否正常工作")
        print("4. macOS系统权限是否完整")

if __name__ == "__main__":
    main()