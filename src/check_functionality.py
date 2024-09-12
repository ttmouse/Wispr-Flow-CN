from audio_capture import AudioCapture
from funasr_engine import FunASREngine
from hotkey_manager import HotkeyManager
from clipboard_manager import ClipboardManager

def test_audio_capture():
    audio_capture = AudioCapture()
    audio_capture.start_recording()
    audio_data = audio_capture.read_audio()
    audio_capture.stop_recording()
    assert len(audio_data) > 0, "音频捕获失败"
    print("音频捕获测试通过")

def test_funasr_engine():
    engine = FunASREngine("path/to/model")
    result = engine.transcribe(b"dummy_audio_data")
    assert result is not None, "语音识别失败"
    print("语音识别测试通过")

def test_hotkey_manager():
    manager = HotkeyManager()
    manager.start_listening()
    manager.stop_listening()
    print("热键管理器测试通过")

def test_clipboard_manager():
    manager = ClipboardManager()
    test_text = "测试文本"
    manager.copy_to_clipboard(test_text)
    assert manager.get_clipboard_content() == test_text, "剪贴板操作失败"
    print("剪贴板管理器测试通过")

if __name__ == "__main__":
    try:
        test_audio_capture()
        test_funasr_engine()
        test_hotkey_manager()
        test_clipboard_manager()
        print("所有功能测试通过")
    except Exception as e:
        print(f"功能测试失败: {e}")