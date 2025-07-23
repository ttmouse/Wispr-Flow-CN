#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试app_loader中设置保存修复效果
"""

import sys
import os
import logging
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def setup_test_logging():
    """设置测试日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def test_app_loader_fix():
    """测试app_loader中的设置保存修复"""
    print("=== 测试app_loader设置保存修复效果 ===")
    
    try:
        from settings_manager import SettingsManager
        
        # 创建设置管理器实例
        settings_manager = SettingsManager()
        print("✓ 设置管理器初始化成功")
        
        # 模拟app_loader中的批量设置更新
        print("\n--- 测试批量模型设置更新（修复后） ---")
        
        # 模拟FunASR引擎加载后的设置更新
        model_paths = {
            'asr_model_path': '/test/asr/model/path',
            'punc_model_path': '/test/punc/model/path'
        }
        
        asr_available = bool(model_paths.get('asr_model_path'))
        punc_available = bool(model_paths.get('punc_model_path'))
        
        # 批量更新所有设置，只保存一次（修复后的逻辑）
        now = datetime.now().isoformat()
        settings_to_update = {
            'cache.models.last_check': now,
            'cache.models.asr_available': asr_available,
            'cache.models.punc_available': punc_available
        }
        
        # 添加模型路径设置
        if 'asr_model_path' in model_paths:
            settings_to_update['asr.model_path'] = model_paths['asr_model_path']
        if 'punc_model_path' in model_paths:
            settings_to_update['asr.punc_model_path'] = model_paths['punc_model_path']
        
        print(f"准备批量更新 {len(settings_to_update)} 个设置项")
        
        # 一次性保存所有设置
        result = settings_manager.set_multiple_settings(settings_to_update)
        
        if result:
            print("✓ 批量设置更新成功")
            print("✓ 预期只产生一条'设置保存成功'日志")
        else:
            print("✗ 批量设置更新失败")
            
        print("\n--- 测试完成 ---")
        print("检查上方日志，应该只看到一条'设置保存成功'的日志记录")
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    setup_test_logging()
    test_app_loader_fix()