#!/usr/bin/env python3
"""
调试测试脚本
"""
import sys
import os

# 添加src目录到Python路径
src_dir = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_dir)

def test_imports():
    """测试导入"""
    try:
        print("🔧 测试基本导入...")
        
        # 测试基本导入
        import logging
        print("✅ logging导入成功")
        
        # 测试PyQt6导入
        from PyQt6.QtWidgets import QApplication
        print("✅ PyQt6导入成功")
        
        # 测试managers导入
        from managers.loading_manager_wrapper import LoadingManagerWrapper
        print("✅ LoadingManagerWrapper导入成功")
        
        # 测试main模块导入
        import main
        print("✅ main模块导入成功")
        
        print("🎉 所有导入测试成功！")
        return True
        
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_syntax():
    """测试语法"""
    try:
        print("🔧 测试语法...")
        
        # 编译main.py
        import py_compile
        py_compile.compile('src/main.py', doraise=True)
        print("✅ main.py语法正确")
        
        # 编译LoadingManagerWrapper
        py_compile.compile('src/managers/loading_manager_wrapper.py', doraise=True)
        print("✅ LoadingManagerWrapper语法正确")
        
        print("🎉 所有语法测试成功！")
        return True
        
    except Exception as e:
        print(f"❌ 语法错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 开始诊断测试...")
    
    # 测试语法
    if not test_syntax():
        sys.exit(1)
    
    # 测试导入
    if not test_imports():
        sys.exit(1)
    
    print("✅ 所有测试通过！")
