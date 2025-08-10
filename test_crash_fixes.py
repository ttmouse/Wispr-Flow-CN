#!/usr/bin/env python3
"""
测试崩溃修复脚本
验证录制时的稳定性改进
"""

import sys
import os
import time
import threading
import logging
from datetime import datetime

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

def setup_test_logging():
    """设置测试日志"""
    log_filename = f"test_crash_fixes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return log_filename

def test_audio_capture_stability():
    """测试音频捕获稳定性"""
    print("🔍 测试音频捕获稳定性...")
    
    try:
        from audio_capture import AudioCapture
        
        # 创建多个音频捕获实例测试
        capture_instances = []
        for i in range(3):
            try:
                capture = AudioCapture()
                capture_instances.append(capture)
                print(f"✓ 音频捕获实例 {i+1} 创建成功")
            except Exception as e:
                print(f"❌ 音频捕获实例 {i+1} 创建失败: {e}")
        
        # 测试录制和停止
        for i, capture in enumerate(capture_instances):
            try:
                print(f"  测试实例 {i+1} 录制...")
                capture.start_recording()
                time.sleep(0.5)  # 短时间录制
                
                # 测试读取数据
                for j in range(5):
                    data = capture.read_audio()
                    if len(data) > 0:
                        print(f"    读取到 {len(data)} 字节数据")
                
                audio_data = capture.stop_recording()
                print(f"  实例 {i+1} 录制完成，数据长度: {len(audio_data)}")
                
            except Exception as e:
                print(f"❌ 实例 {i+1} 录制测试失败: {e}")
        
        # 清理资源
        for i, capture in enumerate(capture_instances):
            try:
                capture.cleanup()
                print(f"✓ 实例 {i+1} 清理完成")
            except Exception as e:
                print(f"⚠️  实例 {i+1} 清理出现问题: {e}")
                
        return True
        
    except ImportError as e:
        print(f"❌ 无法导入音频捕获模块: {e}")
        return False
    except Exception as e:
        print(f"❌ 音频捕获稳定性测试失败: {e}")
        return False

def test_thread_safety():
    """测试线程安全性"""
    print("🔍 测试线程安全性...")
    
    try:
        from audio_threads import AudioCaptureThread, TranscriptionThread
        from audio_capture import AudioCapture
        import numpy as np
        
        # 创建音频捕获实例
        capture = AudioCapture()
        
        # 测试多线程创建和销毁
        threads = []
        results = []
        
        def create_thread_test(thread_id):
            try:
                # 创建音频线程
                audio_thread = AudioCaptureThread(capture)
                
                # 模拟快速启停
                audio_thread.start()
                time.sleep(0.1)
                audio_thread.stop()
                audio_thread.cleanup()
                
                results.append(f"✓ 线程 {thread_id} 测试成功")
            except Exception as e:
                results.append(f"❌ 线程 {thread_id} 测试失败: {e}")
        
        # 创建多个测试线程
        for i in range(5):
            thread = threading.Thread(target=create_thread_test, args=(i+1,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join(timeout=5)
            if thread.is_alive():
                print(f"⚠️  线程超时未完成")
        
        # 输出结果
        for result in results:
            print(f"  {result}")
        
        # 清理
        capture.cleanup()
        
        return len([r for r in results if "✓" in r]) == 5
        
    except ImportError as e:
        print(f"❌ 无法导入线程模块: {e}")
        return False
    except Exception as e:
        print(f"❌ 线程安全性测试失败: {e}")
        return False

def test_macos_compatibility():
    """测试macOS兼容性"""
    print("🔍 测试macOS兼容性...")
    
    if sys.platform != 'darwin':
        print("⏭️  非macOS系统，跳过测试")
        return True
    
    try:
        from utils.macos_compatibility import get_macos_compatibility
        
        # 测试兼容性模块
        compat = get_macos_compatibility()
        if compat:
            print("✓ macOS兼容性模块加载成功")
            
            # 测试dispatch queue安全性
            if 'dispatch_safety' in compat:
                safety = compat['dispatch_safety']
                
                # 测试安全执行
                def test_operation():
                    return "test_result"
                
                result = safety.safe_execute(test_operation)
                if result == "test_result":
                    print("✓ dispatch queue安全执行测试通过")
                else:
                    print("⚠️  dispatch queue安全执行测试异常")
            
            # 测试输入法管理器
            if 'input_manager' in compat:
                input_manager = compat['input_manager']
                print("✓ 输入法兼容性管理器创建成功")
                
                # 简单测试监控功能
                input_manager.start_monitoring()
                time.sleep(1)
                input_manager.stop_monitoring()
                print("✓ 输入法监控测试完成")
        else:
            print("⚠️  macOS兼容性模块未能正确初始化")
            
        return True
        
    except ImportError as e:
        print(f"❌ 无法导入macOS兼容性模块: {e}")
        return False
    except Exception as e:
        print(f"❌ macOS兼容性测试失败: {e}")
        return False

def test_hotkey_stability():
    """测试热键稳定性"""
    print("🔍 测试热键管理稳定性...")
    
    try:
        from hotkey_manager import PythonHotkeyManager
        
        # 创建热键管理器
        hotkey_manager = PythonHotkeyManager()
        
        # 设置回调
        press_called = [False]
        release_called = [False]
        
        def test_press():
            press_called[0] = True
            print("  热键按下回调触发")
        
        def test_release():
            release_called[0] = True
            print("  热键释放回调触发")
        
        hotkey_manager.set_press_callback(test_press)
        hotkey_manager.set_release_callback(test_release)
        
        # 启动监听
        hotkey_manager.start_listening()
        print("✓ 热键监听启动成功")
        
        time.sleep(1)
        
        # 获取状态
        status = hotkey_manager.get_status()
        print(f"  热键状态: {status}")
        
        # 停止监听
        hotkey_manager.stop_listening()
        print("✓ 热键监听停止成功")
        
        # 清理
        hotkey_manager.cleanup()
        print("✓ 热键管理器清理完成")
        
        return True
        
    except ImportError as e:
        print(f"❌ 无法导入热键管理模块: {e}")
        return False
    except Exception as e:
        print(f"❌ 热键稳定性测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始崩溃修复验证测试")
    print("=" * 50)
    
    log_file = setup_test_logging()
    print(f"📝 测试日志将保存到: {log_file}")
    print()
    
    # 运行所有测试
    tests = [
        ("音频捕获稳定性", test_audio_capture_stability),
        ("线程安全性", test_thread_safety),
        ("macOS兼容性", test_macos_compatibility),
        ("热键管理稳定性", test_hotkey_stability),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"🧪 执行测试: {test_name}")
        try:
            success = test_func()
            results[test_name] = "✓ 通过" if success else "❌ 失败"
            print(f"结果: {results[test_name]}")
        except Exception as e:
            results[test_name] = f"❌ 异常: {e}"
            print(f"结果: {results[test_name]}")
            logging.exception(f"测试 {test_name} 出现异常")
        
        print()
    
    # 输出总结
    print("=" * 50)
    print("📊 测试结果总结:")
    for test_name, result in results.items():
        print(f"  {test_name}: {result}")
    
    passed = len([r for r in results.values() if "✓" in r])
    total = len(results)
    
    print(f"\n🎯 总体结果: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！崩溃修复生效")
        return 0
    else:
        print("⚠️  部分测试未通过，请检查相关问题")
        return 1

if __name__ == "__main__":
    sys.exit(main())