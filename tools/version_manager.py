#!/usr/bin/env python3
"""版本管理脚本"""
import os
import re
from datetime import datetime

def read_version(config_path):
    """读取当前版本号"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'APP_VERSION = ["\'](.+?)["\']', content)
            if match:
                return match.group(1)
    except Exception as e:
        print(f"读取版本号失败: {e}")
    return "1.0.0"

def increment_version(version):
    """增加版本号"""
    major, minor, patch = map(int, version.split('.'))
    patch += 1
    if patch > 99:
        patch = 0
        minor += 1
        if minor > 99:
            minor = 0
            major += 1
    return f"{major}.{minor}.{patch}"

def update_version(config_path):
    """更新版本号"""
    current_version = read_version(config_path)
    new_version = increment_version(current_version)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 更新版本号
        new_content = re.sub(
            r'APP_VERSION = ["\'](.+?)["\']',
            f'APP_VERSION = "{new_version}"',
            content
        )
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        # 记录版本更新
        with open('docs/version_history.md', 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"\n## v{new_version} ({timestamp})\n")
            f.write("- 版本更新\n")
        
        print(f"✓ 版本已更新: {current_version} -> {new_version}")
        return new_version
    except Exception as e:
        print(f"❌ 更新版本号失败: {e}")
        return current_version

if __name__ == '__main__':
    # 获取项目根目录
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(root_dir, 'src', 'config.py')
    update_version(config_path) 