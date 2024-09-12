import sys
import pkg_resources

def check_dependencies():
    """检查所有依赖是否已安装"""
    print("开始检查依赖...")
    with open('requirements.txt', 'r') as f:
        requirements = f.read().splitlines()
    
    for requirement in requirements:
        print(f"检查依赖: {requirement}")
        pkg_resources.require(requirement)
    print("依赖检查完成")

def check_python_version():
    """检查 Python 版本"""
    print(f"当前 Python 版本: {sys.version}")
    if sys.version_info < (3, 6):
        raise RuntimeError("Python 3.6 或更高版本是必需的")
    print("Python 版本检查通过")

if __name__ == "__main__":
    print("开始环境检查...")
    try:
        check_python_version()
        check_dependencies()
        print("所有依赖检查通过，环境准备就绪。")
    except Exception as e:
        print(f"环境检查失败: {e}")
        sys.exit(1)