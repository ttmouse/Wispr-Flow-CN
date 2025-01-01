from pynput import keyboard
import time

class HotkeyManager:
    def __init__(self):
        self.press_callback = None
        self.release_callback = None
        self.listener = None
        self.other_keys_pressed = set()  # 记录当前按下的其他键
        self.option_pressed = False      # 记录 Option 键的状态

    def set_press_callback(self, callback):
        self.press_callback = callback

    def set_release_callback(self, callback):
        self.release_callback = callback

    def on_press(self, key):
        if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:  # Option 键
            self.option_pressed = True
            # 只有在没有其他键按下时才触发回调
            if not self.other_keys_pressed and self.press_callback:
                self.press_callback()
        else:
            # 记录其他按键
            self.other_keys_pressed.add(str(key))
            # 如果 Option 已经按下且正在录音，则停止录音
            if self.option_pressed and self.release_callback:
                self.release_callback()

    def on_release(self, key):
        if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
            self.option_pressed = False
            if self.release_callback:
                self.release_callback()
        else:
            # 移除释放的按键
            self.other_keys_pressed.discard(str(key))

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
            # 重置状态
            self.other_keys_pressed.clear()
            self.option_pressed = False