import os
import sys
import shutil
import time
from pathlib import Path

def force_remove(path):
    """强制删除文件或目录"""
    max_retries = 3
    for i in range(max_retries):
        try:
            if os.path.isfile(path):
                os.unlink(path)
            elif os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
            return True
        except Exception as e:
            if i == max_retries - 1:
                print(f"❌ 无法删除 {path}: {e}")
                return False
            print(f"重试删除 {path}...")
            time.sleep(1)
    return False

def clean_build():
    """清理构建目录"""
    print("清理构建目录...")
    dirs_to_clean = ['build', 'dist']
    files_to_clean = ['FunASR.spec']
    
    # 先尝试结束可能占用文件的进程
    if sys.platform == 'darwin':
        os.system("pkill -f FunASR.app")
    else:
        os.system("taskkill /f /im FunASR.exe")
    
    time.sleep(1)  # 等待进程完全结束
    
    # 清理目录
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"删除目录: {dir_name}")
            force_remove(dir_name)
            
    # 清理文件
    for file_name in files_to_clean:
        if os.path.exists(file_name):
            print(f"删除文件: {file_name}")
            force_remove(file_name)

def build_app():
    """构建应用程序"""
    print("开始构建应用程序...")
    
    # 检查必要文件
    if not os.path.exists('src/main.py'):
        print("❌ 找不到主程序文件: src/main.py")
        sys.exit(1)
    
    # 检查资源目录
    if not os.path.exists('resources'):
        os.makedirs('resources')
        print("✓ 已创建 resources 目录")
    
    # 构建命令
    cmd = [
        'pyinstaller',
        '--clean',
        '--windowed',  # macOS上不显示控制台窗口
        '--noconfirm',
        '--name=FunASR',
    ]
    
    # 根据平台选择图标
    if sys.platform == 'darwin':
        if os.path.exists('resources/icon.icns'):
            cmd.append('--icon=resources/icon.icns')
        else:
            print("⚠️ 未找到 icon.icns，将使用默认图标")
    else:
        if os.path.exists('resources/icon.ico'):
            cmd.append('--icon=resources/icon.ico')
        else:
            print("⚠️ 未找到 icon.ico，将使用默认图标")
    
    # 添加其他参数
    cmd.extend([
        '--add-data=src:src',  # 添加源代码
        '--add-data=resources:resources',  # 添加资源文件
        '--hidden-import=PyQt6',
        '--hidden-import=pyaudio',
        '--hidden-import=numpy',
        '--collect-all=funasr',  # 收集所有 funasr 相关文件
        '--exclude-module=PyQt5',  # 排除 PyQt5
        '--exclude-module=PySide6',  # 排除 PySide6
        'src/main.py'  # 主程序入口
    ])
    
    # 执行构建
    print("执行命令:", ' '.join(cmd))
    result = os.system(' '.join(cmd))
    if result != 0:
        print("❌ PyInstaller 构建失败")
        sys.exit(1)
    
    # 检查构建结果
    if sys.platform == 'darwin':
        app_path = 'dist/FunASR.app'
        # 复制配置文件
        if os.path.exists('Info.plist'):
            contents_dir = os.path.join(app_path, 'Contents')
            if not os.path.exists(contents_dir):
                os.makedirs(contents_dir)
            shutil.copy2('Info.plist', contents_dir)
            print("✓ 已添加 Info.plist")
            
        # 复制权限配置
        if os.path.exists('entitlements.plist'):
            print("✓ 使用 entitlements.plist 签名应用")
            os.system(f'codesign --force --deep --entitlements entitlements.plist --sign - "{app_path}"')
        else:
            print("⚠️ 未找到 entitlements.plist，使用默认签名")
            os.system(f'codesign --force --deep --sign - "{app_path}"')
    else:
        app_path = 'dist/FunASR'
        
    if os.path.exists(app_path):
        print(f"✓ 构建成功！应用程序位于: {app_path}")
        print("\n注意：需要手动复制模型文件到以下位置：")
        if sys.platform == 'darwin':
            print(f"- {app_path}/Contents/MacOS/models/")
        else:
            print(f"- {app_path}/models/")
    else:
        print("❌ 构建失败！")
        sys.exit(1)

def main():
    try:
        # 确保在正确的目录
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # 清理旧的构建文件
        clean_build()
        
        # 构建应用程序
        build_app()
        
        print("\n构建完成！")
        print("你现在可以：")
        if sys.platform == 'darwin':
            print("1. 直接运行 dist/FunASR.app")
            print("2. 将 FunASR.app 拖到应用程序文件夹")
        else:
            print("1. 直接运行 dist/FunASR/FunASR.exe")
            print("2. 创建桌面快捷方式")
            
    except Exception as e:
        print(f"❌ 构建过程出错: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()