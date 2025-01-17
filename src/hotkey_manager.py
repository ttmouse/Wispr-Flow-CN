from pynput import keyboard
import time
import logging
import Quartz
import threading
import json
import os

class HotkeyManager:
    def __init__(self):
        self.press_callback = None
        self.release_callback = None
        self.keyboard_listener = None
        self.fn_listener_thread = None
        self.other_keys_pressed = set()  # 记录当前按下的其他键
        self.hotkey_pressed = False      # 记录热键的状态
        self.last_press_time = 0        # 记录最后一次按键时间
        self.is_recording = False       # 记录是否正在录音
        self.should_stop = False        # 控制 fn 监听线程
        
        # 配置日志
        logging.basicConfig(level=logging.DEBUG,
                          format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger('HotkeyManager')
        
        # 加载设置
        self.hotkey_type = self.load_settings().get('hotkey', 'fn')

    def set_press_callback(self, callback):
        self.press_callback = callback

    def set_release_callback(self, callback):
        self.release_callback = callback

    def reset_state(self):
        """重置所有状态"""
        self.other_keys_pressed.clear()
        self.hotkey_pressed = False
        self.is_recording = False
        self.logger.info("热键状态已重置")

    def save_settings(self, hotkey_type='fn'):
        """保存设置"""
        try:
            settings = {'hotkey': hotkey_type}
            with open('settings.json', 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            self.hotkey_type = hotkey_type
            self.logger.info(f"已保存快捷键设置: {hotkey_type}")
        except Exception as e:
            self.logger.error(f"保存设置失败: {e}")

    def load_settings(self):
        """加载设置"""
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"加载设置失败: {e}")
        return {'hotkey': 'fn'}

    def _is_hotkey_pressed(self, key):
        """检查是否是当前设置的热键"""
        if self.hotkey_type == 'fn':
            # 使用 Quartz 检查 fn 键状态
            flags = Quartz.CGEventSourceFlagsState(Quartz.kCGEventSourceStateHIDSystemState)
            return bool(flags & 0x800000)
        elif self.hotkey_type == 'ctrl':
            return key == keyboard.Key.ctrl_l
        elif self.hotkey_type == 'alt':
            return key == keyboard.Key.alt_l
        return False

    def _monitor_fn_key(self):
        """监听 fn 键的状态"""
        while not self.should_stop:
            if self.hotkey_type == 'fn':
                # 获取当前修饰键状态
                flags = Quartz.CGEventSourceFlagsState(Quartz.kCGEventSourceStateHIDSystemState)
                # 检查 fn 键状态 (0x800000)
                is_fn_down = bool(flags & 0x800000)
                
                if is_fn_down != self.hotkey_pressed:
                    if is_fn_down:
                        self.logger.info("fn 键按下")
                        if not self.hotkey_pressed:  # 防止重复触发
                            self.hotkey_pressed = True
                            # 只在没有其他键按下且未在录音时开始录音
                            if not self.other_keys_pressed and not self.is_recording and self.press_callback:
                                try:
                                    self.is_recording = True
                                    self.logger.info("开始录音")
                                    self.press_callback()
                                except Exception as e:
                                    self.logger.error(f"按键回调执行失败: {e}")
                    else:
                        self.logger.info("fn 键释放")
                        if self.hotkey_pressed:  # 防止重复触发
                            self.hotkey_pressed = False
                            # 如果正在录音，则停止录音
                            if self.is_recording and self.release_callback:
                                try:
                                    self.logger.info("停止录音")
                                    self.release_callback()
                                    self.is_recording = False
                                except Exception as e:
                                    self.logger.error(f"释放回调执行失败: {e}")
            
            time.sleep(0.01)  # 降低 CPU 使用率

    def on_press(self, key):
        """处理按键按下事件"""
        try:
            current_time = time.time()
            self.last_press_time = current_time
            
            # 记录按键
            key_str = str(key)
            self.logger.debug(f"按键按下: {key_str}")
            
            if self.hotkey_type != 'fn' and self._is_hotkey_pressed(key):
                self.logger.info(f"{self.hotkey_type} 键按下")
                if not self.hotkey_pressed:  # 防止重复触发
                    self.hotkey_pressed = True
                    # 只在没有其他键按下且未在录音时开始录音
                    if not self.other_keys_pressed and not self.is_recording and self.press_callback:
                        try:
                            self.is_recording = True
                            self.logger.info("开始录音")
                            self.press_callback()
                        except Exception as e:
                            self.logger.error(f"按键回调执行失败: {e}")
            else:
                # 记录其他按键
                if key_str not in self.other_keys_pressed:
                    self.other_keys_pressed.add(key_str)
                    self.logger.debug(f"其他键按下: {key_str}")
                    # 如果正在录音，则停止录音
                    if self.is_recording and self.release_callback:
                        try:
                            self.logger.info("由于其他键按下，停止录音")
                            self.release_callback()
                            self.is_recording = False
                        except Exception as e:
                            self.logger.error(f"释放回调执行失败: {e}")
            
            self.logger.debug(f"按键状态 - {self.hotkey_type}: {self.hotkey_pressed}, 其他键: {self.other_keys_pressed}, 录音: {self.is_recording}")
        
        except Exception as e:
            self.logger.error(f"处理按键按下事件失败: {str(e)}")
            self.logger.debug(f"按键信息: {str(key)}, 类型: {type(key)}")

    def on_release(self, key):
        """处理按键释放事件"""
        try:
            key_str = str(key)
            self.logger.debug(f"按键释放: {key_str}")
            
            if self.hotkey_type != 'fn' and self._is_hotkey_pressed(key):
                self.logger.info(f"{self.hotkey_type} 键释放")
                if self.hotkey_pressed:  # 防止重复触发
                    self.hotkey_pressed = False
                    # 如果正在录音，则停止录音
                    if self.is_recording and self.release_callback:
                        try:
                            self.logger.info("停止录音")
                            self.release_callback()
                            self.is_recording = False
                        except Exception as e:
                            self.logger.error(f"释放回调执行失败: {e}")
            else:
                # 移除释放的按键
                self.other_keys_pressed.discard(key_str)
                self.logger.debug(f"其他键释放: {key_str}")
            
            self.logger.debug(f"释放按键 - {self.hotkey_type}: {self.hotkey_pressed}, 其他键: {self.other_keys_pressed}, 录音: {self.is_recording}")
        
        except Exception as e:
            self.logger.error(f"处理按键释放事件失败: {str(e)}")
            self.logger.debug(f"按键信息: {str(key)}, 类型: {type(key)}")

    def start_listening(self):
        """启动热键监听"""
        try:
            if not self.keyboard_listener or not self.keyboard_listener.is_alive():
                self.reset_state()  # 启动监听时重置状态
                
                # 启动键盘监听器（用于其他键）
                self.keyboard_listener = keyboard.Listener(
                    on_press=self.on_press,
                    on_release=self.on_release,
                    suppress=False  # 不阻止按键事件传递给其他应用
                )
                self.keyboard_listener.daemon = True
                self.keyboard_listener.start()
                
                # 启动 fn 键监听线程
                self.should_stop = False
                self.fn_listener_thread = threading.Thread(target=self._monitor_fn_key)
                self.fn_listener_thread.daemon = True
                self.fn_listener_thread.start()
                
                self.logger.info("热键监听器已启动")
        except Exception as e:
            self.logger.error(f"启动热键监听器失败: {e}")
            self.stop_listening()

    def stop_listening(self):
        """停止热键监听"""
        try:
            # 停止 fn 键监听线程
            self.should_stop = True
            if self.fn_listener_thread and self.fn_listener_thread.is_alive():
                self.fn_listener_thread.join(timeout=1.0)
            
            # 停止键盘监听器
            if self.keyboard_listener:
                self.keyboard_listener.stop()
                self.keyboard_listener = None
            
            self.logger.info("热键监听器已停止")
        except Exception as e:
            self.logger.error(f"停止热键监听器失败: {e}")
        finally:
            self.reset_state()  # 确保状态被重置