from pynput import keyboard
import time
import logging

class HotkeyManager:
    def __init__(self):
        self.press_callback = None
        self.release_callback = None
        self.listener = None
        self.other_keys_pressed = set()  # 记录当前按下的其他键
        self.option_pressed = False      # 记录 Option 键的状态
        self.last_press_time = 0        # 记录最后一次按键时间

    def set_press_callback(self, callback):
        self.press_callback = callback

    def set_release_callback(self, callback):
        self.release_callback = callback

    def reset_state(self):
        """重置所有状态"""
        self.other_keys_pressed.clear()
        self.option_pressed = False
        self.last_press_time = 0

    def on_press(self, key):
        try:
            current_time = time.time()
            
            # 如果距离上次按键时间太久，重置状态
            if current_time - self.last_press_time > 5:  # 5秒无按键，重置状态
                self.reset_state()
            
            self.last_press_time = current_time
            
            if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:  # Option 键
                if not self.option_pressed:  # 防止重复触发
                    self.option_pressed = True
                    # 只有在没有其他键按下时才触发回调
                    if not self.other_keys_pressed and self.press_callback:
                        self.press_callback()
            else:
                # 记录其他按键
                key_str = str(key)
                if key_str not in self.other_keys_pressed:
                    self.other_keys_pressed.add(key_str)
                    # 如果 Option 已经按下且正在录音，则停止录音
                    if self.option_pressed and self.release_callback:
                        self.release_callback()
        
        except Exception as e:
            logging.error(f"处理按键按下事件失败: {e}")
            self.reset_state()  # 发生错误时重置状态

    def on_release(self, key):
        try:
            if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
                if self.option_pressed:  # 防止重复触发
                    self.option_pressed = False
                    if self.release_callback:
                        self.release_callback()
            else:
                # 移除释放的按键
                self.other_keys_pressed.discard(str(key))
        
        except Exception as e:
            logging.error(f"处理按键释放事件失败: {e}")
            self.reset_state()  # 发生错误时重置状态

    def start_listening(self):
        try:
            if not self.listener or not self.listener.is_alive():
                self.reset_state()  # 启动监听时重置状态
                self.listener = keyboard.Listener(
                    on_press=self.on_press,
                    on_release=self.on_release
                )
                self.listener.start()
                logging.info("热键监听器已启动")
        except Exception as e:
            logging.error(f"启动热键监听器失败: {e}")
            self.stop_listening()

    def stop_listening(self):
        try:
            if self.listener:
                self.listener.stop()
                self.listener = None
                self.reset_state()
                logging.info("热键监听器已停止")
        except Exception as e:
            logging.error(f"停止热键监听器失败: {e}")
        finally:
            self.reset_state()  # 确保状态被重置