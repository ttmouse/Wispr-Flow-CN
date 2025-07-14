import numpy as np
from scipy.io import wavfile
import os

# 确保 resources 目录存在
if not os.path.exists('resources'):
    os.makedirs('resources')

# 生成开始音效（上升音）
def create_start_sound():
    sr = 44100  # 采样率
    duration = 0.1  # 缩短持续时间
    t = np.linspace(0, duration, int(sr * duration))
    
    # 使用固定相位的正弦波
    freq = np.linspace(440, 880, len(t))  # 从440Hz升到880Hz
    phase = 0  # 固定相位
    signal = np.sin(2 * np.pi * freq * t + phase)
    
    # 使用更平滑的淡入淡出
    fade_samples = int(sr * 0.02)  # 20ms的淡入淡出
    fade_in = np.linspace(0, 1, fade_samples)
    fade_out = np.linspace(1, 0, fade_samples)
    fade = np.ones(len(signal))
    fade[:fade_samples] = fade_in
    fade[-fade_samples:] = fade_out
    
    # 应用淡入淡出并归一化
    signal = signal * fade
    signal = signal / np.max(np.abs(signal))  # 归一化到[-1,1]
    
    # 转换为16位整数
    return (signal * 32767).astype(np.int16)

# 生成结束音效（下降音）
def create_stop_sound():
    sr = 44100
    duration = 0.1  # 缩短持续时间
    t = np.linspace(0, duration, int(sr * duration))
    
    # 使用固定相位的正弦波
    freq = np.linspace(880, 440, len(t))  # 从880Hz降到440Hz
    phase = 0  # 固定相位
    signal = np.sin(2 * np.pi * freq * t + phase)
    
    # 使用更平滑的淡入淡出
    fade_samples = int(sr * 0.02)  # 20ms的淡入淡出
    fade_in = np.linspace(0, 1, fade_samples)
    fade_out = np.linspace(1, 0, fade_samples)
    fade = np.ones(len(signal))
    fade[:fade_samples] = fade_in
    fade[-fade_samples:] = fade_out
    
    # 应用淡入淡出并归一化
    signal = signal * fade
    signal = signal / np.max(np.abs(signal))  # 归一化到[-1,1]
    
    # 转换为16位整数
    return (signal * 32767).astype(np.int16)

# 创建音效文件
sr = 44100
wavfile.write("resources/start.wav", sr, create_start_sound())
wavfile.write("resources/stop.wav", sr, create_stop_sound())
print("✓ 音效文件已生成")