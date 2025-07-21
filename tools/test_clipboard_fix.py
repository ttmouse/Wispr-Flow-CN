#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪贴板问题修复测试脚本

此脚本用于测试和验证剪贴板粘贴历史记录问题的修复效果。

使用方法：
1. 运行此脚本进行基本测试
2. 启用调试模式：python test_clipboard_fix.py --debug
3. 模拟问题场景：python test_clipboard_fix.py --simulate
"""

import sys
import os
import time
import argparse
import threading

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.clipboard_manager import ClipboardManager
from src.settings_manager import SettingsManager

def test_basic_clipboard_operations(debug_mode=False):
    """测试基本剪贴板操作"""
    print("\n=== 基本剪贴板操作测试 ===")
    
    clipboard = ClipboardManager(debug_mode=debug_mode)
    
    # 测试文本列表
    test_texts = [
        "这是第一段测试文本",
        "This is the second test text",
        "第三段包含特殊字符：!@#$%^&*()",
        "多行文本测试\n第二行\n第三行"
    ]
    
    print(f"测试 {len(test_texts)} 个文本片段...")
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n--- 测试 {i}/{len(test_texts)} ---")
        print(f"原始文本: {repr(text)}")
        
        # 复制到剪贴板
        success = clipboard.copy_to_clipboard(text)
        if not success:
            print(f"❌ 复制失败")
            continue
            
        # 验证剪贴板内容
        clipboard_content = clipboard.get_clipboard_content()
        if clipboard_content == text:
            print(f"✓ 复制验证成功")
        else:
            print(f"❌ 复制验证失败")
            print(f"   期望: {repr(text)}")
            print(f"   实际: {repr(clipboard_content)}")
        
        time.sleep(0.1)  # 短暂延迟
    
    print("\n=== 基本测试完成 ===")

def test_safe_copy_and_paste(debug_mode=False):
    """测试安全复制粘贴功能"""
    print("\n=== 安全复制粘贴测试 ===")
    
    clipboard = ClipboardManager(debug_mode=debug_mode)
    
    test_text = "安全粘贴测试文本 - 这应该被正确粘贴"
    print(f"测试文本: {test_text}")
    
    # 先设置一个不同的剪贴板内容
    clipboard.copy_to_clipboard("这是一个干扰文本")
    print("已设置干扰文本到剪贴板")
    
    # 使用安全粘贴方法
    print("\n执行安全复制粘贴...")
    success = clipboard.safe_copy_and_paste(test_text)
    
    if success:
        print("✓ 安全粘贴操作完成")
    else:
        print("❌ 安全粘贴操作失败")
    
    # 验证最终剪贴板内容
    final_content = clipboard.get_clipboard_content()
    print(f"最终剪贴板内容: {repr(final_content)}")
    
    print("\n=== 安全粘贴测试完成 ===")

def simulate_problem_scenario(debug_mode=False):
    """模拟问题场景：在延迟期间修改剪贴板"""
    print("\n=== 问题场景模拟测试 ===")
    
    clipboard = ClipboardManager(debug_mode=debug_mode)
    
    target_text = "这是目标文本，应该被粘贴"
    interference_text = "这是干扰文本，不应该被粘贴"
    
    print(f"目标文本: {target_text}")
    print(f"干扰文本: {interference_text}")
    
    # 复制目标文本
    clipboard.copy_to_clipboard(target_text)
    print("\n已复制目标文本到剪贴板")
    
    # 模拟延迟期间的干扰
    def interfere_clipboard():
        time.sleep(0.03)  # 30ms后干扰
        clipboard.copy_to_clipboard(interference_text)
        print("[干扰线程] 已修改剪贴板内容")
    
    # 启动干扰线程
    interference_thread = threading.Thread(target=interfere_clipboard)
    interference_thread.start()
    
    # 使用安全粘贴方法
    print("执行安全复制粘贴（应该能抵御干扰）...")
    success = clipboard.safe_copy_and_paste(target_text)
    
    # 等待干扰线程完成
    interference_thread.join()
    
    if success:
        print("✓ 安全粘贴操作完成")
    else:
        print("❌ 安全粘贴操作失败")
    
    # 验证最终剪贴板内容
    final_content = clipboard.get_clipboard_content()
    print(f"最终剪贴板内容: {repr(final_content)}")
    
    if final_content == target_text:
        print("✓ 成功抵御干扰，粘贴了正确内容")
    elif final_content == interference_text:
        print("❌ 未能抵御干扰，粘贴了错误内容")
    else:
        print("⚠️ 剪贴板内容异常")
    
    print("\n=== 问题场景模拟完成 ===")

def enable_debug_mode():
    """启用调试模式"""
    print("\n=== 启用调试模式 ===")
    
    try:
        settings_manager = SettingsManager()
        settings_manager.set_setting('clipboard_debug', True)
        print("✓ 已启用剪贴板调试模式")
        print("重新启动应用程序后，将看到详细的剪贴板操作日志")
    except Exception as e:
        print(f"❌ 启用调试模式失败: {e}")

def disable_debug_mode():
    """禁用调试模式"""
    print("\n=== 禁用调试模式 ===")
    
    try:
        settings_manager = SettingsManager()
        settings_manager.set_setting('clipboard_debug', False)
        print("✓ 已禁用剪贴板调试模式")
    except Exception as e:
        print(f"❌ 禁用调试模式失败: {e}")

def main():
    parser = argparse.ArgumentParser(description='剪贴板问题修复测试脚本')
    parser.add_argument('--debug', action='store_true', help='启用调试模式进行测试')
    parser.add_argument('--simulate', action='store_true', help='模拟问题场景')
    parser.add_argument('--enable-debug', action='store_true', help='启用应用程序调试模式')
    parser.add_argument('--disable-debug', action='store_true', help='禁用应用程序调试模式')
    
    args = parser.parse_args()
    
    print("剪贴板问题修复测试脚本")
    print("=" * 50)
    
    if args.enable_debug:
        enable_debug_mode()
        return
    
    if args.disable_debug:
        disable_debug_mode()
        return
    
    debug_mode = args.debug
    
    if debug_mode:
        print("🔍 调试模式已启用")
    
    # 运行测试
    test_basic_clipboard_operations(debug_mode)
    test_safe_copy_and_paste(debug_mode)
    
    if args.simulate:
        simulate_problem_scenario(debug_mode)
    
    print("\n=== 所有测试完成 ===")
    print("\n修复说明：")
    print("1. 减少了延迟时间从100ms到50ms，降低剪贴板被修改的风险")
    print("2. 添加了安全复制粘贴方法，在粘贴前验证剪贴板内容")
    print("3. 增加了调试模式，可以追踪剪贴板状态变化")
    print("\n如果仍然遇到问题，请：")
    print("1. 运行 'python test_clipboard_fix.py --enable-debug' 启用调试模式")
    print("2. 重新启动应用程序")
    print("3. 复现问题并查看详细日志")
    print("4. 运行 'python test_clipboard_fix.py --disable-debug' 禁用调试模式")

if __name__ == '__main__':
    main()