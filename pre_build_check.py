import sys
import subprocess
import os
import importlib
import traceback
import logging
import shutil
import urllib.request

def check_dependencies():
    """检查所有依赖是否已安装"""
    with open('requirements.txt', 'r') as f:
        dependencies = f.read().splitlines()
    
    all_installed = True
    for package_name in dependencies:
        if not package_name.strip():  # 跳过空行
            continue
        package_name = package_name.split('==')[0].lower()  # 转换为小写
        if package_name == 'keyboard':
            logging.info("暂时跳过 keyboard 模块的检查")
            continue
        try:
            logging.info(f"正在检查 {package_name}")
            if package_name == 'pyaudio':
                import pyaudio
                module = pyaudio
            elif package_name == 'pyqt6':
                from PyQt6 import QtCore
                module = QtCore
            elif package_name == 'pyinstaller':
                import PyInstaller
                module = PyInstaller
            elif package_name == 'pynput':
                import pynput
                module = pynput
                version = "已安装（版本未知）"
            elif package_name == 'pyobjc-framework-avfoundation':
                import AVFoundation
                module = AVFoundation
                version = "已安装（版本未知）"
            else:
                module = importlib.import_module(package_name)
            try:
                version = module.__version__
            except AttributeError:
                version = "已安装（版本未知）"
            path = getattr(module, '__file__', '未知路径')
            logging.info(f"{package_name} 已安装 - 版本: {version}, 路径: {path}")
        except ImportError as e:
            logging.error(f"缺少依赖项: {package_name}")
            logging.error(f"导入错误: {e}")
            all_installed = False
        except Exception as e:
            logging.error(f"检查 {package_name} 时发生错误: {e}")
            logging.error(traceback.format_exc())
            all_installed = False
    
    return all_installed

def check_python_version():
    """检查 Python 版本"""
    print(f"当前 Python 版本: {sys.version}")
    if sys.version_info < (3, 6):
        raise RuntimeError("Python 3.6 或更高版本是必需的")
    print("Python 版本检查通过")

def check_portaudio():
    """检查 portaudio 是否已安装"""
    print("检查 portaudio...")
    try:
        subprocess.run(["brew", "list", "portaudio"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("portaudio 已安装")
    except subprocess.CalledProcessError:
        print("portaudio 安装，请使用 'brew install portaudio' 安装")
        sys.exit(1)

def check_resources():
    required_resources = [
        'app_icon.icns',
        # 'models' 行已被移除
    ]
    
    for resource in required_resources:
        try:
            if not os.path.exists(resource):
                print(f"缺少资源: {resource}")
                return False
            else:
                print(f"资源存在: {resource}")
        except Exception as e:
            print(f"检查资源 {resource} 时发生错误: {e}")
            print(traceback.format_exc())
            return False
    
    return True

def check_file_permissions():
    """检查关键文件的读写权限"""
    critical_files = [
        'main.py',
        'requirements.txt',
        'app_icon.icns',
        # 添加其他关键文件
    ]
    
    for file in critical_files:
        if os.path.exists(file):
            if os.access(file, os.R_OK):
                print(f"{file} 可读")
            else:
                print(f"警告：{file} 不可读")
            
            if os.access(file, os.W_OK):
                print(f"{file} 可写")
            else:
                print(f"警告：{file} 不可写")
        else:
            print(f"错误：{file} 不存在")

# 在 __main__ 中调用此函数
check_file_permissions()

def check_disk_space():
    """检查磁盘空间是否足够"""
    total, used, free = shutil.disk_usage("/")
    print(f"总磁盘空间: {total // (2**30)} GB")
    print(f"已使用空间: {used // (2**30)} GB")
    print(f"可用空间: {free // (2**30)} GB")
    
    if free < 5 * (2**30):  # 如果可用空间小于5GB
        print("警告：可用磁盘空间不足5GB，可能影响打包过程")

# 在 __main__ 中调用此函数
check_disk_space()

def check_network_connection():
    """检查网络连接"""
    try:
        urllib.request.urlopen('http://www.baidu.com', timeout=3)
        print("网络连接正常")
    except urllib.error.URLError:
        print("警告：网络连接异常，可能影响依赖项下载")

# 在 __main__ 中调用此函数
check_network_connection()

def check_environment_variables():
    """检查关键环境变量"""
    critical_vars = [
        'PATH',
        'PYTHONPATH',
        # 添加其他关键环境变量
    ]
    
    for var in critical_vars:
        value = os.environ.get(var)
        if value:
            print(f"{var} 已设置: {value}")
        else:
            print(f"警告：{var} 未设置")

# 在 __main__ 中调用此函数
check_environment_variables()

def check_pyinstaller():
    """检查PyInstaller是否正确安装"""
    try:
        import PyInstaller
        print(f"PyInstaller 版本: {PyInstaller.__version__}")
    except ImportError:
        print("错误：PyInstaller 未安装，请使用 pip install pyinstaller 安装")

# 在 __main__ 中调用此函数
check_pyinstaller()

if __name__ == "__main__":
    print("开始环境检查...")
    print(f"当前 Python 路径: {sys.executable}")
    print(f"当前工作目录: {os.getcwd()}")
    try:
        check_python_version()
        print("Python 版本检查完成")
        check_portaudio()
        print("PortAudio 检查完成")
        dependencies_ok = check_dependencies()
        print("依赖项检查完成")
        print("开始检查资源...")
        try:
            resources_ok = check_resources()
            print("资源检查完成")
        except Exception as e:
            print(f"资源检查失败: {e}")
            print(traceback.format_exc())
            resources_ok = False
        if dependencies_ok and resources_ok:
            print("所有依赖检查通过，环境准备就绪。")
        else:
            print("环境检查未通过，请解决上述问题。")
    except Exception as e:
        print(f"环境检查失败: {e}")
        print(traceback.format_exc())
    print("环境检查完成。")