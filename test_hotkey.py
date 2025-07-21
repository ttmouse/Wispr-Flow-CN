#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热键功能测试脚本
用于诊断热键无响应问题
"""

import sys
import os
import time
from pynput import keyboard
from pynput.keyboard import Key, Listener

def test_basic_keyboard_access():
    """测试基本键盘访问权限"""
    print("\n=== 基本键盘访问测试 ===")
    try:
        def on_press(key):
            print(f"✓ 检测到按键: {key}")
            return False  # 停止监听
        
        print("请按任意键测试键盘监听...")
        with Listener(on_press=on_press) as listener:
            listener.join(timeout=5)
        
        if listener.running:
            print("⚠️  5秒内未检测到按键")
        else:
            print("✓ 键盘监听功能正常")
            
    except Exception as e:
        print(f"❌ 键盘监听失败: {e}")
        return False
    return True

def test_ctrl_key_detection():
    """测试Ctrl键检测"""
    print("\n=== Ctrl键检测测试 ===")
    ctrl_pressed = False
    
    def on_press(key):
        nonlocal ctrl_pressed
        if key == Key.ctrl_l or key == Key.ctrl_r:
            print("✓ 检测到Ctrl键按下")
            ctrl_pressed = True
            return False
    
    def on_release(key):
        if key == Key.esc:
            return False
    
    try:
        print("请按下Ctrl键测试（5秒超时，按ESC退出）...")
        with Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join(timeout=5)
        
        if ctrl_pressed:
            print("✓ Ctrl键检测正常")
            return True
        else:
            print("⚠️  未检测到Ctrl键")
            return False
            
    except Exception as e:
        print(f"❌ Ctrl键检测失败: {e}")
        return False

def test_permission_status():
    """检查权限状态"""
    print("\n=== 权限状态检查 ===")
    
    # 检查是否在虚拟环境中
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✓ 运行在虚拟环境中")
    else:
        print("⚠️  未在虚拟环境中运行")
    
    # 检查Python路径
    print(f"Python路径: {sys.executable}")
    
    # 检查当前用户
    import getpass
    print(f"当前用户: {getpass.getuser()}")
    
    # 尝试检查辅助功能权限（间接方式）
    try:
        # 尝试创建键盘监听器
        listener = Listener(on_press=lambda key: None)
        listener.start()
        time.sleep(0.1)
        listener.stop()
        print("✓ 键盘监听器创建成功（可能有辅助功能权限）")
    except Exception as e:
        print(f"❌ 键盘监听器创建失败: {e}")
        print("   这通常表示缺少辅助功能权限")

def test_hotkey_simulation():
    """模拟热键组合测试"""
    print("\n=== 热键组合测试 ===")
    
    keys_pressed = set()
    hotkey_detected = False
    
    def on_press(key):
        nonlocal hotkey_detected
        keys_pressed.add(key)
        
        # 检查Ctrl组合键
        ctrl_keys = {Key.ctrl_l, Key.ctrl_r}
        if any(ctrl in keys_pressed for ctrl in ctrl_keys):
            print(f"✓ 检测到Ctrl组合键: {keys_pressed}")
            if len(keys_pressed) > 1:  # Ctrl + 其他键
                hotkey_detected = True
                return False
    
    def on_release(key):
        if key in keys_pressed:
            keys_pressed.remove(key)
        if key == Key.esc:
            return False
    
    try:
        print("请按下Ctrl+任意键测试热键组合（10秒超时，按ESC退出）...")
        with Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join(timeout=10)
        
        if hotkey_detected:
            print("✓ 热键组合检测正常")
            return True
        else:
            print("⚠️  未检测到热键组合")
            return False
            
    except Exception as e:
        print(f"❌ 热键组合测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🔍 热键功能诊断测试")
    print("=" * 50)
    
    # 运行所有测试
    tests = [
        ("权限状态检查", test_permission_status),
        ("基本键盘访问", test_basic_keyboard_access),
        ("Ctrl键检测", test_ctrl_key_detection),
        ("热键组合测试", test_hotkey_simulation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except KeyboardInterrupt:
            print("\n用户中断测试")
            break
        except Exception as e:
            print(f"❌ {test_name}执行失败: {e}")
            results.append((test_name, False))
    
    # 输出测试结果总结
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    for test_name, result in results:
        status = "✓ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    # 给出建议
    failed_tests = [name for name, result in results if not result]
    if failed_tests:
        print("\n🔧 建议解决方案:")
        if "基本键盘访问" in failed_tests:
            print("  1. 检查辅助功能权限设置")
            print("  2. 重启终端应用")
            print("  3. 重新授权Python的辅助功能权限")
        if "Ctrl键检测" in failed_tests:
            print("  4. 检查系统快捷键冲突")
            print("  5. 尝试使用不同的热键组合")
        if "热键组合测试" in failed_tests:
            print("  6. 检查第三方快捷键工具冲突")
            print("  7. 重启系统后重试")
    else:
        print("\n✅ 所有测试通过！热键功能应该正常工作。")
        print("   如果应用中仍无响应，请检查应用内部逻辑。")

if __name__ == "__main__":
    main()