#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试PyQt6中的事件类型值
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QEvent

def test_event_types():
    """测试事件类型值"""
    print("PyQt6事件类型测试")
    print("=" * 40)
    
    # 测试ApplicationActivate事件类型
    try:
        activate_type = QEvent.Type.ApplicationActivate
        print(f"ApplicationActivate事件类型: {activate_type} (值: {int(activate_type)})")
    except AttributeError:
        print("❌ ApplicationActivate事件类型不存在")
    
    # 测试其他可能的事件类型
    event_types = [
        'WindowActivate',
        'FocusIn', 
        'Show',
        'ApplicationStateChange',
        'ActivationChange'
    ]
    
    for event_name in event_types:
        try:
            event_type = getattr(QEvent.Type, event_name)
            print(f"{event_name}事件类型: {event_type} (值: {int(event_type)})")
        except AttributeError:
            print(f"❌ {event_name}事件类型不存在")
    
    # 列出所有可用的事件类型
    print("\n所有可用的事件类型:")
    print("-" * 30)
    
    event_attrs = [attr for attr in dir(QEvent.Type) if not attr.startswith('_')]
    for i, attr in enumerate(event_attrs[:20]):  # 只显示前20个
        try:
            event_type = getattr(QEvent.Type, attr)
            print(f"{attr}: {int(event_type)}")
        except:
            pass
    
    if len(event_attrs) > 20:
        print(f"... 还有 {len(event_attrs) - 20} 个事件类型")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    test_event_types()
    app.quit()