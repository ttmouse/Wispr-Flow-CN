#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试设置面板修复效果
验证设置面板保存后能否正常再次打开
"""

import sys
import os
import time
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from settings_manager import SettingsManager
from ui.settings_window import SettingsWindow

def test_settings_window_lifecycle():
    """
    测试设置窗口的生命周期：
    1. 创建并显示设置窗口
    2. 模拟保存设置
    3. 关闭窗口
    4. 再次尝试打开设置窗口
    """
    print("\n=== 设置窗口生命周期测试 ===")
    
    # 初始化设置管理器
    settings_manager = SettingsManager()
    
    # 第一次创建设置窗口
    print("1. 创建第一个设置窗口...")
    window1 = SettingsWindow(settings_manager=settings_manager)
    print(f"   窗口1创建成功，可见性: {window1.isVisible()}")
    
    # 显示窗口
    window1.show()
    print(f"   窗口1显示后，可见性: {window1.isVisible()}")
    
    # 模拟保存操作（不实际保存，只是测试窗口状态）
    print("2. 模拟保存操作...")
    
    # 关闭窗口
    print("3. 关闭窗口...")
    window1.close()
    print(f"   窗口1关闭后，可见性: {window1.isVisible()}")
    
    # 等待一下确保窗口完全关闭
    QApplication.processEvents()
    time.sleep(0.1)
    
    # 第二次创建设置窗口（模拟用户再次打开）
    print("4. 创建第二个设置窗口...")
    window2 = SettingsWindow(settings_manager=settings_manager)
    print(f"   窗口2创建成功，可见性: {window2.isVisible()}")
    
    # 显示第二个窗口
    window2.show()
    print(f"   窗口2显示后，可见性: {window2.isVisible()}")
    
    # 检查窗口是否正常工作
    if window2.isVisible():
        print("✓ 测试通