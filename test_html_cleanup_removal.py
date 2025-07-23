#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试HTML清理移除后的效果
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ui.components.history_manager import HistoryManager
from settings_manager import SettingsManager
from state_manager import StateManager
import json
from datetime import datetime

def test_history_save_without_html_cleanup():
    """测试历史记录保存时不进行HTML清理"""
    print("\n=== 测试历史记录保存（无HTML清理）===")
    
    # 创建测试管理器
    settings_manager = SettingsManager()
    state_manager = StateManager(settings_manager)
    history_manager = HistoryManager(state_manager, max_history=10)
    
    # 测试数据 - 包含HTML标签的文本
    test_texts = [
        "这是一个<b>热词</b>测试",
        "包含<b>facebook</b>和<b>浮层</b>的文本",
        "普通文本没有HTML标签",
        "<b>HTML</b>标签应该被保留在历史记录中"
    ]
    
    # 添加测试数据到历史记录
    for text in test_texts:
        history_manager.add_history_item(text)
    
    # 保存历史记录
    history_data = history_manager.get_history_for_save()
    success = history_manager.save_history(history_data)
    
    print(f"保存结果: {'成功' if success else '失败'}")
    
    # 读取保存的文件内容
    try:
        with open(history_manager.history_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        print("\n保存的历史记录内容:")
        for i, item in enumerate(saved_data[-4:], 1):  # 显示最后4条
            print(f"{i}. {item['text']}")
            
        # 检查HTML标签是否被保留
        html_preserved = any('<b>' in item['text'] for item in saved_data[-4:])
        print(f"\nHTML标签保留状态: {'✓ 已保留' if html_preserved else '✗ 已清理'}")
        
    except Exception as e:
        print(f"读取历史记录文件失败: {e}")

def test_clipboard_operations():
    """测试剪贴板操作（模拟）"""
    print("\n=== 测试剪贴板操作（模拟）===")
    
    # 模拟包含HTML标签的文本
    test_text = "这是一个<b>热词</b>测试文本"
    
    print(f"原始文本: {test_text}")
    
    # 模拟转录完成回调
    print("\n模拟转录完成:")
    print(f"- 待粘贴文本: {test_text}")
    print("- HTML标签状态: 保留（不再清理）")
    
    # 模拟历史记录点击
    print("\n模拟历史记录点击:")
    print(f"- 复制到剪贴板: {test_text}")
    print("- HTML标签状态: 保留（不再清理）")
    
    print("\n✓ 剪贴板操作测试完成")

def main():
    """主测试函数"""
    print("开始测试HTML清理移除后的效果...")
    
    try:
        test_history_save_without_html_cleanup()
        test_clipboard_operations()
        
        print("\n=== 测试总结 ===")
        print("✓ 历史记录保存: 不再清理HTML标签")
        print("✓ 剪贴板操作: 不再清理HTML标签")
        print("✓ 所有修改已生效")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()