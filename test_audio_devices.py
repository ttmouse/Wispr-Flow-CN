#!/usr/bin/env python3
"""
测试音频设备加载功能
"""

import sys
import os

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

def test_audio_devices():
    """测试音频设备获取"""
    print("🧪 测试音频设备获取...")
    
    try:
        import pyaudio
        
        print("✅ PyAudio 可用")
        
        p = pyaudio.PyAudio()
        device_count = p.get_device_count()
        print(f"📱 检测到 {device_count} 个音频设备")
        
        input_devices = []
        for i in range(device_count):
            try:
                device_info = p.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:  # 输入设备
                    input_devices.append({
                        'index': i,
                        'name': device_info['name'],
                        'channels': device_info['maxInputChannels'],
                        'sample_rate': device_info['defaultSampleRate']
                    })
                    print(f"  🎤 {device_info['name']} (通道: {device_info['maxInputChannels']})")
            except Exception as e:
                print(f"  ❌ 设备 {i} 信息获取失败: {e}")
        
        p.terminate()
        
        print(f"\n✅ 找到 {len(input_devices)} 个输入设备")
        return input_devices
        
    except ImportError:
        print("❌ PyAudio 不可用")
        return []
    except Exception as e:
        print(f"❌ 音频设备检测失败: {e}")
        return []

def test_settings_audio_devices():
    """测试设置窗口中的音频设备加载"""
    print("\n🧪 测试设置窗口音频设备加载...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from settings_manager import SettingsManager
        from ui.settings_window import MacOSSettingsWindow
        
        # 创建应用程序（不显示窗口）
        app = QApplication(sys.argv)
        
        # 创建设置管理器
        settings_manager = SettingsManager()
        
        # 创建设置窗口
        settings_window = MacOSSettingsWindow(
            settings_manager=settings_manager,
            audio_capture=None
        )
        
        # 检查设备下拉框
        if hasattr(settings_window, 'input_device_combo'):
            device_count = settings_window.input_device_combo.count()
            print(f"✅ 设置窗口创建成功")
            print(f"📱 下拉框中有 {device_count} 个设备选项:")
            
            for i in range(device_count):
                device_name = settings_window.input_device_combo.itemText(i)
                print(f"  {i}: {device_name}")
            
            # 测试刷新功能
            print("\n🔄 测试刷新功能...")
            settings_window._load_audio_devices()
            
            new_device_count = settings_window.input_device_combo.count()
            print(f"📱 刷新后有 {new_device_count} 个设备选项:")
            
            for i in range(new_device_count):
                device_name = settings_window.input_device_combo.itemText(i)
                print(f"  {i}: {device_name}")
                
        else:
            print("❌ 设置窗口中没有找到 input_device_combo")
        
        return True
        
    except Exception as e:
        print(f"❌ 设置窗口测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🔧 音频设备测试开始...")
    print("=" * 50)
    
    # 1. 测试直接的音频设备获取
    devices = test_audio_devices()
    
    # 2. 测试设置窗口中的音频设备加载
    success = test_settings_audio_devices()
    
    print("\n" + "=" * 50)
    print("🔧 测试完成")
    
    if success and devices:
        print("✅ 所有测试通过")
    else:
        print("❌ 部分测试失败")

if __name__ == "__main__":
    main()
