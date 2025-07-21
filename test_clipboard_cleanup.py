#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪贴板清理功能测试脚本
测试改进后的剪贴板清理机制是否能有效防止历史记录残留
"""

import sys
import os
import time
import pyperclip

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from clipboard_manager import ClipboardManager

def test_clipboard_cleanup():
    """测试剪贴板清理功能"""
    print("=== 剪贴板清理功能测试 ===")
    
    # 创建剪贴板管理器（启用调试模式）
    clipboard = ClipboardManager(debug_mode=True)
    
    # 测试场景1：设置历史内容，然后清理
    print("\n📋 测试场景1：清理历史内容")
    print("-" * 40)
    
    # 手动设置一些历史内容
    historical_content = "这是一些历史剪贴板内容，应该被清理掉"
    pyperclip.copy(historical_content)
    print(f"设置历史内容: {historical_content}")
    
    # 验证历史内容存在
    current = pyperclip.paste()
    print(f"当前剪贴板内容: {current}")
    
    # 使用新的清理方法
    print("\n执行彻底清理...")
    clipboard._thorough_clear_clipboard()
    
    # 验证清理结果
    after_clear = pyperclip.paste()
    print(f"清理后剪贴板内容: '{after_clear}'")
    
    if not after_clear or after_clear.strip() == "":
        print("✅ 清理成功：剪贴板已完全清空")
    else:
        print(f"❌ 清理失败：仍有残留内容 '{after_clear}'")
    
    # 测试场景2：复制新内容时的清理
    print("\n📋 测试场景2：复制新内容时的自动清理")
    print("-" * 40)
    
    # 再次设置历史内容
    pyperclip.copy("另一段历史内容")
    print(f"设置新的历史内容: {pyperclip.paste()}")
    
    # 使用copy_to_clipboard方法（会自动清理）
    new_content = "这是要复制的新内容"
    print(f"准备复制新内容: {new_content}")
    
    success = clipboard.copy_to_clipboard(new_content)
    
    if success:
        final_content = pyperclip.paste()
        if final_content == new_content:
            print("✅ 复制成功：新内容正确设置，历史内容已清理")
        else:
            print(f"❌ 复制异常：期望 '{new_content}', 实际 '{final_content}'")
    else:
        print("❌ 复制失败")
    
    # 测试场景3：安全复制粘贴的清理
    print("\n📋 测试场景3：安全复制粘贴的清理机制")
    print("-" * 40)
    
    # 设置干扰内容
    interference_content = "这是干扰内容，应该被清理"
    pyperclip.copy(interference_content)
    print(f"设置干扰内容: {interference_content}")
    
    # 使用安全复制粘贴
    target_content = "安全粘贴测试内容"
    print(f"准备安全粘贴: {target_content}")
    print("注意：这会执行实际的粘贴操作（Cmd+V）")
    
    # 给用户一些时间准备
    print("3秒后开始测试...")
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    success = clipboard.safe_copy_and_paste(target_content)
    
    if success:
        print("✅ 安全粘贴完成")
    else:
        print("❌ 安全粘贴失败")
    
    print("\n=== 测试完成 ===")

def test_multiple_operations():
    """测试连续多次操作的清理效果"""
    print("\n=== 连续操作清理测试 ===")
    
    clipboard = ClipboardManager(debug_mode=False)  # 关闭调试模式，减少输出
    
    test_texts = [
        "第一段测试文本",
        "第二段测试文本",
        "第三段测试文本",
        "第四段测试文本",
        "第五段测试文本"
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n第{i}次操作: {text}")
        
        # 每次操作前检查剪贴板状态
        before = pyperclip.paste()
        print(f"操作前剪贴板: '{before[:30]}{'...' if len(before) > 30 else ''}'")
        
        # 执行复制
        success = clipboard.copy_to_clipboard(text)
        
        # 检查结果
        after = pyperclip.paste()
        if success and after == text:
            print(f"✅ 成功: '{after}'")
        else:
            print(f"❌ 失败: 期望 '{text}', 实际 '{after}'")
        
        time.sleep(0.1)  # 短暂延迟
    
    print("\n连续操作测试完成")

if __name__ == "__main__":
    try:
        test_clipboard_cleanup()
        test_multiple_operations()
        
        print("\n🎉 所有测试完成！")
        print("\n💡 改进说明：")
        print("1. 增加了彻底清理机制，多次尝试确保清空")
        print("2. 在每次复制前都会彻底清理历史内容")
        print("3. 增加了二次验证，确保复制内容正确")
        print("4. 提供了详细的调试信息帮助排查问题")
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中出错: {e}")
        import traceback
        traceback.print_exc()