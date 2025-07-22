import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio_capture import AudioCapture
from funasr_engine import FunASREngine
from hotkey_manager import HotkeyManager

import numpy as np

def check_audio_capture():
    print("检查音频捕获功能...")
    audio_capture = AudioCapture()
    audio_capture.start_recording()
    # 录制2秒钟的音频
    import time
    time.sleep(2)
    audio_data = audio_capture.stop_recording()
    print(f"捕获的音频数据长度: {len(audio_data)}")
    return len(audio_data) > 0

def check_funasr_engine():
    print("检查FunASR引擎...")
    from download_model import download_funasr_model
    model_dir = download_funasr_model()
    engine = FunASREngine(model_dir)
    # 使用一个简单的音频数据进行测试
    test_audio = np.zeros(16000, dtype=np.float32)  # 1秒的静音，使用 NumPy 数组
    result = engine.transcribe(test_audio)
    print(f"转写结果: {result}")
    return result is not None

def check_hotkey_manager():
    print("检查热键管理器...")
    hotkey_manager = HotkeyManager()
    # 这里只能检查初始化，无法完全测试全局热键功能
    return hotkey_manager is not None



def run_checks():
    checks = [
        ("音频捕获", check_audio_capture),
        ("FunASR引擎", check_funasr_engine),
        ("热键管理器", check_hotkey_manager)
    ]

    all_passed = True
    for name, check_func in checks:
        try:
            result = check_func()
            status = "通过" if result else "失败"
        except Exception as e:
            status = f"错误: {str(e)}"
            result = False
        print(f"{name}检查 {status}")
        all_passed = all_passed and result

    if all_passed:
        print("所有检查都通过了！")
    else:
        print("有些检查未通过，请查看上面的详细信息。")

if __name__ == "__main__":
    run_checks()