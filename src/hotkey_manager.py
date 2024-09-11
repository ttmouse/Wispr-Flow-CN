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

    def stop_listening(self):
        if self.listener:
            self.listener.stop()

    def on_press(self, key):
        if key == keyboard.Key.alt:
            self.press_time = time.time()
            if self.on_press_callback:
                self.on_press_callback()

    def on_release(self, key):
        if key == keyboard.Key.alt:
            release_time = time.time()
            if self.press_time and (release_time - self.press_time) < self.min_record_time:
                time.sleep(self.min_record_time - (release_time - self.press_time))
            if self.on_release_callback:
                self.on_release_callback()

    def set_press_callback(self, callback):
        self.on_press_callback = callback

    def set_release_callback(self, callback):
        self.on_release_callback = callback