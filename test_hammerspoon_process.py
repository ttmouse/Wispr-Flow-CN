#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Hammerspoon进程检测功能
"""

import subprocess
import time

def test_hammerspoon_process_detection():
    """测试Hammerspoon进程检测功能"""
    print("=== Hammerspoon进程检测测试 ===")
    
    def check_hammerspoon_process():
        """检查Hammerspoon进程是否正在运行"""
        try:
            # 使用pgrep检查Hammerspoon进程
            result = subprocess.run(['pgrep', '-f', 'Hammerspoon'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except Exception as e:
            print(f"检查Hammerspoon进程失败: {e}")
            return False
    
    # 测试进程检测
    print("\n1. 检测Hammerspoon进程状态:")
    is_running = manager._check_hammerspoon_process()
    print(f"   Hammerspoon进程运行状态: {is_running}")
    
    # 获取完整状态
    print("\n2. 获取完整热键状态:")
    status = manager.get_status()
    print(f"   活跃状态: {status.get('active')}")
    print(f"   方案: {status.get('scheme')}")
    print(f"   热键类型: {status.get('hotkey_type')}")
    print(f"   Hammerspoon运行: {status.get('hammerspoon_running')}")
    print(f"   错误信息: {status.get('last_error')}")
    print(f"   是否录音: {status.get('is_recording')}")
    
    # 如果Hammerspoon正在运行，测试启动监听
    if is_running:
        print("\n3. 测试启动热键监听:")
        success = manager.start_listening()
        print(f"   启动结果: {success}")
        
        # 等待一下，再次检查状态
        time.sleep(2)
        status = manager.get_status()
        print(f"   启动后状态: {status.get('active')}")
        print(f"   错误信息: {status.get('last_error')}")
        
        # 清理
        manager.stop_listening()
        print("   已停止监听")
    else:
        print("\n3. Hammerspoon未运行，跳过监听测试")
        print("   请确保Hammerspoon应用程序已启动")
    
    print("\n=== 测试完成 ===")

if __name__ == '__main__':
    test_hammerspoon_process_detection()