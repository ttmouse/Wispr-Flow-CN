#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试设置保存修复效果
"""

import sys
import os
import logging
from datetime import datetime

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 配置简单的日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def test_settings_manager():
    """测试设置管理器的批量保存功能"""
    print("=== 测试设置管理器修复效果 ===")
    
    try:
        from settings_manager import SettingsManager
        
        # 创建设置管理器实例
        settings_manager = SettingsManager()
        print("✓ 设置管理器初始化成功")
        
        # 测试批量模型路径更新（修复前会产生多个日志）
        print("\n--- 测试模型路径批量更新 ---")
        model_paths = {
            'asr_model_path': '/test/asr/model/path',
            'punc_model_path': '/test/punc/model/path'
        }
        
        result = settings_manager.update_model_paths(model_paths)
        print(f"模型路径更新结果: {result}")
        
        # 测试批量模型缓存更新（修复前会产生多个日志）
        print("\n--- 测试模型缓存批量更新 ---")
        result = settings_manager.update_models_cache(True, True)
        print(f"模型缓存更新结果: {result}")
        
        # 测试批量权限缓存更新（修复前会产生多个日志）
        print("\n--- 测试权限缓存批量更新 ---")
        result = settings_manager.update_permissions_cache(True, True)
        print(f"权限缓存更新结果: {result}")
        
        print("\n✓ 所有测试完成，检查上方日志输出")
        print("修复效果：每个批量操作应该只产生一条'设置保存成功'日志")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_settings_manager()