#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试NumPy数组错误修复
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from audio_capture import AudioCapture
from funasr_engine import FunASREngine
import time
import numpy as np

def test_audio_capture():
    """测试音频捕获是否还有NumPy数组错误"""
    print("开始测试音频捕获...")
    
    try:
        # 初始化音频捕获
        audio_capture = AudioCapture()
        print("✓ 音频捕获初始化成功")
        
        # 开始录音
        audio_capture.start_recording()
        print("✓ 开始录音")
        
        # 录音2秒
        time.sleep(2)
        
        # 停止录音
        result = audio_capture.stop_recording()
        print(f"✓ 停止录音成功，结果类型: {type(result)}")
        
        if isinstance(result, np.ndarray):
            print(f"✓ 录音数据长度: {len(result)}")
            print(f"✓ 录音数据类型: {result.dtype}")
        
        return True
        
    except Exception as e:
        print(f"❌ 音频捕获测试失败: {e}")
        return False

def test_funasr_preprocessing():
    """测试FunASR预处理是否还有NumPy数组错误"""
    print("\n开始测试FunASR预处理...")
    
    try:
        # 创建测试音频数据
        test_audio = np.random.random(16000).astype(np.float32)  # 1秒的测试音频
        print("✓ 创建测试音频数据")
        
        # 初始化FunASR引擎
        engine = FunASREngine()
        print("✓ FunASR引擎初始化成功")
        
        # 测试预处理
        processed_audio = engine.preprocess_audio(test_audio)
        print(f"✓ 预处理成功，结果类型: {type(processed_audio)}")
        print(f"✓ 预处理后数据长度: {len(processed_audio)}")
        
        return True
        
    except Exception as e:
        print(f"❌ FunASR预处理测试失败: {e}")
        return False

if __name__ == "__main__":
    print("=== NumPy数组错误修复测试 ===")
    
    # 测试音频捕获
    audio_test_passed = test_audio_capture()
    
    # 测试FunASR预处理
    funasr_test_passed = test_funasr_preprocessing()
    
    # 总结测试结果
    print("\n=== 测试结果 ===")
    print(f"音频捕获测试: {'✓ 通过' if audio_test_passed else '❌ 失败'}")
    print(f"FunASR预处理测试: {'✓ 通过' if funasr_test_passed else '❌ 失败'}")
    
    if audio_test_passed and funasr_test_passed:
        print("\n🎉 所有测试通过！NumPy数组错误已修复")
    else:
        print("\n⚠️ 部分测试失败，可能仍存在问题")