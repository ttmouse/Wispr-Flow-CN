import PyInstaller.__main__
import os

# 获取当前脚本的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 设置应用程序图标路径（如果有的话）
# icon_path = os.path.join(current_dir, 'icon.ico')

PyInstaller.__main__.run([
    'src/main.py',
    '--name=FunASR语音转文字',
    '--onefile',
    '--windowed',
    # f'--icon={icon_path}',  # 如果有图标的话
    '--add-data=src:src',
    '--hidden-import=funasr',
    '--hidden-import=PyQt6',
    '--hidden-import=pyaudio',
    '--hidden-import=pynput',
    '--hidden-import=pyperclip',
    '--hidden-import=numpy',
])