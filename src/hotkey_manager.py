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
        self.is_recording = False       # 记录是否正在录音

    def set_press_callback(self, callback):
        self.press_callback = callback

    def set_release_callback(self, callback):
        self.release_callback = callback

    def reset_state(self):
        """重置所有状态"""
        self.other_keys_pressed.clear()
        self.option_pressed = False
        self.is_recording = False
        # 不重置时间，避免误触发重置
        logging.info("热键状态已重置")

    def on_press(self, key):
        """处理按键按下事件"""
        try:
            current_time = time.time()
            self.last_press_time = current_time
            
            # 记录按键
            key_str = str(key)
            
            if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:  # Option 键
                if not self.option_pressed:  # 防止重复触发
                    self.option_pressed = True
                    # 只在没有其他键按下且未在录音时开始录音
                    if not self.other_keys_pressed and not self.is_recording and self.press_callback:
                        try:
                            self.is_recording = True
                            self.press_callback()
                        except Exception as e:
                            logging.error(f"按键回调执行失败: {e}")
            else:
                # 记录其他按键
                if key_str not in self.other_keys_pressed:
                    self.other_keys_pressed.add(key_str)
                    # 如果正在录音，则停止录音
                    if self.is_recording and self.release_callback:
                        try:
                            self.release_callback()
                            self.is_recording = False
                        except Exception as e:
                            logging.error(f"释放回调执行失败: {e}")
            
            logging.debug(f"按键状态 - Option: {self.option_pressed}, 其他键: {self.other_keys_pressed}, 录音: {self.is_recording}")
        
        except Exception as e:
            logging.error(f"处理按键按下事件失败: {e}")
            # 不在异常时重置状态，避免状态丢失

    def on_release(self, key):
        """处理按键释放事件"""
        try:
            key_str = str(key)
            
            if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
                if self.option_pressed:  # 防止重复触发
                    self.option_pressed = False
                    # 如果正在录音，则停止录音
                    if self.is_recording and self.release_callback:
                        try:
                            self.release_callback()
                            self.is_recording = False
                        except Exception as e:
                            logging.error(f"释放回调执行失败: {e}")
            else:
                # 移除释放的按键
                self.other_keys_pressed.discard(key_str)
            
            logging.debug(f"释放按键 - Option: {self.option_pressed}, 其他键: {self.other_keys_pressed}, 录音: {self.is_recording}")
        
        except Exception as e:
            logging.error(f"处理按键释放事件失败: {e}")
            # 不在异常时重置状态，避免状态丢失

    def start_listening(self):
        """启动热键监听"""
        try:
            if not self.listener or not self.listener.is_alive():
                self.reset_state()  # 启动监听时重置状态
                self.listener = keyboard.Listener(
                    on_press=self.on_press,
                    on_release=self.on_release,
                    suppress=False  # 不阻止按键事件传递给其他应用
                )
                self.listener.daemon = True
                self.listener.start()
                logging.info("热键监听器已启动")
        except Exception as e:
            logging.error(f"启动热键监听器失败: {e}")
            self.stop_listening()

    def stop_listening(self):
        """停止热键监听"""
        try:
            if self.listener:
                self.listener.stop()
                self.listener = None
                logging.info("热键监听器已停止")
        except Exception as e:
            logging.error(f"停止热键监听器失败: {e}")
        finally:
            self.reset_state()  # 确保状态被重置