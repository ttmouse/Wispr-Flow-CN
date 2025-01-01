from pynput import keyboard
import time

class HotkeyManager:
    def __init__(self):
        self.press_callback = None
        self.release_callback = None
        self.listener = None

    def set_press_callback(self, callback):
        self.press_callback = callback

    def set_release_callback(self, callback):
        self.release_callback = callback

    def on_press(self, key):
        if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:  # 检测 Option 键（在 macOS 上是 Alt 键）
            if self.press_callback:
                self.press_callback()

    def on_release(self, key):
        if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
            if self.release_callback:
                self.release_callback()

    def start_listening(self):
        if not self.listener:
            self.listener = keyboard.Listener(
                on_press=self.on_press,
                on_release=self.on_release
            )
            self.listener.start()

    def stop_listening(self):
        if self.listener:
            self.listener.stop()
            self.listener = None