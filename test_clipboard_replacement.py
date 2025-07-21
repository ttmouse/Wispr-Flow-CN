#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪贴板替换功能测试脚本
用于验证转录内容是否能正确替换剪贴板历史内容
"""

import time
import pyperclip
from src.clipboard_manager import ClipboardManager

def test_clipboard_replacement():
    """测试剪贴板替换功能"""
    print("=== 剪贴板替换功能测试 ===")
    
    # 创建剪贴板管理器（启用调试模式）
    clipboard = ClipboardManager(debug_mode=True)
    
    # 模拟历史剪贴板内容
    historical_content = "这是历史剪贴板内容，应该被替换"
    print(f"\n1. 设置历史剪贴板内容: {historical_content}")
    pyperclip.copy(historical_content)
    time.sleep(0.1)
    
    # 验证历史内容
    current = pyperclip.paste()
    print(f"   当前剪贴板内容: {current}")
    
    # 模拟转录结果
    transcription_results = [
        "第一次转录结果",
        "第二次转录结果 - 应该完全替换第一次",
        "第三次转录结果 - 应该完全替换第二次",
        "最终转录结果"
    ]
    
    for i, text in enumerate(transcription_results, 1):
        print(f"\n{i}. 模拟转录结果: {text}")
        
        # 使用增强的复制方法
        success = clipboard.copy_to_clipboard(text)
        if success:
            print(f"   ✓ 复制成功")
        else:
            print(f"   ❌ 复制失败")
        
        # 验证剪贴板内容
        time.sleep(0.1)
        current = pyperclip.paste()
        if current == text:
            print(f"   ✓ 验证成功: 剪贴板内容正确")
        else:
            print(f"   ❌ 验证失败: 期望 '{text}', 实际 '{current}'")
        
        # 等待一段时间，模拟实际使用场景
        time.sleep(0.5)
    
    print("\n=== 测试完成 ===")
    
    # 最终清理
    clipboard._thorough_clear_clipboard()
    final_content = pyperclip.paste()
    print(f"最终剪贴板内容: '{final_content}'")

def test_safe_copy_and_paste():
    """测试安全复制粘贴功能"""
    print("\n=== 安全复制粘贴功能测试 ===")
    
    clipboard = ClipboardManager(debug_mode=True)
    
    # 设置干扰内容
    interference = "干扰内容 - 不应该被粘贴"
    pyperclip.copy(interference)
    print(f"设置干扰内容: {interference}")
    
    # 目标内容
    target_text = "目标内容 - 应该被正确粘贴"
    print(f"目标内容: {target_text}")
    
    # 执行安全复制粘贴
    print("\n执行安全复制粘贴...")
    success = clipboard.safe_copy_and_paste(target_text)
    
    if success:
        print("✓ 安全复制粘贴成功")
    else:
        print("❌ 安全复制粘贴失败")
    
    # 检查最终剪贴板状态
    time.sleep(0.2)
    final_content = pyperclip.paste()
    print(f"最终剪贴板内容: '{final_content}'")

if __name__ == "__main__":
    print("剪贴板替换功能测试")
    print("=" * 50)
    
    try:
        test_clipboard_replacement()
        test_safe_copy_and_paste()
        
        print("\n✓ 所有测试完成")
        print("\n使用说明:")
        print("1. 现在可以测试语音转文本功能")
        print("2. 观察控制台输出的调试信息")
        print("3. 验证每次转录是否完全替换剪贴板内容")
        print("4. 如果问题解决，可以运行以下命令禁用调试模式:")
        print("   python tools/test_clipboard_fix.py --disable-debug")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()