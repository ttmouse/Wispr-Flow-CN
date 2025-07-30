#!/usr/bin/env python3
"""
简单测试脚本
"""
import sys
import os

# 添加src目录到Python路径
src_dir = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_dir)

def test_import():
    """测试导入"""
    try:
        print("🔧 测试导入managers模块...")
        
        # 测试导入managers
        import managers
        print("✅ managers模块导入成功")
        
        # 测试导入具体的包装器
        from managers.ui_manager_wrapper import UIManagerWrapper
        print("✅ UIManagerWrapper导入成功")
        
        from managers.audio_manager_wrapper import AudioManagerWrapper
        print("✅ AudioManagerWrapper导入成功")
        
        from managers.state_manager_wrapper import StateManagerWrapper
        print("✅ StateManagerWrapper导入成功")
        
        from managers.settings_manager_wrapper import SettingsManagerWrapper
        print("✅ SettingsManagerWrapper导入成功")
        
        print("🎉 所有managers模块导入成功！")
        return True
        
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_import()
