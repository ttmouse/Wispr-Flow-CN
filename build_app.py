import PyInstaller.__main__
import os

# 获取当前脚本所在的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 设置打包参数
params = [
    'src/main.py',  # 您的主脚本
    '--name=语音转文字',  # 应用程序名称
    '--onefile',  # 打包成单个可执行文件
    '--windowed',  # 使用 GUI 模式，不显示控制台
    f'--add-data={os.path.join(current_dir, "src")}:src',  # 添加 src 目录
    '--icon=app_icon.ico',  # 应用程序图标（如果有的话）
    '--noconsole',  # 不显示控制台窗口
]

# 运行 PyInstaller
PyInstaller.__main__.run(params)