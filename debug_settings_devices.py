#!/usr/bin/env python3
"""
调试设置窗口中的音频设备问题
"""

import sys
import os
from PyQt6.QtWidgets import QApplication

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

def debug_settings_window():
    """调试设置窗口"""
    print("🔍 调试设置窗口音频设备问题...")
    
    try:
        # 创建应用程序
        app = QApplication(sys.argv)
        
        # 导入设置管理器和设置窗口
        from settings_manager import SettingsManager
        from ui.settings_window import MacOSSettingsWindow
        
        # 创建设置管理器
        settings_manager = SettingsManager()
        
        print("✅ 设置管理器创建成功")
        
        # 尝试创建audio_capture（模拟实际应用程序的情况）
        audio_capture = None
        try:
            # 这里模拟实际应用程序中可能传递的audio_capture
            print("🔍 检查audio_capture参数...")
            print(f"audio_capture: {audio_capture}")
        except Exception as e:
            print(f"⚠️ audio_capture检查失败: {e}")
        
        # 创建设置窗口
        print("🔍 创建设置窗口...")
        settings_window = MacOSSettingsWindow(
            settings_manager=settings_manager,
            audio_capture=audio_capture
        )
        
        print("✅ 设置窗口创建成功")
        
        # 检查是否有input_device_combo属性
        if hasattr(settings_window, 'input_device_combo'):
            print("✅ 找到input_device_combo属性")
            
            # 检查初始状态
            initial_count = settings_window.input_device_combo.count()
            print(f"📱 初始设备数量: {initial_count}")
            
            for i in range(initial_count):
                device_name = settings_window.input_device_combo.itemText(i)
                print(f"  {i}: {device_name}")
            
            # 手动调用_load_audio_devices并捕获异常
            print("\n🔍 手动调用_load_audio_devices...")
            try:
                settings_window._load_audio_devices()
                print("✅ _load_audio_devices调用成功")
                
                # 检查调用后的状态
                after_count = settings_window.input_device_combo.count()
                print(f"📱 调用后设备数量: {after_count}")
                
                for i in range(after_count):
                    device_name = settings_window.input_device_combo.itemText(i)
                    print(f"  {i}: {device_name}")
                    
            except Exception as e:
                print(f"❌ _load_audio_devices调用失败: {e}")
                import traceback
                traceback.print_exc()
            
            # 测试直接的pyaudio调用
            print("\n🔍 测试直接pyaudio调用...")
            try:
                import pyaudio
                p = pyaudio.PyAudio()
                device_count = p.get_device_count()
                print(f"📱 PyAudio检测到 {device_count} 个设备")
                
                input_devices = []
                for i in range(device_count):
                    try:
                        device_info = p.get_device_info_by_index(i)
                        if device_info['maxInputChannels'] > 0:
                            input_devices.append(device_info['name'])
                            print(f"  🎤 {device_info['name']}")
                    except Exception as e:
                        print(f"  ❌ 设备 {i} 获取失败: {e}")
                
                p.terminate()
                print(f"✅ 找到 {len(input_devices)} 个输入设备")
                
                # 手动添加到下拉框
                print("\n🔍 手动添加设备到下拉框...")
                settings_window.input_device_combo.clear()
                settings_window.input_device_combo.addItem("系统默认")
                
                for device_name in input_devices:
                    settings_window.input_device_combo.addItem(device_name)
                    print(f"  ➕ 添加: {device_name}")
                
                final_count = settings_window.input_device_combo.count()
                print(f"📱 最终设备数量: {final_count}")
                
            except Exception as e:
                print(f"❌ 直接pyaudio调用失败: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("❌ 没有找到input_device_combo属性")
        
        # 显示窗口进行实际测试
        print("\n💡 显示设置窗口进行实际测试...")
        settings_window.show()
        
        # 运行应用程序
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_settings_window()
