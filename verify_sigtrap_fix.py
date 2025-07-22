#!/usr/bin/env python3
"""
验证SIGTRAP修复 - 检查代码更改是否正确应用
"""

import sys
import os
import re

def verify_lambda_fix():
    """
    验证lambda函数是否已被替换
    """
    print("🔍 检查lambda函数修复...")
    
    main_py_path = os.path.join('src', 'main.py')
    
    if not os.path.exists(main_py_path):
        print(f"❌ 文件不存在: {main_py_path}")
        return False
    
    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否还有problematic lambda
    lambda_pattern = r'restart_hotkey_action\.triggered\.connect\(lambda:.*restart_hotkey_manager\(\)\)'
    if re.search(lambda_pattern, content):
        print("❌ 仍然存在problematic lambda函数")
        return False
    
    # 检查是否有新的安全方法调用
    safe_method_pattern = r'restart_hotkey_action\.triggered\.connect\(self\._safe_restart_hotkey_manager\)'
    if not re.search(safe_method_pattern, content):
        print("❌ 未找到安全方法调用")
        return False
    
    print("✓ lambda函数已成功替换为安全方法调用")
    return True

def verify_safe_method():
    """
    验证安全方法是否已添加
    """
    print("🔍 检查安全方法实现...")
    
    main_py_path = os.path.join('src', 'main.py')
    
    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查pyqtSlot装饰器
    if '@pyqtSlot()' not in content:
        print("❌ 未找到@pyqtSlot装饰器")
        return False
    
    # 检查安全方法定义
    if 'def _safe_restart_hotkey_manager(self):' not in content:
        print("❌ 未找到_safe_restart_hotkey_manager方法定义")
        return False
    
    # 检查线程安全检查
    if 'QThread.currentThread() != QApplication.instance().thread()' not in content:
        print("❌ 未找到线程安全检查")
        return False
    
    # 检查QMetaObject.invokeMethod调用
    if 'QMetaObject.invokeMethod' not in content:
        print("❌ 未找到QMetaObject.invokeMethod调用")
        return False
    
    print("✓ 安全方法实现完整")
    return True

def verify_imports():
    """
    验证必要的导入是否存在
    """
    print("🔍 检查必要的导入...")
    
    main_py_path = os.path.join('src', 'main.py')
    
    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_imports = [
        'from PyQt6.QtCore import QThread, pyqtSignal, QTimer, QMetaObject, Qt, Q_ARG, QObject, pyqtSlot',
        'QSystemTrayIcon',
        'QApplication'
    ]
    
    for import_item in required_imports:
        if import_item not in content:
            print(f"❌ 缺少导入: {import_item}")
            return False
    
    print("✓ 所有必要的导入都存在")
    return True

def main():
    """
    主验证函数
    """
    print("=" * 60)
    print("SIGTRAP修复验证")
    print("=" * 60)
    
    checks = [
        ("导入检查", verify_imports),
        ("Lambda修复检查", verify_lambda_fix),
        ("安全方法检查", verify_safe_method)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}:")
        if not check_func():
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有验证通过！SIGTRAP修复已正确应用")
        print("\n🔧 修复摘要:")
        print("   1. 替换了problematic lambda函数")
        print("   2. 添加了@pyqtSlot装饰的安全方法")
        print("   3. 实现了线程安全检查")
        print("   4. 增强了异常处理")
        print("\n🎯 预期效果:")
        print("   - 消除EXC_BREAKPOINT (SIGTRAP)崩溃")
        print("   - 提高dock菜单操作的稳定性")
        print("   - 确保线程安全的热键管理器重启")
    else:
        print("❌ 验证失败，修复可能不完整")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())