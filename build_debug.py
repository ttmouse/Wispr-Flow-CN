#!/usr/bin/env python3
# 简化的构建脚本，用于诊断闪退问题

import os
import sys
import shutil

def build_debug_app():
    """构建调试版本的应用程序"""
    print("构建调试版本...")
    
    # 清理旧的构建文件
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('FunASR.spec'):
        os.remove('FunASR.spec')
    
    # 简化的构建命令，排除大型依赖
    cmd = [
        'pyinstaller',
        '--clean',
        '--windowed',
        '--noconfirm',
        '--name=FunASR-Debug',
        '--debug=all',  # 启用调试模式
        '--console',    # 显示控制台以查看错误
    ]
    
    # 添加图标
    if os.path.exists('resources/icon.icns'):
        cmd.append('--icon=resources/icon.icns')
    
    # 只添加必要的数据文件
    cmd.extend([
        '--add-data=src/ui:src/ui',
        '--add-data=src/config.py:src',
        '--add-data=src/settings_manager.py:src',
        '--add-data=resources:resources',
    ])
    
    # 只添加基本的隐藏导入
    cmd.extend([
        '--hidden-import=PyQt6',
        '--hidden-import=PyQt6.QtCore',
        '--hidden-import=PyQt6.QtWidgets',
        '--hidden-import=PyQt6.QtGui',
        '--exclude-module=torch',      # 排除torch
        '--exclude-module=torchaudio', # 排除torchaudio
        '--exclude-module=funasr',     # 排除funasr
        '--exclude-module=numpy',      # 排除numpy
        '--exclude-module=pyaudio',    # 排除pyaudio
    ])
    
    cmd.append('src/main.py')
    
    print("执行命令:", ' '.join(cmd))
    result = os.system(' '.join(cmd))
    
    if result == 0:
        print("✓ 调试版本构建成功！")
        if sys.platform == 'darwin':
            print("应用位置: dist/FunASR-Debug.app")
            print("\n尝试运行调试版本:")
            print("./dist/FunASR-Debug.app/Contents/MacOS/FunASR-Debug")
        else:
            print("应用位置: dist/FunASR-Debug/")
    else:
        print("❌ 构建失败")
        return False
    
    return True

if __name__ == '__main__':
    build_debug_app()