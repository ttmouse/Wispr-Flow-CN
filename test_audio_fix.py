#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试音频停止清理错误修复
"""

import sys
import os
import time
import numpy as np

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from audio_capture import AudioCapture

def test_audio_capture_fix():
    """测试音频捕获修复"""
    print("🧪 开始测试音频停止清理错误修复...")
    
    try:
        # 创建音频捕获实例
        audio_capture = AudioCapture()
        print("✓ 音频捕获实例创建成功")
        
        # 测试1: 正常录音和停止
        print("\n📝 测试1: 正常录音和停止")
        audio_capture.start_recording()
        print("✓ 开始录音")
        
        # 模拟短时间录音
        time.sleep(1)
        
        # 停止录音
        result = audio_capture.stop_recording()
        print(f"✓ 停止录音成功，返回数据类型: {type(result)}, 长度: {len(result)}")
        
        # 测试2: 测试计数器类型
        print("\n📝 测试2: 检查计数器类型")
        print(f"valid_frame_count 类型: {type(audio_capture.valid_frame_count)}, 值: {audio_capture.valid_frame_count}")
        print(f"silence_frame_count 类型: {type(audio_capture.silence_frame_count)}, 值: {audio_capture.silence_frame_count}")
        print(f"min_valid_frames 类型: {type(audio_capture.min_valid_frames)}, 值: {audio_capture.min_valid_frames}")
        print(f"max_silence_frames 类型: {type(audio_capture.max_silence_frames)}, 值: {audio_capture.max_silence_frames}")
        
        # 测试3: 测试比较操作
        print("\n📝 测试3: 测试比较操作")
        try:
            # 测试有效帧数比较
            valid_count = int(audio_capture.valid_frame_count) if hasattr(audio_capture.valid_frame_count, '__len__') else audio_capture.valid_frame_count
            min_valid = int(audio_capture.min_valid_frames) if hasattr(audio_capture.min_valid_frames, '__len__') else audio_capture.min_valid_frames
            comparison_result = valid_count < min_valid
            print(f"✓ 有效帧数比较成功: {valid_count} < {min_valid} = {comparison_result}")
            
            # 测试静音帧数比较
            silence_count = int(audio_capture.silence_frame_count) if hasattr(audio_capture.silence_frame_count, '__len__') else audio_capture.silence_frame_count
            max_silence = int(audio_capture.max_silence_frames) if hasattr(audio_capture.max_silence_frames, '__len__') else audio_capture.max_silence_frames
            comparison_result2 = silence_count >= max_silence
            print(f"✓ 静音帧数比较成功: {silence_count} >= {max_silence} = {comparison_result2}")
            
        except Exception as e:
            print(f"❌ 比较操作失败: {e}")
            return False
        
        # 测试4: 测试多次录音停止
        print("\n📝 测试4: 测试多次录音停止")
        for i in range(3):
            try:
                audio_capture.start_recording()
                time.sleep(0.5)
                result = audio_capture.stop_recording()
                print(f"✓ 第{i+1}次录音停止成功")
            except Exception as e:
                print(f"❌ 第{i+1}次录音停止失败: {e}")
                return False
        
        # 清理资源
        audio_capture.cleanup()
        print("✓ 资源清理成功")
        
        print("\n🎉 所有测试通过！音频停止清理错误已修复")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_audio_capture_fix()
    if success:
        print("\n✅ 修复验证成功")
        sys.exit(0)
    else:
        print("\n❌ 修复验证失败")
        sys.exit(1)