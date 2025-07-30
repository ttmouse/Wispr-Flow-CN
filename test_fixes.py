#!/usr/bin/env python3
"""
测试修复后的功能
"""
import sys
import os

# 添加src目录到Python路径
src_dir = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_dir)

def test_settings_import():
    """测试设置窗口导入"""
    try:
        print("🔧 测试设置窗口导入...")
        
        # 测试导入MacOSSettingsWindow
        from ui.settings_window import MacOSSettingsWindow
        print("✅ MacOSSettingsWindow导入成功")
        
        # 测试SettingsManagerWrapper
        from managers.settings_manager_wrapper import SettingsManagerWrapper
        print("✅ SettingsManagerWrapper导入成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 设置窗口导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ui_manager():
    """测试UI管理器"""
    try:
        print("🔧 测试UI管理器...")
        
        # 测试UIManagerWrapper导入
        from managers.ui_manager_wrapper import UIManagerWrapper
        print("✅ UIManagerWrapper导入成功")
        
        return True
        
    except Exception as e:
        print(f"❌ UI管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_main_window():
    """测试主窗口"""
    try:
        print("🔧 测试主窗口...")
        
        # 测试主窗口导入
        from ui.main_window import MainWindow
        print("✅ MainWindow导入成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 主窗口测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 开始测试修复...")
    
    success = True
    
    # 测试设置窗口
    if not test_settings_import():
        success = False
    
    # 测试UI管理器
    if not test_ui_manager():
        success = False
    
    # 测试主窗口
    if not test_main_window():
        success = False
    
    if success:
        print("✅ 所有测试通过！")
        sys.exit(0)
    else:
        print("❌ 部分测试失败！")
        sys.exit(1)
