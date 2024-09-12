from pynput import keyboard
import time

class HotkeyManager:
    def __init__(self):
        self.listener = None
        self.on_press_callback = None
        self.on_release_callback = None
        self.press_time = None
        self.min_record_time = 0.5  # 最小录音时间（秒）

    def start_listening(self):
        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release)
        self.listener.start()
        print("热键监听器已启动")

    def stop_listening(self):
        if self.listener:
            self.listener.stop()
            print("热键监听器已停止")

    def on_press(self, key):
        try:
            if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
                print("Option 键被按下")
                self.press_time = time.time()
                if self.on_press_callback:
                    self.on_press_callback()
        except Exception as e:
            print(f"按键处理出错: {e}")

    def on_release(self, key):
        try:
            if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
                print("Option 键被释放")
                release_time = time.time()
                if self.press_time and (release_time - self.press_time) < self.min_record_time:
                    time.sleep(self.min_record_time - (release_time - self.press_time))
                if self.on_release_callback:
                    self.on_release_callback()
        except Exception as e:
            print(f"按键释放处理出错: {e}")

    def set_press_callback(self, callback):
        self.on_press_callback = callback
        print("按键回调已设置")

    def set_release_callback(self, callback):
        self.on_release_callback = callback
        print("释放回调已设置")