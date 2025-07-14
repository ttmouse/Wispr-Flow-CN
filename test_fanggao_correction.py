#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试梵高到行高的发音纠错功能
"""

class TestEngine:
    """模拟引擎类用于测试"""
    
    def __init__(self):
        # 模拟热词列表
        self.hotwords = ['cursor', '禁音', '行高', '浮层', '热词', 'HTML', 'facebook']
    
    def _is_pronunciation_correction_enabled(self):
        """检查是否启用发音纠错"""
        return True  # 默认启用
    
    def _correct_similar_pronunciation(self, text):
        """纠正发音相似的词"""
        if not text or not self._is_pronunciation_correction_enabled():
            return text
        
        # 定义发音相似词映射表
        pronunciation_map = {
            '浮沉': '浮层',
            '浮尘': '浮层',
            '浮城': '浮层',
            '胡成': '浮层',  # 根据用户需求添加
            '含高': '行高',  # 添加含高到行高的映射
            '韩高': '行高',  # 可能的其他发音变体
            '汉高': '行高',  # 可能的其他发音变体
            '梵高': '行高',  # 修复梵高被错误识别为行高的问题
        }
        
        corrected_text = text
        
        # 只有当目标热词在热词列表中时才进行纠错
        for similar_word, correct_word in pronunciation_map.items():
            if similar_word in corrected_text and correct_word in self.hotwords:
                corrected_text = corrected_text.replace(similar_word, correct_word)
                print(f"🔧 发音纠错: '{similar_word}' -> '{correct_word}'")
        
        return corrected_text

def test_fanggao_correction():
    """测试梵高到行高的发音纠错功能"""
    engine = TestEngine()
    
    test_cases = [
        "梵高设置很重要",
        "调整一下梵高参数", 
        "梵高的效果不错",
        "这个梵高需要优化",
        "梵高和浮层都是热词",
        "行高本身就是正确的",
        "含高也需要纠正",
        "梵高、含高、韩高都应该纠正为行高"
    ]
    
    print("=== 梵高到行高发音纠错测试 ===")
    print(f"热词列表: {engine.hotwords}")
    print()
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"测试 {i}: {test_text}")
        corrected = engine._correct_similar_pronunciation(test_text)
        print(f"结果: {corrected}")
        if test_text != corrected:
            print("✅ 发音纠错生效")
        else:
            print("ℹ️  无需纠错")
        print("-" * 50)

if __name__ == "__main__":
    test_fanggao_correction()