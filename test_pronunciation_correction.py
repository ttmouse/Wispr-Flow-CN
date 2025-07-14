#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试发音相似词纠错功能
"""

class TestEngine:
    """模拟引擎类用于测试"""
    
    def __init__(self):
        # 模拟热词列表
        self.hotwords = ['浮层', 'cursor', '禁音', '行高']
    
    def _correct_similar_pronunciation(self, text):
        """纠正发音相似的词"""
        if not text:
            return text
        
        # 定义发音相似词映射表
        pronunciation_map = {
            '浮沉': '浮层',
            '浮尘': '浮层',
            '浮城': '浮层',
            '胡成': '浮层',  # 根据用户需求添加
        }
        
        corrected_text = text
        
        # 只有当目标热词在热词列表中时才进行纠错
        for similar_word, correct_word in pronunciation_map.items():
            if similar_word in corrected_text and correct_word in self.hotwords:
                corrected_text = corrected_text.replace(similar_word, correct_word)
                print(f"🔧 发音纠错: '{similar_word}' -> '{correct_word}'")
        
        return corrected_text

def test_pronunciation_correction():
    """测试发音纠错功能"""
    engine = TestEngine()
    
    test_cases = [
        "胡成是一个很好的功能",
        "浮沉显示在屏幕上", 
        "浮尘效果很棒",
        "浮城的设计很好",
        "这个浮层很漂亮",
        "cursor移动很快",
        "没有相似词的文本",
        "胡成和浮沉都需要纠正为浮层"
    ]
    
    print("=== 发音相似词纠错测试 ===")
    print(f"热词列表: {engine.hotwords}")
    print()
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"测试 {i}:")
        print(f"原文: {test_text}")
        corrected = engine._correct_similar_pronunciation(test_text)
        print(f"纠错后: {corrected}")
        print(f"是否有变化: {'是' if corrected != test_text else '否'}")
        print("-" * 50)

if __name__ == "__main__":
    test_pronunciation_correction()