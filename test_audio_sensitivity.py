#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频敏感度测试脚本
用于测试改进后的音频检测参数
"""

import sys
import os
import time
import numpy as np
from src.audio_capture import AudioCapture

def test_audio_sensitivity():
    """测试音频敏感度"""
    print("🎤 音频敏感度测试")
    print("=" * 50)
    
    try:
        # 创建音频捕获实例
        audio_capture = AudioCapture()
        print(f"✓ 音频系统初始化成功")
        print(f"📊 当前参数:")
        print(f"   音量阈值: {audio_capture.volume_threshold:.5f}")
        print(f"   最少有效帧: {audio_capture.min_valid_frames}")
        print(f"   最大静音帧: {audio_capture.max_silence_frames}")
        
        # 测试不同音量阈值
        test_thresholds = [0.0005, 0.001, 0.002, 0.003, 0.005]
        
        for threshold in test_thresholds:
            print(f"\n🔧 测试阈值: {threshold:.5f}")
            audio_capture.volume_threshold = threshold
            
            # 进行5秒录音测试
            print("   请说话进行测试（5秒）...")
            
            try:
                audio_capture.start_recording()
                start_time = time.time()
                
                while time.time() - start_time < 5:
                    data = audio_capture.read_audio()
                    if data is None:  # 静音时间过长
                        break
                    time.sleep(0.032)  # 约30fps
                
                # 获取录音结果
                audio_data = audio_capture.stop_recording()
                
                if len(audio_data) > 0:
                    print(f"   ✅ 检测到音频: {len(audio_data)} 样本")
                    print(f"   📈 有效帧数: {audio_capture.valid_frame_count}")
                else:
                    print(f"   ❌ 未检测到有效音频")
                    print(f"   📉 有效帧数: {audio_capture.valid_frame_count}")
                
            except Exception as e:
                print(f"   ❌ 录音测试失败: {e}")
            
            # 清理数据准备下次测试
            audio_capture.clear_recording_data()
            time.sleep(1)
        
        # 推荐最佳阈值
        print("\n" + "=" * 50)
        print("📋 测试总结:")
        print("   建议根据测试结果选择合适的阈值")
        print("   - 0.0005: 极高敏感度（可能有噪音干扰）")
        print("   - 0.001:  高敏感度（推荐）")
        print("   - 0.002:  中等敏感度")
        print("   - 0.003:  原始设置")
        print("   - 0.005:  低敏感度（需要大声说话）")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(traceback.format_exc())
    
    finally:
        # 清理资源
        try:
            if 'audio_capture' in locals():
                audio_capture.cleanup()
        except Exception as e:
            print(f"清理资源时出错: {e}")

def test_real_time_monitoring():
    """实时音量监控测试"""
    print("\n🎤 实时音量监控测试")
    print("=" * 50)
    print("说话时观察音量变化，按 Ctrl+C 停止")
    
    try:
        audio_capture = AudioCapture()
        audio_capture.start_recording()
        
        frame_count = 0
        while True:
            data = audio_capture.read_audio()
            if data:
                # 计算当前音量
                audio_data = np.frombuffer(data, dtype=np.float32)
                volume = np.sqrt(np.mean(np.square(audio_data)))
                
                frame_count += 1
                if frame_count % 10 == 0:  # 每10帧显示一次
                    bar_length = int(volume * 10000)  # 音量条
                    bar = "█" * min(bar_length, 50)
                    print(f"\r音量: {volume:.5f} |{bar:<50}|", end="", flush=True)
            
            time.sleep(0.032)
            
    except KeyboardInterrupt:
        print("\n\n✓ 监控已停止")
    except Exception as e:
        print(f"\n❌ 监控失败: {e}")
    finally:
        try:
            if 'audio_capture' in locals():
                audio_capture.cleanup()
        except Exception as e:
            print(f"清理资源时出错: {e}")

def test_quick_speech():
    """快速语音测试"""
    print("\n🎤 快速语音测试")
    print("=" * 50)
    print("测试短词汇识别能力")
    
    test_words = ["是", "好", "不", "对", "行", "可以", "没问题"]
    
    try:
        audio_capture = AudioCapture()
        
        for word in test_words:
            print(f"\n请说: '{word}' (3秒内)")
            input("按回车开始录音...")
            
            audio_capture.start_recording()
            start_time = time.time()
            
            while time.time() - start_time < 3:
                data = audio_capture.read_audio()
                if data is None:
                    break
                time.sleep(0.032)
            
            audio_data = audio_capture.stop_recording()
            
            if len(audio_data) > 0:
                print(f"   ✅ '{word}' - 检测成功 ({len(audio_data)} 样本)")
            else:
                print(f"   ❌ '{word}' - 检测失败")
            
            audio_capture.clear_recording_data()
            time.sleep(0.5)
        
    except Exception as e:
        print(f"❌ 快速语音测试失败: {e}")
    finally:
        try:
            if 'audio_capture' in locals():
                audio_capture.cleanup()
        except Exception as e:
            print(f"清理资源时出错: {e}")

def main():
    """主函数"""
    print("🔍 音频敏感度综合测试")
    print("=" * 60)
    
    while True:
        print("\n请选择测试项目:")
        print("1. 音频敏感度测试")
        print("2. 实时音量监控")
        print("3. 快速语音测试")
        print("4. 退出")
        
        choice = input("\n请输入选择 (1-4): ").strip()
        
        if choice == "1":
            test_audio_sensitivity()
        elif choice == "2":
            test_real_time_monitoring()
        elif choice == "3":
            test_quick_speech()
        elif choice == "4":
            print("👋 测试结束")
            break
        else:
            print("❌ 无效选择，请重试")

if __name__ == "__main__":
    main()