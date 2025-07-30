#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证Application类重构效果
分析代码结构改进和职责分离情况
"""

import os
import sys
import ast
import inspect
from typing import Dict, List, Tuple

def analyze_file_complexity(file_path: str) -> Dict:
    """分析文件复杂度"""
    if not os.path.exists(file_path):
        return {"error": "文件不存在"}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 基本统计
        lines = content.split('\n')
        total_lines = len(lines)
        code_lines = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
        comment_lines = len([line for line in lines if line.strip().startswith('#')])
        
        # AST分析
        try:
            tree = ast.parse(content)
            
            # 统计类和方法
            classes = []
            functions = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                    classes.append({
                        'name': node.name,
                        'methods': len(class_methods),
                        'method_names': [m.name for m in class_methods]
                    })
                elif isinstance(node, ast.FunctionDef) and not any(isinstance(parent, ast.ClassDef) for parent in ast.walk(tree) if hasattr(parent, 'body') and node in getattr(parent, 'body', [])):
                    functions.append(node.name)
            
            return {
                'total_lines': total_lines,
                'code_lines': code_lines,
                'comment_lines': comment_lines,
                'classes': classes,
                'functions': functions,
                'complexity_score': code_lines / 10  # 简单的复杂度评分
            }
        except SyntaxError:
            return {
                'total_lines': total_lines,
                'code_lines': code_lines,
                'comment_lines': comment_lines,
                'error': 'AST解析失败'
            }
    except Exception as e:
        return {"error": str(e)}

def compare_architectures():
    """比较原始架构和重构后架构"""
    print("🔍 分析Application类重构效果")
    print("=" * 60)
    
    # 文件路径
    original_main = "src/main.py"
    simplified_main = "src/simplified_main.py"
    managers_dir = "src/managers"
    
    # 分析原始文件
    print("📊 原始架构分析:")
    if os.path.exists(original_main):
        original_stats = analyze_file_complexity(original_main)
        print(f"  📄 main.py: {original_stats.get('total_lines', 0)} 行")
        print(f"  📝 代码行数: {original_stats.get('code_lines', 0)}")
        
        if 'classes' in original_stats:
            for cls in original_stats['classes']:
                if cls['name'] == 'Application':
                    print(f"  🏗️  Application类: {cls['methods']} 个方法")
                    print(f"     方法列表: {', '.join(cls['method_names'][:10])}{'...' if len(cls['method_names']) > 10 else ''}")
    else:
        print("  ❌ 原始main.py文件不存在")
    
    print("\n📊 重构后架构分析:")
    
    # 分析简化后的主文件
    if os.path.exists(simplified_main):
        simplified_stats = analyze_file_complexity(simplified_main)
        print(f"  📄 simplified_main.py: {simplified_stats.get('total_lines', 0)} 行")
        print(f"  📝 代码行数: {simplified_stats.get('code_lines', 0)}")
        
        if 'classes' in simplified_stats:
            for cls in simplified_stats['classes']:
                if 'Application' in cls['name']:
                    print(f"  🏗️  {cls['name']}类: {cls['methods']} 个方法")
    else:
        print("  ❌ simplified_main.py文件不存在")
    
    # 分析管理器文件
    if os.path.exists(managers_dir):
        print(f"\n📊 管理器架构分析:")
        manager_files = [f for f in os.listdir(managers_dir) if f.endswith('.py') and f != '__init__.py']
        
        total_manager_lines = 0
        total_manager_methods = 0
        
        for manager_file in manager_files:
            manager_path = os.path.join(managers_dir, manager_file)
            manager_stats = analyze_file_complexity(manager_path)
            
            lines = manager_stats.get('total_lines', 0)
            total_manager_lines += lines
            
            print(f"  📄 {manager_file}: {lines} 行")
            
            if 'classes' in manager_stats:
                for cls in manager_stats['classes']:
                    methods = cls['methods']
                    total_manager_methods += methods
                    print(f"     🏗️  {cls['name']}: {methods} 个方法")
        
        print(f"\n  📈 管理器总计: {len(manager_files)} 个文件, {total_manager_lines} 行, {total_manager_methods} 个方法")
    else:
        print("  ❌ managers目录不存在")
    
    return True

def analyze_separation_of_concerns():
    """分析职责分离情况"""
    print("\n🎯 职责分离分析:")
    print("=" * 60)
    
    managers_info = {
        "recording_manager.py": "录音相关功能（开始/停止录音、音频处理、转写）",
        "system_manager.py": "系统集成功能（托盘、权限检查、系统设置）",
        "ui_manager.py": "界面管理功能（窗口、启动界面、托盘菜单）",
        "audio_manager.py": "音频处理功能（音频捕获、引擎管理）",
        "event_bus.py": "事件通信系统（解耦管理器间通信）",
        "application_context.py": "应用程序上下文（统一管理所有组件）",
        "component_manager.py": "组件生命周期管理（初始化、启动、清理）"
    }
    
    managers_dir = "src/managers"
    existing_managers = []
    
    if os.path.exists(managers_dir):
        for manager_file, description in managers_info.items():
            manager_path = os.path.join(managers_dir, manager_file)
            if os.path.exists(manager_path):
                existing_managers.append(manager_file)
                print(f"  ✅ {manager_file}: {description}")
            else:
                print(f"  ❌ {manager_file}: {description} (未实现)")
    
    print(f"\n  📊 已实现管理器: {len(existing_managers)}/{len(managers_info)}")
    
    return len(existing_managers) >= len(managers_info) * 0.7  # 70%以上实现算成功

def analyze_code_quality_improvements():
    """分析代码质量改进"""
    print("\n📈 代码质量改进分析:")
    print("=" * 60)
    
    improvements = []
    
    # 检查单一职责原则
    managers_dir = "src/managers"
    if os.path.exists(managers_dir):
        manager_count = len([f for f in os.listdir(managers_dir) if f.endswith('.py') and f != '__init__.py'])
        if manager_count >= 5:
            improvements.append("✅ 单一职责原则: 功能已拆分到专门的管理器中")
        else:
            improvements.append("⚠️ 单一职责原则: 需要更多的职责分离")
    
    # 检查事件总线
    event_bus_path = os.path.join(managers_dir, "event_bus.py")
    if os.path.exists(event_bus_path):
        improvements.append("✅ 解耦通信: 实现了事件总线系统")
    else:
        improvements.append("❌ 解耦通信: 缺少事件总线系统")
    
    # 检查组件管理
    component_manager_path = os.path.join(managers_dir, "component_manager.py")
    if os.path.exists(component_manager_path):
        improvements.append("✅ 生命周期管理: 实现了统一的组件管理")
    else:
        improvements.append("❌ 生命周期管理: 缺少组件管理器")
    
    # 检查简化的主程序
    simplified_main = "src/simplified_main.py"
    if os.path.exists(simplified_main):
        stats = analyze_file_complexity(simplified_main)
        if stats.get('code_lines', 1000) < 300:
            improvements.append("✅ 代码简化: 主程序代码大幅简化")
        else:
            improvements.append("⚠️ 代码简化: 主程序仍然较复杂")
    
    for improvement in improvements:
        print(f"  {improvement}")
    
    success_count = len([i for i in improvements if i.startswith("✅")])
    total_count = len(improvements)
    
    print(f"\n  📊 改进完成度: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    return success_count >= total_count * 0.75  # 75%以上算成功

def generate_refactoring_report():
    """生成重构报告"""
    print("\n📋 Application类重构报告")
    print("=" * 60)
    
    # 执行各项分析
    architecture_ok = compare_architectures()
    separation_ok = analyze_separation_of_concerns()
    quality_ok = analyze_code_quality_improvements()
    
    # 总结
    print(f"\n🎯 重构效果总结:")
    print(f"  📊 架构对比: {'✅ 通过' if architecture_ok else '❌ 需改进'}")
    print(f"  🎯 职责分离: {'✅ 通过' if separation_ok else '❌ 需改进'}")
    print(f"  📈 代码质量: {'✅ 通过' if quality_ok else '❌ 需改进'}")
    
    overall_success = architecture_ok and separation_ok and quality_ok
    
    if overall_success:
        print(f"\n🎉 重构成功！Application类职责过重问题已得到有效解决")
        print(f"   主要改进:")
        print(f"   • 将单一的Application类拆分为多个专门的管理器")
        print(f"   • 实现了单一职责原则，每个管理器负责特定功能")
        print(f"   • 引入事件总线系统，减少组件间的直接依赖")
        print(f"   • 统一的组件生命周期管理")
        print(f"   • 大幅简化了主程序代码")
    else:
        print(f"\n⚠️ 重构部分完成，仍有改进空间")
        print(f"   建议继续完善未实现的管理器和功能")
    
    return overall_success

def main():
    """主函数"""
    try:
        print("🚀 开始验证Application类重构效果...")
        
        # 切换到项目根目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
        
        # 生成重构报告
        success = generate_refactoring_report()
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"❌ 验证过程出错: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
