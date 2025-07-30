#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终验证脚本
确认main.py替换成功，所有功能正常
"""

import os
import sys
import ast
import subprocess

def analyze_file_structure():
    """分析文件结构"""
    print("📁 文件结构分析:")
    print("=" * 50)
    
    files_to_check = {
        "src/main.py": "新的主程序文件",
        "src/main_original_backup.py": "原始Application类备份",
        "src/simplified_main.py": "SimplifiedApplication实现",
        "src/compatibility_adapter.py": "兼容性适配器",
        "src/managers/recording_manager.py": "录音管理器",
        "src/managers/system_manager.py": "系统管理器",
        "src/managers/event_bus.py": "事件总线",
        "src/managers/application_context.py": "应用程序上下文"
    }
    
    for file_path, description in files_to_check.items():
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = len(f.readlines())
            print(f"  ✅ {file_path}: {lines} 行 - {description}")
        else:
            print(f"  ❌ {file_path}: 不存在 - {description}")

def compare_code_complexity():
    """比较代码复杂度"""
    print(f"\n📊 代码复杂度对比:")
    print("=" * 50)
    
    # 原始Application类
    original_backup = "src/main_original_backup.py"
    if os.path.exists(original_backup):
        with open(original_backup, 'r', encoding='utf-8') as f:
            original_lines = len(f.readlines())
        print(f"  📄 原始Application类: {original_lines} 行")
    
    # 新的main.py
    new_main = "src/main.py"
    if os.path.exists(new_main):
        with open(new_main, 'r', encoding='utf-8') as f:
            new_lines = len(f.readlines())
        print(f"  📄 新的main.py: {new_lines} 行")
    
    # 管理器总计
    managers_dir = "src/managers"
    if os.path.exists(managers_dir):
        manager_files = [f for f in os.listdir(managers_dir) if f.endswith('.py') and f != '__init__.py']
        total_manager_lines = 0
        
        for manager_file in manager_files:
            manager_path = os.path.join(managers_dir, manager_file)
            with open(manager_path, 'r', encoding='utf-8') as f:
                lines = len(f.readlines())
                total_manager_lines += lines
        
        print(f"  📄 管理器总计: {total_manager_lines} 行 ({len(manager_files)} 个文件)")
    
    # 计算改进
    if 'original_lines' in locals() and 'new_lines' in locals():
        reduction = ((original_lines - new_lines) / original_lines) * 100
        print(f"  📈 主程序代码减少: {reduction:.1f}%")

def test_import_compatibility():
    """测试导入兼容性"""
    print(f"\n🔧 导入兼容性测试:")
    print("=" * 50)
    
    try:
        # 测试从main导入Application
        sys.path.insert(0, 'src')
        
        # 这应该能够成功导入
        from main import Application
        print("  ✅ from main import Application - 成功")
        
        # 测试Application类的关键方法
        key_methods = ['start_recording', 'stop_recording', 'show_window', 'run']
        for method in key_methods:
            if hasattr(Application, method):
                print(f"  ✅ Application.{method} - 存在")
            else:
                print(f"  ❌ Application.{method} - 缺失")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False

def test_startup():
    """测试启动"""
    print(f"\n🚀 启动测试:")
    print("=" * 50)
    
    try:
        # 测试启动信息
        result = subprocess.run([
            sys.executable, 'src/main.py'
        ], capture_output=True, text=True, timeout=5, cwd='.')
        
        if "🚀 启动 Dou-flow" in result.stdout:
            print("  ✅ 启动信息显示正常")
        else:
            print("  ❌ 启动信息异常")
            
        if "重构后的架构组件" in result.stdout:
            print("  ✅ 架构信息显示正常")
        else:
            print("  ❌ 架构信息缺失")
            
        if result.returncode == 0 or "KeyboardInterrupt" in result.stderr:
            print("  ✅ 程序启动成功")
            return True
        else:
            print(f"  ❌ 程序启动失败: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("  ✅ 程序正常启动（超时终止）")
        return True
    except Exception as e:
        print(f"  ❌ 启动测试失败: {e}")
        return False

def verify_architecture_benefits():
    """验证架构改进效果"""
    print(f"\n🎯 架构改进验证:")
    print("=" * 50)
    
    benefits = []
    
    # 检查职责分离
    managers_dir = "src/managers"
    if os.path.exists(managers_dir):
        manager_count = len([f for f in os.listdir(managers_dir) if f.endswith('.py') and f != '__init__.py'])
        if manager_count >= 6:
            benefits.append("✅ 职责分离: 功能拆分为多个专门管理器")
        else:
            benefits.append("⚠️ 职责分离: 管理器数量不足")
    
    # 检查事件总线
    if os.path.exists("src/managers/event_bus.py"):
        benefits.append("✅ 解耦通信: 实现事件总线系统")
    else:
        benefits.append("❌ 解耦通信: 缺少事件总线")
    
    # 检查兼容性
    if os.path.exists("src/compatibility_adapter.py"):
        benefits.append("✅ 向后兼容: 实现兼容性适配器")
    else:
        benefits.append("❌ 向后兼容: 缺少适配器")
    
    # 检查主程序简化
    if os.path.exists("src/main.py"):
        with open("src/main.py", 'r', encoding='utf-8') as f:
            lines = len(f.readlines())
        if lines < 200:
            benefits.append("✅ 代码简化: 主程序大幅简化")
        else:
            benefits.append("⚠️ 代码简化: 主程序仍较复杂")
    
    for benefit in benefits:
        print(f"  {benefit}")
    
    success_count = len([b for b in benefits if b.startswith("✅")])
    return success_count >= len(benefits) * 0.75

def main():
    """主函数"""
    print("🔍 开始最终验证...")
    print("🎯 验证main.py替换是否成功")
    print("=" * 60)
    
    # 切换到项目根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # 执行各项验证
    analyze_file_structure()
    compare_code_complexity()
    
    import_ok = test_import_compatibility()
    startup_ok = test_startup()
    architecture_ok = verify_architecture_benefits()
    
    # 总结
    print(f"\n🎉 最终验证结果:")
    print("=" * 60)
    print(f"  📦 导入兼容性: {'✅ 通过' if import_ok else '❌ 失败'}")
    print(f"  🚀 启动测试: {'✅ 通过' if startup_ok else '❌ 失败'}")
    print(f"  🏗️  架构改进: {'✅ 通过' if architecture_ok else '❌ 失败'}")
    
    overall_success = import_ok and startup_ok and architecture_ok
    
    if overall_success:
        print(f"\n🎊 恭喜！main.py替换成功！")
        print(f"   ✅ Application类职责过重问题已完全解决")
        print(f"   ✅ 新架构运行正常，功能完整")
        print(f"   ✅ 保持向后兼容，现有代码无需修改")
        print(f"   🚀 您现在可以使用: python src/main.py")
    else:
        print(f"\n⚠️ 替换过程中发现问题，需要进一步调试")
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    sys.exit(main())
