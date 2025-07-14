from pynput import keyboard
import time
import logging
import Quartz
import threading

class HotkeyManager:
    def __init__(self, settings_manager=None):
        self.press_callback = None
        self.release_callback = None
        self.keyboard_listener = None
        self.fn_listener_thread = None
        self.other_keys_pressed = set()  # 记录当前按下的其他键
        self.hotkey_pressed = False      # 记录热键的状态
        self.last_press_time = 0        # 记录最后一次按键时间
        self.is_recording = False       # 记录是否正在录音
        self.should_stop = False        # 控制 fn 监听线程
        self.settings_manager = settings_manager  # 使用传入的设置管理器
        
        # CPU优化相关变量
        self.last_state_check = 0       # 上次状态检查时间
        self.state_stable_count = 0     # 状态稳定计数
        self.delayed_threads = []       # 延迟线程池
        
        # 时间延迟检测相关变量
        self.hotkey_press_time = 0      # 热键按下的时间
        self.delay_threshold = 0.15     # 延迟阈值（150ms）
        
        # 配置日志
        self.logger = logging.getLogger('HotkeyManager')
        
        # 从设置管理器获取快捷键类型
        self.hotkey_type = self.settings_manager.get_hotkey() if self.settings_manager else 'fn'
        
        # 资源清理标志
        self._cleanup_done = False

    def set_press_callback(self, callback):
        self.press_callback = callback

    def set_release_callback(self, callback):
        self.release_callback = callback

    def _schedule_delayed_check(self, key_str):
        """优化的延迟检查方法"""
        def delayed_check():
            time.sleep(0.1)  # 等待100ms
            if key_str in self.other_keys_pressed:
                self.other_keys_pressed.discard(key_str)
        
        # 清理已完成的线程
        self.delayed_threads = [t for t in self.delayed_threads if t.is_alive()]
        
        # 限制同时运行的延迟线程数量
        if len(self.delayed_threads) < 5:
            thread = threading.Thread(target=delayed_check, daemon=True)
            thread.start()
            self.delayed_threads.append(thread)
    
    def reset_state(self):
        """重置所有状态"""
        self.other_keys_pressed.clear()
        self.hotkey_pressed = False
        self.is_recording = False
        self.last_press_time = 0
        self.last_state_check = 0
        self.state_stable_count = 0
        self.hotkey_press_time = 0  # 重置热键按下时间
        
        # 清理延迟线程
        for thread in self.delayed_threads:
            if thread.is_alive():
                thread.join(timeout=0.1)
        self.delayed_threads.clear()
        
        # 额外检查确保系统级修饰键状态正确
        if self.hotkey_type != 'fn':
            # 检查当前实际的修饰键状态
            flags = Quartz.CGEventSourceFlagsState(Quartz.kCGEventSourceStateHIDSystemState)
            # 如果没有任何修饰键被按下，确保状态完全重置
            if not (flags & (0x800000 | 0x100000 | 0x200000)):  # fn, cmd, shift flags
                self.hotkey_pressed = False
                self.other_keys_pressed.clear()
        
        self.logger.info("热键状态已重置，并验证系统修饰键状态")

    def force_reset(self):
        """强制重置所有状态并重新初始化监听器"""
        self.stop_listening()
        self.reset_state()
        self.start_listening()
        self.logger.info("热键管理器已强制重置")

    def update_hotkey(self, hotkey_type='fn'):
        """更新快捷键设置"""
        self.hotkey_type = hotkey_type
        self.logger.info(f"已更新快捷键设置: {hotkey_type}")

    def _is_hotkey_pressed(self, key):
        """检查是否是当前设置的热键"""
        if self.hotkey_type == 'fn':
            # 使用 Quartz 检查 fn 键状态
            flags = Quartz.CGEventSourceFlagsState(Quartz.kCGEventSourceStateHIDSystemState)
            return bool(flags & 0x800000)
        elif self.hotkey_type == 'ctrl':
            return key in [keyboard.Key.ctrl_l, keyboard.Key.ctrl_r]
        elif self.hotkey_type == 'alt':
            return key in [keyboard.Key.alt_l, keyboard.Key.alt_r]
        return False
    
    def _start_delayed_hotkey_check(self):
        """启动延迟检测线程"""
        if self.hotkey_press_time == 0:
            self.hotkey_press_time = time.time()
            # 启动一个线程来持续检查
            import threading
            threading.Thread(target=self._delayed_check_worker, daemon=True).start()
    
    def _delayed_check_worker(self):
        """延迟检测工作线程"""
        try:
            start_time = self.hotkey_press_time
            has_other_keys = False  # 标记是否检测到其他修饰键
            
            while self.hotkey_press_time == start_time:
                time.sleep(0.01)  # 10ms 检查间隔
                current_time = time.time()
                
                # 检查是否有其他修饰键被按下（不要求热键必须一直按着）
                if self._has_other_modifier_keys():
                    has_other_keys = True
                    break  # 检测到其他修饰键，立即退出
                
                # 如果超过延迟阈值且没有检测到其他修饰键，触发录音
                if current_time - start_time >= self.delay_threshold / 1000.0:
                    if not has_other_keys:
                        # 通过检查，触发录音
                        if not self.hotkey_pressed and not self.other_keys_pressed and not self.is_recording and self.press_callback:
                            try:
                                self.hotkey_pressed = True
                                self.is_recording = True
                                self.logger.info("开始录音（延迟检测通过）")
                                self.press_callback()
                            except Exception as e:
                                self.logger.error(f"按键回调执行失败: {e}")
                    break
                    
        except Exception as e:
            self.logger.error(f"延迟检测线程错误: {e}")
    
    def _has_other_modifier_keys(self):
        """检查是否有其他修饰键被按下（不包括当前设置的热键）"""
        try:
            # 获取当前修饰键状态
            flags = Quartz.CGEventSourceFlagsState(Quartz.kCGEventSourceStateCombinedSessionState)
            
            # 定义修饰键标志
            ctrl_flag = Quartz.kCGEventFlagMaskControl
            cmd_flag = Quartz.kCGEventFlagMaskCommand
            shift_flag = Quartz.kCGEventFlagMaskShift
            alt_flag = Quartz.kCGEventFlagMaskAlternate
            
            if self.hotkey_type == 'ctrl':
                # 检查是否有除了 ctrl 之外的其他修饰键
                return bool(flags & (cmd_flag | shift_flag | alt_flag))
            elif self.hotkey_type == 'alt':
                # 检查是否有除了 alt 之外的其他修饰键
                return bool(flags & (cmd_flag | shift_flag | ctrl_flag))
            elif self.hotkey_type == 'fn':
                # fn 键不是标准修饰键，检查是否有任何修饰键
                return bool(flags & (cmd_flag | shift_flag | ctrl_flag | alt_flag))
            
            return False
            
        except Exception as e:
            self.logger.error(f"检查修饰键状态失败: {e}")
            return False
    
    def _check_only_hotkey_pressed(self):
        """检查是否只有热键被按下，没有其他修饰键（不包含时间逻辑）"""
        try:
            # 获取当前修饰键状态
            flags = Quartz.CGEventSourceFlagsState(Quartz.kCGEventSourceStateCombinedSessionState)
            
            # 定义修饰键标志
            ctrl_flag = Quartz.kCGEventFlagMaskControl
            cmd_flag = Quartz.kCGEventFlagMaskCommand
            shift_flag = Quartz.kCGEventFlagMaskShift
            alt_flag = Quartz.kCGEventFlagMaskAlternate
            
            if self.hotkey_type == 'ctrl':
                return bool(flags & ctrl_flag) and not bool(flags & (cmd_flag | shift_flag | alt_flag))
            elif self.hotkey_type == 'alt':
                return bool(flags & alt_flag) and not bool(flags & (cmd_flag | shift_flag | ctrl_flag))
            elif self.hotkey_type == 'fn':
                # 检查 fn 键状态
                fn_flags = Quartz.CGEventSourceFlagsState(Quartz.kCGEventSourceStateHIDSystemState)
                fn_pressed = bool(fn_flags & 0x800000)
                # fn 键被按下且没有其他修饰键
                return fn_pressed and not bool(flags & (cmd_flag | shift_flag | ctrl_flag | alt_flag))
            
            return False
            
        except Exception as e:
            self.logger.error(f"检查修饰键状态失败: {e}")
            return False
    
    def _is_only_hotkey_pressed(self):
        """检查是否只有热键被按下，没有其他修饰键（保持兼容性）"""
        return self._check_only_hotkey_pressed()

    def _monitor_fn_key(self):
        """监听 fn 键的状态 - 优化CPU使用率"""
        last_fn_state = False
        stable_count = 0
        
        while not self.should_stop:
            if self.hotkey_type == 'fn':
                current_time = time.time()
                
                # 获取当前修饰键状态
                flags = Quartz.CGEventSourceFlagsState(Quartz.kCGEventSourceStateHIDSystemState)
                # 检查 fn 键状态 (0x800000)
                is_fn_down = bool(flags & 0x800000)
                
                # 状态变化检测
                if is_fn_down != last_fn_state:
                    stable_count = 0
                    last_fn_state = is_fn_down
                    
                    if is_fn_down != self.hotkey_pressed:
                        if is_fn_down:
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
                    stable_count += 1
                
                # 自适应休眠：状态稳定时增加休眠时间
                if stable_count < 10:
                    time.sleep(0.01)  # 状态变化期间保持高响应
                elif stable_count < 100:
                    time.sleep(0.02)  # 短期稳定
                else:
                    time.sleep(0.05)  # 长期稳定，降低CPU使用
            else:
                # 非fn模式时大幅降低检查频率
                time.sleep(0.1)

    def on_press(self, key):
        """处理按键按下事件"""
        try:
            current_time = time.time()
            
            # 检查是否需要强制重置状态
            # 1. 如果上次按键时间超过5秒
            # 2. 如果检测到Command键（但不包括单独的Shift或Alt键，因为它们可能与热键组合）
            if (current_time - self.last_press_time > 5 and (self.hotkey_pressed or self.other_keys_pressed)) or \
               (isinstance(key, keyboard.Key) and key == keyboard.Key.cmd):
                self.logger.info("检测到可能的状态异常或系统快捷键，执行强制重置")
                self.reset_state()
            
            self.last_press_time = current_time
            
            # 记录按键
            key_str = str(key)
            # 减少debug日志输出频率
            if current_time - self.last_state_check > 1.0:  # 每秒最多一次debug日志
                self.logger.debug(f"按键按下: {key_str}")
                self.last_state_check = current_time
            
            if self.hotkey_type != 'fn' and self._is_hotkey_pressed(key):
                self.logger.info(f"{self.hotkey_type} 键按下")
                if not self.hotkey_pressed:  # 防止重复触发
                    # 启动延迟检测线程
                    self._start_delayed_hotkey_check()
            else:
                # 记录其他按键
                if key_str not in self.other_keys_pressed:
                    self.other_keys_pressed.add(key_str)
                    # 如果正在录音，则停止录音
                    if self.is_recording and self.release_callback:
                        try:
                            self.logger.info("由于其他键按下，停止录音")
                            self.release_callback()
                            self.is_recording = False
                        except Exception as e:
                            self.logger.error(f"释放回调执行失败: {e}")
        
        except Exception as e:
            self.logger.error(f"处理按键按下事件失败: {str(e)}")
            self.logger.debug(f"按键信息: {str(key)}, 类型: {type(key)}")

    def on_release(self, key):
        """处理按键释放事件"""
        try:
            key_str = str(key)
            self.logger.debug(f"按键释放: {key_str}")
            
            # 优化延迟检查，使用线程池管理
            self._schedule_delayed_check(key_str)
            
            if self.hotkey_type != 'fn' and self._is_hotkey_pressed(key):
                self.logger.info(f"{self.hotkey_type} 键释放")
                # 重置热键按下时间
                self.hotkey_press_time = 0
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
            
            # 减少debug日志输出
        
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
    
    def cleanup(self):
        """清理所有资源"""
        if self._cleanup_done:
            return
            
        try:
            self.logger.info("开始清理热键管理器资源")
            
            # 停止监听
            self.stop_listening()
            
            # 等待并清理所有延迟线程
            for thread in self.delayed_threads:
                if thread.is_alive():
                    thread.join(timeout=0.5)
            self.delayed_threads.clear()
            
            # 清理回调
            self.press_callback = None
            self.release_callback = None
            
            self._cleanup_done = True
            self.logger.info("热键管理器资源清理完成")
            
        except Exception as e:
            self.logger.error(f"清理热键管理器资源失败: {e}")
    
    def __del__(self):
        """析构函数，确保资源被释放"""
        try:
            self.cleanup()
        except:
            pass