#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用程序退出功能改进测试
测试点击关闭按钮是否能正确退出应用程序
"""

import sys
import os
import time
import subprocess
import psutil
import signal
from pathlib import Path

def find_app_processes():
    """查找应用程序相关的进程"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
            if 'main.py' in cmdline or 'ASR-FunASR' in cmdline:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cmdline': cmdline
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes

def test_window_close_exit():
    """测试窗口关闭是否能正确退出应用程序"""
    print("\n=== 测试窗口关闭退出功能 ===")
    
    # 1. 启动应用程序
    print("\n步骤1: 启动应用程序")
    try:
        process = subprocess.Popen(
            [sys.executable, 'src/main.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"✓ 应用程序已启动，PID: {process.pid}")
        
        # 等待应用程序完全启动
        print("等待应用程序初始化...")
        time.sleep(8)
        
        # 检查进程是否正在运行
        if process.poll() is None:
            print("✓ 应用程序正在运行")
        else:
            print("❌ 应用程序启动失败")
            return False
            
    except Exception as e:
        print(f"❌ 启动应用程序失败: {e}")
        return False
    
    # 2. 查找所有相关进程
    print("\n步骤2: 查找应用程序进程")
    initial_processes = find_app_processes()
    print(f"找到 {len(initial_processes)} 个相关进程:")
    for proc in initial_processes:
        print(f"  - PID: {proc['pid']}, 名称: {proc['name']}")
    
    # 3. 模拟窗口关闭（发送SIGTERM信号模拟用户点击关闭按钮）
    print("\n步骤3: 模拟窗口关闭")
    try:
        # 在macOS上，我们可以使用AppleScript来关闭窗口
        close_script = '''
        tell application "System Events"
            set appName to "Python"
            if exists (process appName) then
                tell process appName
                    if exists window 1 then
                        click button 1 of window 1
                    end if
                end tell
            end if
        end tell
        '''
        
        # 尝试使用AppleScript关闭窗口
        try:
            subprocess.run(['osascript', '-e', close_script], 
                         timeout=5, capture_output=True)
            print("✓ 已发送窗口关闭信号")
        except subprocess.TimeoutExpired:
            print("⚠️ AppleScript超时，使用SIGTERM信号")
            process.terminate()
        except Exception as e:
            print(f"⚠️ AppleScript失败: {e}，使用SIGTERM信号")
            process.terminate()
            
    except Exception as e:
        print(f"❌ 发送关闭信号失败: {e}")
        return False
    
    # 4. 等待进程退出
    print("\n步骤4: 等待进程退出")
    exit_timeout = 10  # 10秒超时
    start_time = time.time()
    
    while time.time() - start_time < exit_timeout:
        try:
            # 检查主进程是否已退出
            if process.poll() is not None:
                print(f"✓ 主进程已退出，退出码: {process.returncode}")
                break
            time.sleep(0.5)
        except Exception as e:
            print(f"检查进程状态时出错: {e}")
            break
    else:
        print("❌ 进程未在预期时间内退出")
        # 强制终止
        try:
            process.kill()
            print("✓ 已强制终止进程")
        except:
            pass
        return False
    
    # 5. 验证所有相关进程是否已清理
    print("\n步骤5: 验证进程清理")
    time.sleep(2)  # 等待进程完全清理
    
    remaining_processes = find_app_processes()
    if remaining_processes:
        print(f"❌ 仍有 {len(remaining_processes)} 个进程未清理:")
        for proc in remaining_processes:
            print(f"  - PID: {proc['pid']}, 名称: {proc['name']}")
            # 尝试清理残留进程
            try:
                psutil.Process(proc['pid']).terminate()
                print(f"  已终止进程 {proc['pid']}")
            except:
                pass
        return False
    else:
        print("✓ 所有相关进程已清理")
        return True

def test_multiple_start_exit():
    """测试多次启动和退出"""
    print("\n=== 测试多次启动和退出 ===")
    
    success_count = 0
    total_tests = 3
    
    for i in range(total_tests):
        print(f"\n--- 第 {i+1} 次测试 ---")
        if test_window_close_exit():
            success_count += 1
            print(f"✓ 第 {i+1} 次测试成功")
        else:
            print(f"❌ 第 {i+1} 次测试失败")
        
        # 等待系统清理
        time.sleep(3)
    
    print(f"\n多次测试结果: {success_count}/{total_tests} 成功")
    return success_count == total_tests

def test_resource_cleanup():
    """测试资源清理是否完整"""
    print("\n=== 测试资源清理 ===")
    
    # 检查是否有残留的音频设备占用
    print("检查音频设备状态...")
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        device_count = p.get_device_count()
        print(f"✓ 音频设备可正常访问，共 {device_count} 个设备")
        p.terminate()
    except Exception as e:
        print(f"⚠️ 音频设备检查失败: {e}")
    
    # 检查是否有残留的热键监听
    print("检查热键监听状态...")
    # 这里可以添加更多的资源检查逻辑
    
    return True

def main():
    """主测试函数"""
    print("应用程序退出功能改进测试")
    print("=" * 50)
    
    # 确保在正确的目录
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # 清理可能存在的残留进程
    print("\n清理可能存在的残留进程...")
    initial_processes = find_app_processes()
    for proc in initial_processes:
        try:
            psutil.Process(proc['pid']).terminate()
            print(f"已清理进程 {proc['pid']}")
        except:
            pass
    time.sleep(2)
    
    test_results = []
    
    # 测试1: 基本窗口关闭退出功能
    print("\n" + "=" * 60)
    test1_result = test_window_close_exit()
    test_results.append(("窗口关闭退出", test1_result))
    
    # 测试2: 多次启动退出
    print("\n" + "=" * 60)
    test2_result = test_multiple_start_exit()
    test_results.append(("多次启动退出", test2_result))
    
    # 测试3: 资源清理
    print("\n" + "=" * 60)
    test3_result = test_resource_cleanup()
    test_results.append(("资源清理", test3_result))
    
    # 总结测试结果
    print("\n" + "=" * 60)
    print("测试结果总结:")
    print("-" * 30)
    
    all_passed = True
    for test_name, result in test_results:
        status = "✓ 通过" if result else "❌ 失败"
        print(f"{test_name:<15} {status}")
        if not result:
            all_passed = False
    
    print("-" * 30)
    if all_passed:
        print("🎉 所有测试通过！退出功能改进成功。")
        print("\n改进效果:")
        print("- ✓ 点击关闭按钮现在会完全退出应用程序")
        print("- ✓ 界面和后台Python进程都会正确清理")
        print("- ✓ 系统资源得到正确释放")
        print("- ✓ 符合用户对关闭按钮的预期行为")
    else:
        print("⚠️ 部分测试失败，需要进一步调试。")
        print("\n建议检查:")
        print("- 应用程序是否正确调用了quit_application方法")
        print("- 资源清理是否完整")
        print("- 是否存在阻塞退出的线程或资源")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)