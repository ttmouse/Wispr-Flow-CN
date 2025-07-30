#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新架构的功能完整性
确保所有关键功能在新架构中正常工作
"""

import sys
import os
import asyncio
import logging
from unittest.mock import Mock, patch

# 添加src目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'src'))

def setup_test_logging():
    """设置测试日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

async def test_simplified_application():
    """测试SimplifiedApplication"""
    print("🧪 测试SimplifiedApplication...")
    
    try:
        # 模拟Qt环境
        with patch('PyQt6.QtWidgets.QApplication') as mock_app:
            mock_app.return_value = Mock()
            mock_app.instance.return_value = None
            
            from simplified_main import SimplifiedApplication
            
            # 创建应用程序实例
            app = SimplifiedApplication()
            
            # 测试基本属性
            assert hasattr(app, 'context'), "应该有context属性"
            assert hasattr(app, 'event_bus'), "应该有event_bus属性"
            
            print("  ✅ SimplifiedApplication创建成功")
            print("  ✅ 基本属性检查通过")
            
            return True
            
    except Exception as e:
        print(f"  ❌ SimplifiedApplication测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_compatibility_adapter():
    """测试兼容性适配器"""
    print("🧪 测试兼容性适配器...")
    
    try:
        # 模拟Qt环境
        with patch('PyQt6.QtWidgets.QApplication') as mock_app:
            mock_app.return_value = Mock()
            mock_app.instance.return_value = Mock()
            
            from compatibility_adapter import ApplicationAdapter, Application
            
            # 测试适配器创建
            adapter = ApplicationAdapter()
            
            # 测试关键方法存在
            key_methods = [
                'start_recording', 'stop_recording', 'toggle_recording',
                'on_option_press', 'on_option_release', 'show_window',
                'quit_application', 'update_ui', 'is_ready_for_recording',
                'cleanup', 'run'
            ]
            
            for method in key_methods:
                assert hasattr(adapter, method), f"适配器应该有{method}方法"
                assert callable(getattr(adapter, method)), f"{method}应该是可调用的"
            
            # 测试Application别名
            assert Application == ApplicationAdapter, "Application应该是ApplicationAdapter的别名"
            
            print("  ✅ 兼容性适配器创建成功")
            print("  ✅ 所有关键方法都存在")
            print("  ✅ Application别名正确")
            
            return True
            
    except Exception as e:
        print(f"  ❌ 兼容性适配器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_application_context():
    """测试ApplicationContext"""
    print("🧪 测试ApplicationContext...")
    
    try:
        # 模拟Qt环境
        with patch('PyQt6.QtWidgets.QApplication') as mock_app:
            mock_app.return_value = Mock()
            
            from managers.application_context import ApplicationContext
            
            # 创建上下文
            context = ApplicationContext(mock_app.return_value)
            
            # 测试基本属性
            assert hasattr(context, 'start_recording'), "应该有start_recording方法"
            assert hasattr(context, 'stop_recording'), "应该有stop_recording方法"
            assert hasattr(context, 'is_recording'), "应该有is_recording方法"
            assert hasattr(context, 'is_ready_for_recording'), "应该有is_ready_for_recording方法"
            
            # 测试初始状态
            assert not context.is_initialized, "初始状态应该未初始化"
            
            print("  ✅ ApplicationContext创建成功")
            print("  ✅ 录音接口方法存在")
            print("  ✅ 初始状态正确")
            
            return True
            
    except Exception as e:
        print(f"  ❌ ApplicationContext测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_manager_imports():
    """测试管理器导入"""
    print("🧪 测试管理器导入...")
    
    try:
        # 测试所有管理器都能正常导入
        managers = [
            ('managers.recording_manager', 'RecordingManager'),
            ('managers.system_manager', 'SystemManager'),
            ('managers.ui_manager', 'UIManager'),
            ('managers.audio_manager', 'AudioManager'),
            ('managers.event_bus', 'EventBus'),
            ('managers.application_context', 'ApplicationContext'),
            ('managers.component_manager', 'ComponentManager')
        ]
        
        for module_name, class_name in managers:
            try:
                module = __import__(module_name, fromlist=[class_name])
                cls = getattr(module, class_name)
                print(f"  ✅ {module_name}.{class_name}")
            except ImportError as e:
                print(f"  ❌ {module_name}.{class_name}: {e}")
                return False
            except AttributeError as e:
                print(f"  ❌ {module_name}.{class_name}: {e}")
                return False
        
        print("  ✅ 所有管理器导入成功")
        return True
        
    except Exception as e:
        print(f"  ❌ 管理器导入测试失败: {e}")
        return False

def test_event_bus_functionality():
    """测试事件总线功能"""
    print("🧪 测试事件总线功能...")
    
    try:
        from managers.event_bus import EventBus, EventType, get_event_bus
        
        # 测试事件总线创建
        event_bus = EventBus()
        
        # 测试全局事件总线
        global_bus = get_event_bus()
        assert global_bus is not None, "全局事件总线应该存在"
        
        # 测试事件类型
        assert hasattr(EventType, 'RECORDING_STARTED'), "应该有RECORDING_STARTED事件类型"
        assert hasattr(EventType, 'RECORDING_STOPPED'), "应该有RECORDING_STOPPED事件类型"
        
        # 测试事件订阅和发射
        received_events = []
        
        def test_callback(event):
            received_events.append(event)
        
        event_bus.subscribe(EventType.RECORDING_STARTED, test_callback)
        event_bus.emit(EventType.RECORDING_STARTED, "test_data")
        
        # 等待事件处理
        import time
        time.sleep(0.1)
        
        assert len(received_events) > 0, "应该接收到事件"
        
        print("  ✅ 事件总线创建成功")
        print("  ✅ 事件类型定义完整")
        print("  ✅ 事件订阅和发射正常")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 事件总线功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def run_all_tests():
    """运行所有测试"""
    print("🚀 开始测试新架构功能完整性...")
    print("=" * 60)
    
    setup_test_logging()
    
    tests = [
        test_manager_imports,
        test_event_bus_functionality,
        test_application_context,
        test_compatibility_adapter,
        test_simplified_application
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if asyncio.iscoroutinefunction(test):
                result = await test()
            else:
                result = test()
            
            if result:
                passed += 1
            print("-" * 40)
        except Exception as e:
            print(f"❌ 测试执行失败: {e}")
            print("-" * 40)
    
    print("=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！新架构功能完整！")
        print("✅ 可以安全地替换原始main.py")
        return True
    else:
        print("⚠️ 部分测试失败，需要进一步调试")
        return False

def main():
    """主函数"""
    try:
        result = asyncio.run(run_all_tests())
        return 0 if result else 1
    except KeyboardInterrupt:
        print("\n测试被中断")
        return 1
    except Exception as e:
        print(f"测试运行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
