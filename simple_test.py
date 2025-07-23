#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试设置保存修复效果
"""

import sys
import os
import logging
import json
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def test_settings_only():
    """只测试设置管理器核心功能"""
    print("=== 测试设置管理器批量保存修复 ===")
    
    try:
        # 直接导入设置管理器类
        from settings_manager import SettingsManager
        
        # 直接创建设置管理器（使用默认的settings.json）
        settings_manager = SettingsManager()
        print("✓ 设置管理器初始化成功")
        
        print("\n--- 测试1: 批量模型路径更新 ---")
        print("修复前：会产生2条'设置保存成功'日志")
        print("修复后：应该只产生1条'设置保存成功'日志")
        
        model_paths = {
            'asr_model_path': '/test/asr/model/path',
            'punc_model_path': '/test/punc/model/path'
        }
        
        result = settings_manager.update_model_paths(model_paths)
        print(f"模型路径更新结果: {result}")
        
        print("\n--- 测试2: 批量模型缓存更新 ---")
        print("修复前：会产生3条'设置保存成功'日志")
        print("修复后：应该只产生1条'设置保存成功'日志")
        
        result = settings_manager.update_models_cache(True, True)
        print(f"模型缓存更新结果: {result}")
        
        print("\n--- 测试3: 批量权限缓存更新 ---")
        print("修复前：会产生2条'设置保存成功'日志")
        print("修复后：应该只产生1条'设置保存成功'日志")
        
        result = settings_manager.update_permissions_cache(True, True)
        print(f"权限缓存更新结果: {result}")
        
        print("\n✓ 所有测试完成")
        print("\n总结：")
        print("- 如果看到每个测试只有1条'设置保存成功'日志，说明修复成功")
        print("- 如果看到每个测试有多条'设置保存成功'日志，说明还有问题")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_settings_only()