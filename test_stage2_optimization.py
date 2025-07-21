#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第二阶段优化验证测试
测试局部重构的效果
"""

import time
import threading
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_unified_exception_handling():
    """测试统一异常处理装饰器"""
    print("\n=== 测试统一异常处理 ===")
    
    try:
        from main import handle_common_exceptions
        
        # 创建测试类来模拟实例方法
        class TestClass:
            @handle_common_exceptions(show_error=False)
            def test_method(self):
                raise FileNotFoundError("测试文件未找到错误")
            
            @handle_common_exceptions(show_error=False)
            def normal_method(self):
                return "正常执行"
        
        test_obj = TestClass()
        
        # 测试异常处理
        result1 = test_obj.test_method()
        result2 = test_obj.normal_method()
        
        print(f"✓ 异常方法返回: {result1}")
        print(f"✓ 正常方法返回: {result2}")
        print("✓ 异常处理装饰器工作正常")
        return True
    except Exception as e:
        print(f"❌ 异常处理测试失败: {e}")
        return False

def test_component_status_check():
    """测试统一组件状态检查"""
    print("\n=== 测试组件状态检查 ===")
    
    try:
        from main import Application
        
        # 创建模拟组件
        class MockComponent:
            def __init__(self, ready=True):
                self.is_ready = ready
                self.running = True
            
            def check_status(self):
                return self.is_ready
        
        # 模拟应用实例
        app = type('MockApp', (), {})()
        app.mock_component = MockComponent(True)
        app.none_component = None
        
        # 绑定方法
        from main import Application
        app.is_component_ready = Application.is_component_ready.__get__(app)
        
        # 测试各种状态检查
        tests = [
            ("存在的组件", lambda: app.is_component_ready('mock_component')),
            ("不存在的组件", lambda: app.is_component_ready('none_component')),
            ("方法检查", lambda: app.is_component_ready('mock_component', 'check_status')),
            ("属性检查", lambda: app.is_component_ready('mock_component', 'is_ready')),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                print(f"✓ {test_name}: {result}")
                results.append(result)
            except Exception as e:
                print(f"❌ {test_name} 失败: {e}")
                results.append(False)
        
        # 验证结果
        expected = [True, False, True, True]
        if results == expected:
            print("✓ 组件状态检查功能正常")
            return True
        else:
            print(f"❌ 结果不符合预期: {results} != {expected}")
            return False
            
    except Exception as e:
        print(f"❌ 组件状态检查测试失败: {e}")
        return False

def test_simplified_initialization():
    """测试简化的初始化流程"""
    print("\n=== 测试简化初始化流程 ===")
    
    try:
        # 检查新的初始化方法是否存在
        from main import Application
        
        required_methods = [
            'initialize_components',
            '_check_permissions_async',
            '_initialize_funasr_engine',
            '_initialize_core_components',
            '_finalize_initialization',
            '_mark_initialization_complete'
        ]
        
        missing_methods = []
        for method in required_methods:
            if not hasattr(Application, method):
                missing_methods.append(method)
        
        if missing_methods:
            print(f"❌ 缺少方法: {missing_methods}")
            return False
        
        print("✓ 所有初始化方法都已实现")
        return True
        
    except Exception as e:
        print(f"❌ 初始化流程测试失败: {e}")
        return False

def test_ui_event_optimization():
    """测试UI事件处理优化"""
    print("\n=== 测试UI事件处理优化 ===")
    
    try:
        # 检查UI事件处理方法的简化
        from ui.main_window import MainWindow
        
        # 检查拖动事件处理方法
        required_methods = [
            '_handle_title_bar_mouse_press',
            '_handle_title_bar_mouse_move',
            '_handle_title_bar_mouse_release'
        ]
        
        missing_methods = []
        for method in required_methods:
            if not hasattr(MainWindow, method):
                missing_methods.append(method)
        
        if missing_methods:
            print(f"❌ 缺少UI事件处理方法: {missing_methods}")
            return False
        
        print("✓ UI事件处理方法已优化")
        return True
        
    except Exception as e:
        print(f"❌ UI事件处理测试失败: {e}")
        return False

def test_performance_improvements():
    """测试性能改进"""
    print("\n=== 测试性能改进 ===")
    
    try:
        # 测试组件状态检查性能
        from main import Application
        
        class MockApp:
            def __init__(self):
                self.test_component = type('TestComponent', (), {'is_ready': True})()
            
            def is_component_ready(self, component_name, check_method=None):
                return Application.is_component_ready(self, component_name, check_method)
        
        app = MockApp()
        
        # 性能测试
        start_time = time.time()
        for _ in range(1000):
            app.is_component_ready('test_component', 'is_ready')
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"✓ 1000次状态检查耗时: {duration:.4f}秒")
        
        if duration < 0.1:  # 应该在100ms内完成
            print("✓ 状态检查性能良好")
            return True
        else:
            print(f"⚠️ 状态检查性能可能需要优化: {duration:.4f}秒")
            return False
            
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        return False

def main():
    """运行所有第二阶段优化测试"""
    print("🔧 第二阶段优化验证测试")
    print("=" * 50)
    
    tests = [
        ("统一异常处理", test_unified_exception_handling),
        ("组件状态检查", test_component_status_check),
        ("简化初始化流程", test_simplified_initialization),
        ("UI事件处理优化", test_ui_event_optimization),
        ("性能改进", test_performance_improvements),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 第二阶段优化验证成功！")
        print("\n✅ 优化成果:")
        print("   • 统一了异常处理机制")
        print("   • 简化了组件状态检查")
        print("   • 优化了初始化流程")
        print("   • 简化了UI事件处理")
        print("   • 提升了整体性能")
    else:
        print(f"⚠️ 部分测试未通过，需要进一步优化")
    
    return passed == total

if __name__ == "__main__":
    main()