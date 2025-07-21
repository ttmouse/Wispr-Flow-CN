#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
录音稳定性测试脚本
用于验证改进后的录音功能是否更稳定
"""

import time
import threading
from src.hotkey_manager import HotkeyManager
from src.state_manager import StateManager
from src.audio_capture import AudioCapture

def test_recording_stability():
    """测试录音稳定性"""
    print("🎤 录音稳定性测试")
    print("=" * 50)
    print("此测试将模拟多次录音操作，观察稳定性")
    print("请在听到提示音后说话，每次录音持续3-5秒")
    print("\n按 Ctrl+C 可随时停止测试\n")
    
    # 统计数据
    total_tests = 0
    successful_recordings = 0
    failed_recordings = 0
    
    try:
        # 创建音频捕获实例
        audio_capture = AudioCapture()
        print(f"✓ 音频系统初始化成功")
        print(f"📊 当前参数: 阈值={audio_capture.volume_threshold:.5f}, 最少有效帧={audio_capture.min_valid_frames}, 最大静音帧={audio_capture.max_silence_frames}")
        
        # 进行10次录音测试
        for i in range(1, 11):
            total_tests += 1
            print(f"\n🔄 第 {i}/10 次测试")
            print("   请开始说话...")
            
            try:
                # 开始录音
                audio_capture.start_recording()
                start_time = time.time()
                
                # 录音5秒或直到检测到静音
                while time.time() - start_time < 5:
                    data = audio_capture.read_audio()
                    if data is None:  # 静音时间过长，自动停止
                        print("   ⏹️  检测到静音，自动停止录音")
                        break
                    time.sleep(0.032)  # 约30fps
                
                # 停止录音并获取数据
                audio_data = audio_capture.stop_recording()
                
                # 评估录音结果
                if len(audio_data) > 0:
                    duration = len(audio_data) / 16000  # 假设16kHz采样率
                    print(f"   ✅ 录音成功: {duration:.2f}秒, {len(audio_data)}样本")
                    print(f"   📈 有效帧: {audio_capture.valid_frame_count}, 静音帧: {audio_capture.silence_frame_count}")
                    successful_recordings += 1
                else:
                    print(f"   ❌ 录音失败: 未检测到有效音频")
                    print(f"   📉 有效帧: {audio_capture.valid_frame_count}, 静音帧: {audio_capture.silence_frame_count}")
                    failed_recordings += 1
                
            except Exception as e:
                print(f"   ❌ 录音过程出错: {e}")
                failed_recordings += 1
            
            # 清理数据，准备下次测试
            audio_capture.clear_recording_data()
            
            # 短暂休息
            if i < 10:
                print("   ⏳ 等待2秒后进行下次测试...")
                time.sleep(2)
        
        # 显示测试结果
        print("\n" + "=" * 50)
        print("📊 测试结果统计:")
        print(f"   总测试次数: {total_tests}")
        print(f"   成功录音: {successful_recordings} ({successful_recordings/total_tests*100:.1f}%)")
        print(f"   失败录音: {failed_recordings} ({failed_recordings/total_tests*100:.1f}%)")
        
        if successful_recordings >= 8:
            print("   🎉 录音稳定性: 优秀")
        elif successful_recordings >= 6:
            print("   👍 录音稳定性: 良好")
        elif successful_recordings >= 4:
            print("   ⚠️  录音稳定性: 一般")
        else:
            print("   ❌ 录音稳定性: 需要改进")
        
        # 给出建议
        print("\n💡 建议:")
        if failed_recordings > 2:
            print("   - 考虑进一步降低音量阈值")
            print("   - 检查麦克风设备状态")
            print("   - 确保录音环境相对安静")
        else:
            print("   - 当前参数设置较为合适")
            print("   - 可以正常使用录音功能")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        print(traceback.format_exc())
    
    finally:
        # 清理资源
        try:
            if 'audio_capture' in locals():
                audio_capture.cleanup()
                print("\n🧹 资源清理完成")
        except Exception as e:
            print(f"清理资源时出错: {e}")

def test_quick_responses():
    """测试快速响应能力"""
    print("\n⚡ 快速响应测试")
    print("=" * 50)
    print("测试短语音的检测能力")
    
    quick_phrases = [
        "是", "好的", "不行", "可以", "没问题", 
        "谢谢", "再见", "你好", "对的", "不对"
    ]
    
    successful = 0
    total = len(quick_phrases)
    
    try:
        audio_capture = AudioCapture()
        
        for i, phrase in enumerate(quick_phrases, 1):
            print(f"\n📝 {i}/{total}: 请快速说 '{phrase}'")
            input("   按回车开始录音...")
            
            try:
                audio_capture.start_recording()
                start_time = time.time()
                
                # 最多录音2秒
                while time.time() - start_time < 2:
                    data = audio_capture.read_audio()
                    if data is None:
                        break
                    time.sleep(0.032)
                
                audio_data = audio_capture.stop_recording()
                
                if len(audio_data) > 0:
                    print(f"   ✅ '{phrase}' - 检测成功")
                    successful += 1
                else:
                    print(f"   ❌ '{phrase}' - 检测失败")
                
                audio_capture.clear_recording_data()
                
            except Exception as e:
                print(f"   ❌ '{phrase}' - 出错: {e}")
        
        print(f"\n📊 快速响应测试结果: {successful}/{total} ({successful/total*100:.1f}%)")
        
    except Exception as e:
        print(f"❌ 快速响应测试失败: {e}")
    finally:
        try:
            if 'audio_capture' in locals():
                audio_capture.cleanup()
        except Exception as e:
            print(f"清理资源时出错: {e}")

def main():
    """主函数"""
    print("🔍 录音功能稳定性综合测试")
    print("=" * 60)
    print("此测试用于验证改进后的录音参数是否提高了稳定性")
    
    while True:
        print("\n请选择测试项目:")
        print("1. 录音稳定性测试 (推荐)")
        print("2. 快速响应测试")
        print("3. 退出")
        
        choice = input("\n请输入选择 (1-3): ").strip()
        
        if choice == "1":
            test_recording_stability()
        elif choice == "2":
            test_quick_responses()
        elif choice == "3":
            print("👋 测试结束")
            break
        else:
            print("❌ 无效选择，请重试")

if __name__ == "__main__":
    main()