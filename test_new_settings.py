#!/usr/bin/env python3
"""
测试新的设置面板
"""

import sys
import os
from PyQt6.QtWidgets import QApplication

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

def test_settings_window():
    """测试设置窗口"""
    print("🧪 测试新的设置面板...")
    
    try:
        # 创建应用程序
        app = QApplication(sys.argv)
        
        # 导入设置管理器和设置窗口
        from settings_manager import SettingsManager
        from ui.settings_window import MacOSSettingsWindow
        
        # 创建设置管理器
        settings_manager = SettingsManager()
        
        # 创建设置窗口
        settings_window = MacOSSettingsWindow(
            settings_manager=settings_manager,
            audio_capture=None
        )
        
        print("✅ 新设置面板创建成功")
        print("✅ 设置窗口已显示")
        print("💡 请在窗口中测试各项功能，然后关闭窗口")
        
        # 显示窗口
        settings_window.show()
        
        # 运行应用程序
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_settings_window()
