import numpy as np
from scipy.io import wavfile
import os

# 确保 resources 目录存在
if not os.path.exists('resources'):
    os.makedirs('resources')

# 生成开始音效（上升音）
def create_start_sound():
    sr = 44100  # 采样率
    duration = 0.15  # 持续时间
    t = np.linspace(0, duration, int(sr * duration))
    freq = np.linspace(440, 880, len(t))  # 从440Hz升到880Hz
    signal = np.sin(2 * np.pi * freq * t)
    fade = np.linspace(0, 1, len(signal))
    signal = signal * fade
    return (signal * 32767).astype(np.int16)

# 生成结束音效（下降音）
def create_stop_sound():
    sr = 44100
    duration = 0.15
    t = np.linspace(0, duration, int(sr * duration))
    freq = np.linspace(880, 440, len(t))  # 从880Hz降到440Hz
    signal = np.sin(2 * np.pi * freq * t)
    fade = np.linspace(1, 0, len(signal))
    signal = signal * fade
    return (signal * 32767).astype(np.int16)

# 创建音效文件
sr = 44100
wavfile.write("resources/start.wav", sr, create_start_sound())
wavfile.write("resources/stop.wav", sr, create_stop_sound())
print("✓ 音效文件已生成") 