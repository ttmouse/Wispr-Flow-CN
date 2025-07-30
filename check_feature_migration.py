#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查功能迁移完整性
确保原始Application类的所有关键功能都已在新架构中实现
"""

import os
import ast
import sys

def extract_methods_from_file(file_path):
    """从文件中提取所有方法名"""
    if not os.path.exists(file_path):
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        methods = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append(f"{node.name}.{item.name}")
        
        return methods
    except Exception as e:
        print(f"解析文件 {file_path} 失败: {e}")
        return []

def check_feature_migration():
    """检查功能迁移完整性"""
    print("🔍 检查Application类功能迁移完整性")
    print("=" * 60)
    
    # 原始Application类的关键方法
    original_key_methods = [
        "start_recording",
        "stop_recording", 
        "toggle_recording",
        "on_option_press",
        "on_option_release",
        "show_window",
        "quit_application",
        "update_ui",
        "is_ready_for_recording",
        "cleanup",
        "run"
    ]
    
    print("📋 原始Application类关键方法:")
    for method in original_key_methods:
        print(f"  • {method}")
    
    print(f"\n🔍 检查新架构中的实现:")
    
    # 检查各个管理器中的实现
    manager_mappings = {
        "RecordingManager": {
            "file": "src/managers/recording_manager.py",
            "expected_methods": ["start_recording", "stop_recording", "toggle_recording", "is_ready_for_recording"]
        },
        "SystemManager": {
            "file": "src/managers/system_manager.py", 
            "expected_methods": ["show_tray_message", "get_permissions_status"]
        },
        "UIManager": {
            "file": "src/managers/ui_manager.py",
            "expected_methods": ["show_main_window", "hide_main_window"]
        },
        "ApplicationContext": {
            "file": "src/managers/application_context.py",
            "expected_methods": ["start_recording", "stop_recording", "show_main_window", "cleanup"]
        },
        "SimplifiedApplication": {
            "file": "src/simplified_main.py",
            "expected_methods": ["run", "cleanup", "quit_application"]
        },
        "ApplicationAdapter": {
            "file": "src/compatibility_adapter.py",
            "expected_methods": original_key_methods
        }
    }
    
    all_implemented = True
    
    for manager_name, info in manager_mappings.items():
        file_path = info["file"]
        expected_methods = info["expected_methods"]
        
        print(f"\n📊 {manager_name} ({file_path}):")
        
        if not os.path.exists(file_path):
            print(f"  ❌ 文件不存在")
            all_implemented = False
            continue
        
        # 提取实际方法
        actual_methods = extract_methods_from_file(file_path)
        class_methods = [m.split('.')[1] for m in actual_methods if m.startswith(manager_name.split('Manager')[0]) or m.startswith(manager_name)]
        
        # 检查期望的方法
        for method in expected_methods:
            if any(method in cm for cm in class_methods):
                print(f"  ✅ {method}")
            else:
                print(f"  ❌ {method} (缺失)")
                all_implemented = False
    
    # 检查兼容性适配器
    print(f"\n🔧 兼容性检查:")
    adapter_path = "src/compatibility_adapter.py"
    if os.path.exists(adapter_path):
        print(f"  ✅ 兼容性适配器存在")
        
        # 检查适配器是否实现了所有关键方法
        adapter_methods = extract_methods_from_file(adapter_path)
        adapter_class_methods = [m.split('.')[1] for m in adapter_methods if 'Application' in m]
        
        missing_methods = []
        for method in original_key_methods:
            if not any(method in acm for acm in adapter_class_methods):
                missing_methods.append(method)
        
        if missing_methods:
            print(f"  ⚠️ 适配器缺少方法: {', '.join(missing_methods)}")
            all_implemented = False
        else:
            print(f"  ✅ 适配器实现了所有关键方法")
    else:
        print(f"  ❌ 兼容性适配器不存在")
        all_implemented = False
    
    # 总结
    print(f"\n🎯 迁移完整性总结:")
    if all_implemented:
        print(f"  ✅ 所有关键功能都已在新架构中实现")
        print(f"  ✅ 兼容性适配器确保向后兼容")
        print(f"  🎉 可以安全地替换原始main.py")
    else:
        print(f"  ⚠️ 部分功能尚未完全迁移")
        print(f"  💡 建议完善缺失的功能后再进行替换")
    
    return all_implemented

def check_import_compatibility():
    """检查导入兼容性"""
    print(f"\n📦 检查导入兼容性:")
    
    # 检查是否有其他文件导入了原始的Application类
    import_files = []
    
    # 搜索可能导入Application的文件
    search_dirs = ["src", "tests", "."]
    for search_dir in search_dirs:
        if os.path.exists(search_dir):
            for root, dirs, files in os.walk(search_dir):
                for file in files:
                    if file.endswith('.py') and file != 'main.py':
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                if 'from main import Application' in content or 'import main' in content:
                                    import_files.append(file_path)
                        except:
                            pass
    
    if import_files:
        print(f"  ⚠️ 发现以下文件导入了原始Application:")
        for file_path in import_files:
            print(f"    • {file_path}")
        print(f"  💡 这些文件需要更新导入语句")
    else:
        print(f"  ✅ 没有发现其他文件导入原始Application")
    
    return len(import_files) == 0

def main():
    """主函数"""
    try:
        print("🚀 开始检查功能迁移完整性...")
        
        # 切换到项目根目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
        
        # 检查功能迁移
        migration_complete = check_feature_migration()
        
        # 检查导入兼容性
        import_compatible = check_import_compatibility()
        
        # 总体评估
        print(f"\n📋 总体评估:")
        if migration_complete and import_compatible:
            print(f"  🎉 功能迁移完整，可以安全替换main.py")
            return 0
        else:
            print(f"  ⚠️ 需要完善部分功能后再进行替换")
            return 1
        
    except Exception as e:
        print(f"❌ 检查过程出错: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
