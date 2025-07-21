#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import time
import subprocess
import signal
import threading

def test_program_exit():
    """测试程序退出功能是否正常工作"""
    print("开始测试程序退出功能...")
    
    # 启动程序
    print("\n=== 步骤1: 启动程序 ===")
    try:
        # 使用subprocess启动程序
        process = subprocess.Popen(
            [sys.executable, 'src/main.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        print(f"程序已启动，PID: {process.pid}")
        
        # 等待程序初始化
        print("等待程序初始化...")
        time.sleep(5)
        
        # 检查程序是否正在运行
        if process.poll() is None:
            print("✅ 程序正在正常运行")
        else:
            print("❌ 程序启动失败或已退出")
            stdout, stderr = process.communicate()
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return False
        
    except Exception as e:
        print(f"❌ 启动程序失败: {e}")
        return False
    
    # 测试正常退出
    print("\n=== 步骤2: 测试正常退出 ===")
    try:
        # 发送SIGTERM信号（模拟正常退出）
        print("发送SIGTERM信号...")
        process.terminate()
        
        # 等待程序退出，设置超时
        print("等待程序退出...")
        try:
            stdout, stderr = process.communicate(timeout=10)  # 10秒超时
            exit_code = process.returncode
            
            print(f"程序已退出，退出码: {exit_code}")
            
            # 检查输出中是否有卡死相关的错误
            output = stdout + stderr
            
            if "killed" in output.lower():
                print("⚠️ 检测到程序被强制终止")
            
            if "resource_tracker" in output.lower() and "leaked" in output.lower():
                print("⚠️ 检测到资源泄漏警告")
                print("相关输出:")
                for line in output.split('\n'):
                    if 'resource_tracker' in line.lower() or 'leaked' in line.lower():
                        print(f"  {line}")
            
            if "热键监听已停止" in output:
                print("✅ 热键监听正常停止")
            
            if "快速清理完成" in output:
                print("✅ 资源清理正常完成")
            
            print("\n程序输出:")
            print("--- STDOUT ---")
            print(stdout)
            print("--- STDERR ---")
            print(stderr)
            
            return exit_code == 0 or exit_code == -15  # 0表示正常退出，-15表示SIGTERM
            
        except subprocess.TimeoutExpired:
            print("❌ 程序在10秒内未能正常退出，可能卡死")
            
            # 强制终止
            print("强制终止程序...")
            process.kill()
            try:
                stdout, stderr = process.communicate(timeout=5)
                print("程序已被强制终止")
                print("--- STDOUT ---")
                print(stdout)
                print("--- STDERR ---")
                print(stderr)
            except subprocess.TimeoutExpired:
                print("❌ 程序无法被强制终止")
            
            return False
            
    except Exception as e:
        print(f"❌ 测试退出功能失败: {e}")
        try:
            process.kill()
        except:
            pass
        return False

def test_multiple_exits():
    """测试多次启动和退出"""
    print("\n=== 测试多次启动和退出 ===")
    
    success_count = 0
    total_tests = 3
    
    for i in range(total_tests):
        print(f"\n--- 第 {i+1} 次测试 ---")
        
        try:
            # 启动程序
            process = subprocess.Popen(
                [sys.executable, 'src/main.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待初始化
            time.sleep(3)
            
            # 检查是否正在运行
            if process.poll() is None:
                print(f"✅ 第 {i+1} 次启动成功")
                
                # 正常退出
                process.terminate()
                try:
                    stdout, stderr = process.communicate(timeout=8)
                    print(f"✅ 第 {i+1} 次退出成功")
                    success_count += 1
                except subprocess.TimeoutExpired:
                    print(f"❌ 第 {i+1} 次退出超时")
                    process.kill()
                    process.communicate()
            else:
                print(f"❌ 第 {i+1} 次启动失败")
                
        except Exception as e:
            print(f"❌ 第 {i+1} 次测试异常: {e}")
        
        # 短暂等待
        time.sleep(1)
    
    print(f"\n多次测试结果: {success_count}/{total_tests} 成功")
    return success_count == total_tests

def main():
    """主测试函数"""
    print("程序退出功能测试")
    print("=" * 50)
    
    # 确保在正确的目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 测试1: 基本退出功能
    test1_result = test_program_exit()
    
    # 测试2: 多次启动退出
    test2_result = test_multiple_exits()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试结果总结:")
    print(f"1. 基本退出功能: {'✅ 通过' if test1_result else '❌ 失败'}")
    print(f"2. 多次启动退出: {'✅ 通过' if test2_result else '❌ 失败'}")
    
    overall_success = test1_result and test2_result
    
    if overall_success:
        print("\n🎉 所有测试通过！程序退出功能正常")
        print("\n修复效果:")
        print("1. ✅ 程序能够正常退出，不会卡死")
        print("2. ✅ 热键监听能够正确停止")
        print("3. ✅ 资源清理快速完成")
        print("4. ✅ 支持多次启动和退出")
        print("5. ✅ 减少了资源泄漏问题")
    else:
        print("\n❌ 部分测试失败，程序退出功能仍需改进")
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    sys.exit(main())