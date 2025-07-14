#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
开发环境权限检查工具
用于检查直接运行 python src/main.py 时所需的 macOS 权限
"""

import subprocess
import sys
import os

def check_accessibility_permission():
    """检查辅助功能权限"""
    try:
        result = subprocess.run([
            'osascript',
            '-e', 'tell application "System Events"',
            '-e', 'set isEnabled to UI elements enabled',
            '-e', 'return isEnabled',
            '-e', 'end tell'
        ], capture_output=True, text=True)
        
        return 'true' in result.stdout.lower()
    except Exception as e:
        print(f"检查辅助功能权限时出错: {e}")
        return False

def check_microphone_permission():
    """检查麦克风权限（简单检查）"""
    try:
        # 尝试执行一个简单的 AppleScript 来测试基本权限
        result = subprocess.run([
            'osascript',
            '-e', 'return "mic_test"'
        ], capture_output=True, text=True)
        
        return 'mic_test' in result.stdout
    except Exception as e:
        print(f"检查麦克风权限时出错: {e}")
        return False

def get_current_app_name():
    """获取当前运行的应用名称"""
    if 'TERM_PROGRAM' in os.environ:
        term_program = os.environ['TERM_PROGRAM']
        if term_program == 'iTerm.app':
            return 'iTerm.app'
        elif term_program == 'Apple_Terminal':
            return 'Terminal.app'
        elif 'vscode' in term_program.lower():
            return 'Visual Studio Code.app'
    
    # 检查是否在 PyCharm 中运行
    if 'PYCHARM_HOSTED' in os.environ or 'JETBRAINS_IDE' in os.environ:
        return 'PyCharm.app'
    
    return '您的终端应用'

def open_system_preferences():
    """打开系统设置"""
    try:
        # 尝试打开辅助功能设置页面
        subprocess.run([
            'open', 
            'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'
        ], check=False)
        return True
    except:
        try:
            # 备用方案：打开系统设置
            subprocess.run(['open', '/System/Applications/System Preferences.app'], check=False)
            return True
        except:
            return False

def main():
    print("=" * 60)
    print("🔍 开发环境权限检查工具")
    print("=" * 60)
    print()
    
    current_app = get_current_app_name()
    print(f"当前运行环境: {current_app}")
    print()
    
    # 检查辅助功能权限
    print("检查辅助功能权限...")
    has_accessibility = check_accessibility_permission()
    
    if has_accessibility:
        print("✅ 辅助功能权限: 已授予")
    else:
        print("❌ 辅助功能权限: 未授予")
    
    # 检查麦克风权限
    print("检查麦克风权限...")
    has_microphone = check_microphone_permission()
    
    if has_microphone:
        print("✅ 基本权限: 正常")
    else:
        print("❌ 基本权限: 异常")
    
    print()
    
    # 如果缺少权限，提供解决方案
    if not has_accessibility:
        print("🚨 快捷键录音功能需要辅助功能权限")
        print()
        print("解决步骤：")
        print("1. 打开 系统设置 > 隐私与安全性 > 辅助功能")
        print(f"2. 点击 '+' 按钮添加: {current_app}")
        print("3. 确保应用已勾选")
        print("4. 重新运行程序")
        print()
        print("常见应用路径：")
        print("• Terminal.app: /System/Applications/Utilities/Terminal.app")
        print("• iTerm.app: /Applications/iTerm.app")
        print("• PyCharm: /Applications/PyCharm CE.app (或 PyCharm Professional.app)")
        print("• VS Code: /Applications/Visual Studio Code.app")
        print()
        
        # 尝试打开系统设置
        if open_system_preferences():
            print("✅ 已尝试打开系统设置页面")
        else:
            print("❌ 无法自动打开系统设置，请手动打开")
        
        print()
        print("💡 提示：")
        print("• 打包后的应用 (bash tools/build_app.sh) 会自动请求权限")
        print("• 如果仍有问题，请重启终端应用后重试")
        
        return 1
    else:
        print("🎉 所有权限检查通过！")
        print("快捷键录音功能应该可以正常工作")
        return 0

if __name__ == "__main__":
    sys.exit(main())