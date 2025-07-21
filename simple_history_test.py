#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的历史记录测试脚本
专注于测试历史记录添加的核心逻辑
"""

import sys
import os
import json
import traceback
from datetime import datetime

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 直接定义clean_html_tags函数
def clean_html_tags(text):
    """清理HTML标签，返回纯文本"""
    if not text:
        return text
    import re
    # 移除HTML标签
    clean_text = re.sub(r'<[^>]+>', '', text)
    # 解码HTML实体
    clean_text = clean_text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"').replace('&#39;', "'")
    return clean_text

try:
    from ui.components.history_manager import HistoryManager
    from settings_manager import SettingsManager
    from state_manager import StateManager
except ImportError as e:
    print(f"导入模块失败: {e}")
    sys.exit(1)

def test_history_manager():
    """测试历史记录管理器"""
    print("=== 历史记录管理器测试 ===")
    
    try:
        # 创建测试用的设置和状态管理器
        settings_manager = SettingsManager()
        state_manager = StateManager()
        
        # 创建历史记录管理器
        history_manager = HistoryManager(
            history_file_path="test_history_simple.json"
        )
        history_manager.set_state_manager(state_manager)
        
        print("✓ 历史记录管理器创建成功")
        
        # 测试添加不同类型的文本
        test_cases = [
            ("正常文本", True),
            ("另一个正常文本", True),
            ("正常文本", False),  # 重复文本
            ("<b>带HTML标签的文本</b>", True),
            ("带HTML标签的文本", False),  # 去除HTML后重复
            ("", False),  # 空文本
            ("   ", False),  # 空白文本
            ("转写失败，请重试", True),  # 错误消息也应该被添加
        ]
        
        for i, (text, expected_added) in enumerate(test_cases):
            print(f"\n测试 {i+1}: '{text}'")
            
            initial_count = len(history_manager.history_items)
            result = history_manager.add_history_item(text)
            final_count = len(history_manager.history_items)
            
            print(f"  返回值: {result}")
            print(f"  历史记录数量: {initial_count} -> {final_count}")
            print(f"  期望添加: {expected_added}")
            print(f"  实际添加: {final_count > initial_count}")
            
            if result == expected_added:
                print(f"  ✓ 测试通过")
            else:
                print(f"  ❌ 测试失败")
        
        # 显示最终的历史记录
        print(f"\n最终历史记录数量: {len(history_manager.history_items)}")
        for i, item in enumerate(history_manager.history_items):
            print(f"  {i+1}. {item['text']}")
        
        return history_manager
        
    except Exception as e:
        print(f"❌ 历史记录管理器测试失败: {e}")
        traceback.print_exc()
        return None

def test_transcription_flow():
    """测试转录流程中的文本处理"""
    print("\n=== 转录流程测试 ===")
    
    # 模拟不同的转录结果
    transcription_results = [
        "这是一个正常的转录结果",
        "另一个转录结果",
        "转写失败，请重试",  # 错误消息
        "<b>带格式的</b>转录结果",
        "",  # 空结果
        "   ",  # 空白结果
    ]
    
    for i, text in enumerate(transcription_results):
        print(f"\n转录结果 {i+1}: '{text}'")
        
        # 模拟on_transcription_done的处理逻辑
        if text and text.strip():
            clean_text = clean_html_tags(text)
            print(f"  清理后文本: '{clean_text}'")
            print(f"  应该被处理: 是")
        else:
            print(f"  应该被处理: 否（空文本）")

def test_duplicate_detection():
    """测试重复检测逻辑"""
    print("\n=== 重复检测测试 ===")
    
    try:
        settings_manager = SettingsManager()
        state_manager = StateManager()
        history_manager = HistoryManager(
            history_file_path="test_duplicate.json"
        )
        history_manager.set_state_manager(state_manager)
        
        # 添加基础文本
        base_texts = ["文本A", "文本B", "<b>格式化文本</b>"]
        for text in base_texts:
            history_manager.add_history_item(text)
        
        print(f"基础历史记录: {len(history_manager.history_items)} 条")
        
        # 测试重复检测
        test_cases = [
            ("文本A", True),  # 完全重复
            ("<i>文本A</i>", True),  # HTML包装的重复
            ("文本A ", True),  # 带空格的重复
            ("格式化文本", True),  # 去除HTML后重复
            ("新文本", False),  # 不重复
        ]
        
        existing_texts = [item['text'] for item in history_manager.history_items]
        
        for text, expected_duplicate in test_cases:
            is_duplicate = history_manager.is_duplicate_text(text, existing_texts)
            status = "✓" if is_duplicate == expected_duplicate else "❌"
            print(f"  {status} '{text}' -> 重复: {is_duplicate} (期望: {expected_duplicate})")
        
    except Exception as e:
        print(f"❌ 重复检测测试失败: {e}")
        traceback.print_exc()

def main():
    """主函数"""
    print("开始简化历史记录测试...\n")
    
    try:
        # 运行各项测试
        history_manager = test_history_manager()
        test_transcription_flow()
        test_duplicate_detection()
        
        print("\n=== 测试完成 ===")
        
        # 保存测试结果
        if history_manager:
            test_result = {
                'test_time': datetime.now().isoformat(),
                'history_count': len(history_manager.history_items),
                'history_items': history_manager.get_history_for_save()
            }
            
            with open('simple_test_result.json', 'w', encoding='utf-8') as f:
                json.dump(test_result, f, ensure_ascii=False, indent=2)
            
            print("✓ 测试结果已保存到 simple_test_result.json")
        
    except Exception as e:
        print(f"❌ 测试运行失败: {e}")
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())