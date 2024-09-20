import sys
print(f"Python 版本: {sys.version}")

print("导入 torch")
import torch
print(f"torch 版本: {torch.__version__}")

print("导入 funasr")
import funasr
print(f"funasr 版本: {funasr.__version__}")

print("导入 numpy")
import numpy
print(f"numpy 版本: {numpy.__version__}")

print("导入 pyaudio")
import pyaudio
print(f"pyaudio 版本: {pyaudio.__version__}")

print("导入 PyQt6")
from PyQt6 import QtCore
print(f"PyQt6 版本: {QtCore.PYQT_VERSION_STR}")

print("导入 PyInstaller")
import PyInstaller
print(f"PyInstaller 版本: {PyInstaller.__version__}")

print("导入 pynput")
import pynput
print("pynput 已成功导入（版本未知）")

print("导入 pyperclip")
import pyperclip
print(f"pyperclip 版本: {pyperclip.__version__}")

print("所有导入成功")