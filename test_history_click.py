#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试历史记录点击功能
验证点击历史记录时复制的是原始文本而不是高亮文本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ui.components.history_manager import HistoryManager
from src.state_manager import StateManager
from datetime import datetime

def test_history_click_functionality():
    """测试历史记录点击功能"""
    print("=== 测试历史记录点击功能 ===")
    
    # 创建历史记录管理器
    history_manager = HistoryManager("test_history.json", max_history=10)
    
    # 创建状态管理器并设置热词
    state_manager = StateManager()
    # 直接设置热词到状态管理器
    if hasattr(state_manager, 'hotwords'):
        state_manager.hotwords = ["prompt", "cursor", "HTML"]
    else:
        # 如果没有hotwords属性，创建一个get_hotwords方法
        state_manager.get_hotwords = lambda: ["prompt", "cursor", "HTML"]
    
    history_manager.set_state_manager(state_manager)
    
    # 添加测试数据
    test_texts = [
        "这是一个包含prompt关键词的测试文本",
        "cursor移动到HTML标签位置",
        "普通文本没有热词"
    ]
    
    print("\n1. 添加测试历史记录:")
    for i, text in enumerate(test_texts):
        history_manager.add_history_item(text)
        print(f"   {i}: {text}")
    
    print("\n2. 获取显示文本（带高亮）:")
    display_texts = history_manager.get_history_texts()
    for i, text in enumerate(display_texts):
        print(f"   {i}: {text}")
    
    print("\n3. 测试根据索引获取原始文本:")
    for i in range(len(test_texts)):
        original_text = history_manager.get_original_text_by_index(i)
        print(f"   索引 {i}: {original_text}")
        
        # 验证原始文本不包含HTML标签
        if '<b>' in original_text or '</b>' in original_text:
            print(f"   ❌ 错误：原始文本包含HTML标签")
        else:
            print(f"   ✓ 正确：原始文本不包含HTML标签")
    
    print("\n4. 测试边界情况:")
    # 测试无效索引
    invalid_text = history_manager.get_original_text_by_index(-1)
    print(f"   索引 -1: '{invalid_text}' (应为空字符串)")
    
    invalid_text = history_manager.get_original_text_by_index(999)
    print(f"   索引 999: '{invalid_text}' (应为空字符串)")
    
    print("\n=== 测试完成 ===")
    
    # 清理测试文件
    if os.path.exists("test_history.json"):
        os.remove("test_history.json")
        print("✓ 测试文件已清理")

if __name__ == "__main__":
    test_history_click_functionality()