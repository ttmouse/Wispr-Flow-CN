#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIGTRAP修复验证测试脚本
测试线程安全性和锁的改进
"""

import sys
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from hotkey_manager import HotkeyManager
    from audio_threads import AudioCaptureThread
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

def test_hotkey_manager_lock():
    """测试热键管理器的锁机制"""
    print("\n🔧 测试热键管理器锁机制...")
    
    # 创建模拟的设置管理器
    class MockSettingsManager:
        def get_setting(self, key, default):
            return default
        def get_hotkey(self):
            return 'fn'
    
    settings_manager = MockSettingsManager()
    hotkey_manager = HotkeyManager(settings_manager)
    
    # 测试可重入锁
    def test_reentrant_lock():
        with hotkey_manager._state_lock:
            print("  ✓ 外层锁获取成功")
            with hotkey_manager._state_lock:  # 测试可重入性
                print("  ✓ 内层锁获取成功（可重入）")
                hotkey_manager.other_keys_pressed.add("test_key")
                return True
        return False
    
    # 并发测试
    def concurrent_access(thread_id):
        try:
            for i in range(10):
                with hotkey_manager._state_lock:
                    # 模拟状态修改
                    hotkey_manager.other_keys_pressed.add(f"key_{thread_id}_{i}")
                    time.sleep(0.001)  # 短暂持有锁
                    hotkey_manager.other_keys_pressed.discard(f"key_{thread_id}_{i}")
            return True
        except Exception as e:
            print(f"  ❌ 线程 {thread_id} 出错: {e}")
            return False
    
    # 测试可重入锁
    if test_reentrant_lock():
        print("  ✓ 可重入锁测试通过")
    else:
        print("  ❌ 可重入锁测试失败")
    
    # 测试并发访问
    print("  🔄 测试并发访问...")
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(concurrent_access, i) for i in range(5)]
        results = [f.result() for f in futures]
    
    if all(results):
        print("  ✓ 并发访问测试通过")
    else:
        print("  ❌ 并发访问测试失败")
    
    # 清理
    hotkey_manager.cleanup()
    print("  ✓ 热键管理器清理完成")

def test_thread_timeout():
    """测试线程超时机制"""
    print("\n⏱️ 测试线程超时机制...")
    
    class MockSettingsManager:
        def get_setting(self, key, default):
            return default
        def get_hotkey(self):
            return 'ctrl'  # 使用ctrl避免fn键监听
    
    settings_manager = MockSettingsManager()
    hotkey_manager = HotkeyManager(settings_manager)
    
    # 创建一些延迟线程
    def long_running_task():
        time.sleep(2)  # 模拟长时间运行的任务
    
    # 添加一些线程到管理器
    for i in range(3):
        thread = threading.Thread(target=long_running_task, daemon=True)
        thread.start()
        hotkey_manager.delayed_threads.append(thread)
    
    print(f"  📊 创建了 {len(hotkey_manager.delayed_threads)} 个测试线程")
    
    # 测试清理超时
    start_time = time.time()
    hotkey_manager.cleanup()
    cleanup_time = time.time() - start_time
    
    print(f"  ⏱️ 清理耗时: {cleanup_time:.2f}秒")
    
    if cleanup_time < 2.0:  # 应该在超时时间内完成
        print("  ✓ 线程超时机制工作正常")
    else:
        print("  ❌ 线程超时机制可能有问题")

def test_audio_thread_improvements():
    """测试音频线程改进"""
    print("\n🎵 测试音频线程改进...")
    
    # 模拟音频捕获器
    class MockAudioCapture:
        def __init__(self):
            self.data_count = 0
            
        def start_recording(self):
            print("  📹 模拟开始录音")
            
        def read_audio(self):
            if self.data_count < 5:
                self.data_count += 1
                return b'mock_audio_data_' + str(self.data_count).encode()
            return None
            
        def stop_recording(self):
            print("  🛑 模拟停止录音")
            return b'final_audio_data'
    
    mock_audio = MockAudioCapture()
    audio_thread = AudioCaptureThread(mock_audio)
    
    # 记录信号发射次数
    signal_count = 0
    def count_signals(data):
        nonlocal signal_count
        signal_count += 1
        print(f"  📡 收到音频信号 #{signal_count}, 数据长度: {len(data)}")
    
    audio_thread.audio_captured.connect(count_signals)
    
    # 启动线程
    audio_thread.start()
    
    # 等待完成
    audio_thread.wait(3000)  # 3秒超时
    
    print(f"  📊 总共发射了 {signal_count} 个信号")
    
    if signal_count <= 3:  # 应该通过批量发射减少信号数量
        print("  ✓ 音频信号批量发射工作正常")
    else:
        print("  ⚠️ 音频信号发射次数可能仍然过多")

def main():
    """主测试函数"""
    print("🚀 开始SIGTRAP修复验证测试")
    print("=" * 50)
    
    try:
        test_hotkey_manager_lock()
        test_thread_timeout()
        test_audio_thread_improvements()
        
        print("\n" + "=" * 50)
        print("✅ 所有测试完成！")
        print("\n📋 修复总结:")
        print("  • 将 threading.Lock() 改为 threading.RLock()")
        print("  • 优化了锁持有时间")
        print("  • 添加了线程超时机制")
        print("  • 改进了音频信号发射策略")
        print("  • 增强了错误处理和资源清理")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())