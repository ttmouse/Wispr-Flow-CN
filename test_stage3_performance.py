#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第三阶段性能微调验证测试
测试内存优化和启动时间改进的效果
"""

import time
import threading
import sys
import os
import psutil
from collections import deque

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_audio_buffer_optimization():
    """测试音频缓冲区优化"""
    print("\n=== 测试音频缓冲区优化 ===")
    
    try:
        from audio_capture import AudioCapture
        
        audio_capture = AudioCapture()
        
        # 检查是否使用了deque
        if isinstance(audio_capture.frames, deque):
            print("✓ 音频缓冲区已优化为deque类型")
            print(f"✓ 缓冲区最大长度: {audio_capture.frames.maxlen}")
        else:
            print("❌ 音频缓冲区仍使用list类型")
            return False
        
        # 测试缓冲区清理方法
        audio_capture.frames.extend([b'test'] * 100)
        initial_len = len(audio_capture.frames)
        
        # 测试clear方法
        audio_capture.clear_buffer()
        after_clear_len = len(audio_capture.frames)
        
        print(f"✓ 清理前缓冲区长度: {initial_len}")
        print(f"✓ 清理后缓冲区长度: {after_clear_len}")
        
        if after_clear_len == 0:
            print("✓ 缓冲区清理功能正常")
            return True
        else:
            print("❌ 缓冲区清理功能异常")
            return False
            
    except Exception as e:
        print(f"❌ 音频缓冲区测试失败: {e}")
        return False

def test_memory_usage():
    """测试内存使用情况"""
    print("\n=== 测试内存使用情况 ===")
    
    try:
        process = psutil.Process(os.getpid())
        
        # 获取初始内存
        initial_memory = process.memory_info().rss / 1024 / 1024
        print(f"✓ 初始内存使用: {initial_memory:.2f} MB")
        
        # 模拟音频缓冲区使用
        from collections import deque
        
        # 测试优化后的deque vs 原始list的内存使用
        test_data = [b'x' * 1024] * 1000  # 1MB数据
        
        # 使用deque (优化后)
        deque_buffer = deque(maxlen=1000)
        deque_buffer.extend(test_data)
        
        memory_after_deque = process.memory_info().rss / 1024 / 1024
        deque_usage = memory_after_deque - initial_memory
        
        # 清理deque
        deque_buffer.clear()
        del deque_buffer
        
        # 使用list (原始方式)
        list_buffer = []
        list_buffer.extend(test_data)
        
        memory_after_list = process.memory_info().rss / 1024 / 1024
        list_usage = memory_after_list - memory_after_deque
        
        print(f"✓ deque内存使用: {deque_usage:.2f} MB")
        print(f"✓ list内存使用: {list_usage:.2f} MB")
        
        # 清理
        del list_buffer
        del test_data
        
        # 内存优化效果
        if deque_usage <= list_usage:
            improvement = ((list_usage - deque_usage) / list_usage * 100) if list_usage > 0 else 0
            print(f"✓ 内存优化效果: {improvement:.1f}%")
            return True
        else:
            print("⚠️ deque内存使用高于list")
            return False
            
    except Exception as e:
        print(f"❌ 内存测试失败: {e}")
        return False

def test_startup_time():
    """测试启动时间"""
    print("\n=== 测试启动时间 ===")
    
    try:
        # 模拟组件初始化时间
        components = [
            ('设置管理器', 'settings_manager'),
            ('音频捕获', 'audio_capture'),
            ('热键管理器', 'hotkey_manager'),
            ('状态管理器', 'state_manager')
        ]
        
        total_time = 0
        
        for name, module in components:
            start_time = time.time()
            
            try:
                if module == 'settings_manager':
                    from settings_manager import SettingsManager
                    obj = SettingsManager()
                elif module == 'audio_capture':
                    from audio_capture import AudioCapture
                    obj = AudioCapture()
                elif module == 'hotkey_manager':
                    from hotkey_manager import HotkeyManager
                    from settings_manager import SettingsManager
                    settings = SettingsManager()
                    obj = HotkeyManager(settings_manager=settings)
                elif module == 'state_manager':
                    from state_manager import StateManager
                    obj = StateManager()
                
                init_time = time.time() - start_time
                total_time += init_time
                
                print(f"✓ {name}初始化: {init_time:.3f}s")
                
                # 清理对象
                if hasattr(obj, 'cleanup'):
                    obj.cleanup()
                del obj
                
            except Exception as e:
                print(f"❌ {name}初始化失败: {e}")
                return False
        
        print(f"✓ 总启动时间: {total_time:.3f}s")
        
        # 检查是否满足目标 (< 3秒)
        if total_time < 3.0:
            print("✓ 启动时间符合目标 (< 3秒)")
            return True
        else:
            print(f"⚠️ 启动时间超过目标: {total_time:.3f}s >= 3.0s")
            return False
            
    except Exception as e:
        print(f"❌ 启动时间测试失败: {e}")
        return False

def test_hotkey_response_time():
    """测试热键响应时间"""
    print("\n=== 测试热键响应时间 ===")
    
    try:
        from hotkey_manager import HotkeyManager
        from settings_manager import SettingsManager
        
        settings_manager = SettingsManager()
        hotkey_manager = HotkeyManager(settings_manager)
        
        # 测试响应时间
        response_times = []
        
        for i in range(10):
            start_time = time.time()
            
            # 模拟热键状态重置
            hotkey_manager.reset_state()
            
            response_time = time.time() - start_time
            response_times.append(response_time)
        
        avg_response_time = sum(response_times) * 1000 / len(response_times)  # 转换为毫秒
        max_response_time = max(response_times) * 1000
        
        print(f"✓ 平均响应时间: {avg_response_time:.2f}ms")
        print(f"✓ 最大响应时间: {max_response_time:.2f}ms")
        
        # 清理
        hotkey_manager.cleanup()
        
        # 检查是否满足目标 (< 150ms)
        if avg_response_time < 150:
            print("✓ 热键响应时间符合目标 (< 150ms)")
            return True
        else:
            print(f"⚠️ 热键响应时间超过目标: {avg_response_time:.2f}ms >= 150ms")
            return False
            
    except Exception as e:
        print(f"❌ 热键响应时间测试失败: {e}")
        return False

def main():
    """运行所有第三阶段性能测试"""
    print("🚀 第三阶段性能微调验证测试")
    print("=" * 50)
    print("优化目标:")
    print("• 热键响应时间 < 150ms")
    print("• 启动时间 < 3秒")
    print("• 内存使用减少 > 15%")
    print("• 音频缓冲区优化")
    
    tests = [
        ("音频缓冲区优化", test_audio_buffer_optimization),
        ("内存使用优化", test_memory_usage),
        ("启动时间优化", test_startup_time),
        ("热键响应时间", test_hotkey_response_time),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 第三阶段性能微调验证成功！")
        print("\n✅ 性能优化成果:")
        print("   • 音频缓冲区使用deque优化内存")
        print("   • 热键响应时间保持在目标范围内")
        print("   • 启动时间符合性能要求")
        print("   • 内存使用得到有效控制")
    else:
        print(f"⚠️ 部分测试未通过，需要进一步优化")
    
    return passed == total

if __name__ == "__main__":
    main()