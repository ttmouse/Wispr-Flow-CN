#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热词加载测试脚本
"""

import sys
import os
sys.path.append('src')

from funasr_engine import FunASREngine
from settings_manager import SettingsManager

def test_hotword_loading():
    """测试热词加载功能"""
    print("=== 热词加载测试 ===")
    
    try:
        # 初始化设置管理器
        settings_manager = SettingsManager()
        print(f"✅ 设置管理器初始化成功")
        
        # 初始化FunASR引擎
        print("\n正在初始化FunASR引擎...")
        engine = FunASREngine(settings_manager)
        
        if engine.is_ready:
            print(f"✅ FunASR引擎初始化成功")
            print(f"📊 热词数量: {len(engine.hotwords)}")
            print(f"📝 热词列表: {engine.hotwords}")
            print(f"⚖️ 热词权重: {engine._get_hotword_weight()}")
            
            # 测试热词重新加载
            print("\n测试热词重新加载...")
            engine.reload_hotwords()
            
            # 检查热词文件路径
            if getattr(sys, 'frozen', False):
                application_path = sys._MEIPASS
            else:
                application_path = os.path.dirname(os.path.abspath('src/funasr_engine.py'))
            
            hotwords_file = os.path.join(os.path.dirname(application_path), "resources", "hotwords.txt")
            print(f"\n📁 热词文件路径: {hotwords_file}")
            print(f"📄 文件是否存在: {os.path.exists(hotwords_file)}")
            
            if os.path.exists(hotwords_file):
                with open(hotwords_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"📖 文件内容预览:\n{content[:200]}...")
            
        else:
            print("❌ FunASR引擎初始化失败")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_hotword_loading()