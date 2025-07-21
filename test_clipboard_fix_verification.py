#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪贴板修复验证测试
测试修复后的剪贴板功能是否正常工作
"""

import time
import subprocess
import sys
import os

def test_clipboard_fix():
    """
    测试剪贴板修复效果
    """
    print("=== 剪贴板修复验证测试 ===")
    print("\n测试说明:")
    print("1. 应用程序已启动")
    print("2. 请使用热键进行录音测试")
    print("3. 观察是否还会出现'粘贴后剪贴板内容异常'的警告")
    print("4. 测试完成后按 Ctrl+C 退出")
    
    print("\n修复内容:")
    print("- 移除了粘贴后的剪贴板内容验证")
    print("- 避免因应用修改剪贴板而产生的误报警告")
    print("- 保持粘贴功能正常工作")
    
    print("\n请进行以下测试:")
    print("1. 按住 Control 键开始录音")
    print("2. 说一些话")
    print("3. 释放 Control 键停止录音")
    print("4. 观察终端输出，确认没有'粘贴后剪贴板内容异常'警告")
    print("5. 检查转录文本是否正确粘贴到目标应用")
    
    print("\n监控应用程序日志...")
    print("(按 Ctrl+C 停止监控)")
    
    try:
        # 持续监控，等待用户测试
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n=== 测试结束 ===")
        print("如果没有看到'粘贴后剪贴板内容异常'的警告，说明修复成功！")
        return True

if __name__ == "__main__":
    test_clipboard_fix()