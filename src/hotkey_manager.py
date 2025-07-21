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
        
        # 简化的状态检查变量
        self.last_state_check = 0       # 上次状态检查时间
        self.delayed_threads = []       # 延迟线程池（减少使用）
        
        # 简化的延迟检测相关变量
        self.hotkey_press_time = 0      # 热键按下的时间
        self.delay_threshold = 0.2      # 减少延迟阈值到200ms
        
        # 配置日志
        self.logger = logging.getLogger('HotkeyManager')
        
        # 从设置管理器获取快捷键类型
        self.hotkey_type = self.settings_manager.get_hotkey() if self.settings_manager else 'fn'
        
        # 资源清理标志
        self._cleanup_done = False
        
        # 线程安全保护
        self._state_lock = threading.Lock()  # 添加状态锁保护共享变量

    def set_press_callback(self, callback):
        self.press_callback = callback

    def set_release_callback(self, callback):
        self.release_callback = callback

    def _schedule_delayed_check(self, key_str):
        """简化的延迟检查方法"""
        # 直接移除按键，减少线程使用
        def delayed_check():
            time.sleep(0.05)  # 减少等待时间到50ms
            with self._state_lock:
                self.other_keys_pressed.discard(key_str)
        
        # 只在必要时创建线程，限制数量
        if len([t for t in self.delayed_threads if t.is_alive()]) < 3:
            thread = threading.Thread(target=delayed_check, daemon=True)
            thread.start()
            self.delayed_threads.append(thread)
    
    def reset_state(self):
        """重置所有状态"""
        with self._state_lock:
            self.other_keys_pressed.clear()
            self.hotkey_pressed = False
            self.is_recording = False
            self.last_press_time = 0
            self.last_state_check = 0
            self.hotkey_press_time = 0  # 重置热键按下时间
            
            # 简化线程清理逻辑
            self.delayed_threads.clear()
        
        self.logger.info("热键状态已重置")

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
        with self._state_lock:
            if self.hotkey_press_time == 0:
                self.hotkey_press_time = time.time()
                # 启动一个线程来持续检查
                import threading
                thread = threading.Thread(target=self._delayed_check_worker, daemon=True)
                thread.start()
                # 将线程添加到管理列表中
                self.delayed_threads.append(thread)
    
    def _delayed_check_worker(self):
        """简化的延迟检测工作线程"""
        try:
            with self._state_lock:
                start_time = self.hotkey_press_time
            
            # 简化检查逻辑，减少循环次数
            time.sleep(self.delay_threshold)  # 直接等待延迟时间
            
            with self._state_lock:
                # 检查状态是否仍然有效
                if (self.hotkey_press_time == start_time and 
                    not self.hotkey_pressed and 
                    not self.other_keys_pressed and 
                    not self.is_recording and 
                    self.press_callback):
                    
                    self.hotkey_pressed = True
                    self.is_recording = True
                    should_trigger = True
                else:
                    should_trigger = False
            
            if should_trigger:
                try:
                    self.logger.info("开始录音（延迟检测通过）")
                    self.press_callback()
                except Exception as e:
                    self.logger.error(f"按键回调执行失败: {e}")
                    
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
            
            # 线程安全地获取热键类型
            with self._state_lock:
                current_hotkey_type = self.hotkey_type
            
            if current_hotkey_type == 'ctrl':
                # 检查是否有除了 ctrl 之外的其他修饰键
                return bool(flags & (cmd_flag | shift_flag | alt_flag))
            elif current_hotkey_type == 'alt':
                # 检查是否有除了 alt 之外的其他修饰键
                return bool(flags & (cmd_flag | shift_flag | ctrl_flag))
            elif current_hotkey_type == 'fn':
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
            
            # 线程安全地获取热键类型
            with self._state_lock:
                current_hotkey_type = self.hotkey_type
            
            if current_hotkey_type == 'ctrl':
                return bool(flags & ctrl_flag) and not bool(flags & (cmd_flag | shift_flag | alt_flag))
            elif current_hotkey_type == 'alt':
                return bool(flags & alt_flag) and not bool(flags & (cmd_flag | shift_flag | ctrl_flag))
            elif current_hotkey_type == 'fn':
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
    
    def _is_common_combination_key(self, key):
        """检查是否是常见组合键的字母部分"""
        try:
            # 检查是否是字母键
            if hasattr(key, 'char') and key.char:
                # 常见的组合键字母：C(复制), V(粘贴), X(剪切), Z(撤销), Y(重做), A(全选), S(保存), F(查找)等
                common_combo_chars = {'c', 'v', 'x', 'z', 'y', 'a', 's', 'f', 'n', 'o', 'p', 'w', 't', 'r'}
                return key.char.lower() in common_combo_chars
            return False
        except Exception as e:
            self.logger.debug(f"检查组合键字母时出错: {e}")
            return False

    def _monitor_fn_key(self):
        """简化的fn键监听 - 降低CPU使用率"""
        last_fn_state = False
        
        while not self.should_stop:
            if self.hotkey_type == 'fn':
                # 获取当前修饰键状态
                flags = Quartz.CGEventSourceFlagsState(Quartz.kCGEventSourceStateHIDSystemState)
                is_fn_down = bool(flags & 0x800000)
                
                # 只在状态变化时处理
                if is_fn_down != last_fn_state:
                    last_fn_state = is_fn_down
                    
                    with self._state_lock:
                        if is_fn_down and not self.hotkey_pressed:
                            self.hotkey_pressed = True
                            # 只在没有其他键按下且未在录音时开始录音
                            if not self.other_keys_pressed and not self.is_recording and self.press_callback:
                                try:
                                    self.is_recording = True
                                    self.logger.info("开始录音")
                                    self.press_callback()
                                except Exception as e:
                                    self.logger.error(f"按键回调执行失败: {e}")
                        elif not is_fn_down and self.hotkey_pressed:
                            self.hotkey_pressed = False
                            # 如果正在录音，则停止录音
                            if self.is_recording and self.release_callback:
                                try:
                                    self.logger.info("停止录音")
                                    self.release_callback()
                                    self.is_recording = False
                                except Exception as e:
                                    self.logger.error(f"释放回调执行失败: {e}")
                
                # 固定休眠时间，减少CPU使用
                time.sleep(0.02)  # 50Hz检查频率
            else:
                # 非fn模式时降低检查频率
                time.sleep(0.1)

    def on_press(self, key):
        """处理按键按下事件"""
        try:
            current_time = time.time()
            
            # 简化状态重置检查
            with self._state_lock:
                should_reset = (current_time - self.last_press_time > 5 and 
                               (self.hotkey_pressed or self.other_keys_pressed))
                self.last_press_time = current_time
            
            if should_reset:
                self.reset_state()
            
            # 记录按键
            key_str = str(key)
            
            if self.hotkey_type != 'fn' and self._is_hotkey_pressed(key):
                with self._state_lock:
                    should_start_check = not self.hotkey_pressed
                if should_start_check:
                    # 启动延迟检测线程
                    self._start_delayed_hotkey_check()
            else:
                # 记录其他按键
                with self._state_lock:
                    key_already_pressed = key_str in self.other_keys_pressed
                    if not key_already_pressed:
                        self.other_keys_pressed.add(key_str)
                        should_stop_recording = self.is_recording and self.release_callback
                        
                        # 如果检测到常见的组合键字母，重置热键状态
                        if self._is_common_combination_key(key):
                            self.hotkey_press_time = 0
                
                # 如果正在录音且检测到其他按键，停止录音
                if not key_already_pressed and should_stop_recording:
                    try:
                        self.release_callback()
                        with self._state_lock:
                            self.is_recording = False
                    except Exception as e:
                        self.logger.error(f"释放回调执行失败: {e}")
        
        except Exception as e:
            self.logger.error(f"处理按键按下事件失败: {str(e)}")

    def on_release(self, key):
        """处理按键释放事件"""
        try:
            key_str = str(key)
            
            # 延迟移除按键记录
            self._schedule_delayed_check(key_str)
            
            if self.hotkey_type != 'fn' and self._is_hotkey_pressed(key):
                # 重置热键按下时间
                with self._state_lock:
                    self.hotkey_press_time = 0
                    should_stop_recording = self.hotkey_pressed
                    if should_stop_recording:
                        self.hotkey_pressed = False
                        is_currently_recording = self.is_recording and self.release_callback
                
                if should_stop_recording and is_currently_recording:
                    try:
                        self.release_callback()
                        with self._state_lock:
                            self.is_recording = False
                    except Exception as e:
                        self.logger.error(f"释放回调执行失败: {e}")
        
        except Exception as e:
            self.logger.error(f"处理按键释放事件失败: {str(e)}")

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
                print("✓ 键盘监听器已启动")
                
                # 启动 fn 键监听线程
                self.should_stop = False
                self.fn_listener_thread = threading.Thread(target=self._monitor_fn_key)
                self.fn_listener_thread.daemon = True
                self.fn_listener_thread.start()
                print("✓ Fn键监听线程已启动")
                
                self.logger.info("热键监听器已启动")
                print(f"✓ 热键监听已启动，当前热键: {self.hotkey_type}")
        except Exception as e:
            self.logger.error(f"启动热键监听器失败: {e}")
            print(f"❌ 启动热键监听失败: {e}")
            import traceback
            print(f"详细错误信息: {traceback.format_exc()}")
            self.stop_listening()
            raise

    def stop_listening(self):
        """停止热键监听"""
        try:
            # 停止 fn 键监听线程
            self.should_stop = True
            if self.fn_listener_thread and self.fn_listener_thread.is_alive():
                # 缩短超时时间，避免在程序退出时卡死
                self.fn_listener_thread.join(timeout=0.1)
                if self.fn_listener_thread.is_alive():
                    print("⚠️ Fn键监听线程未能及时停止，但继续退出流程")
                else:
                    print("✓ Fn键监听线程已停止")
            
            # 停止键盘监听器
            if self.keyboard_listener:
                self.keyboard_listener.stop()
                self.keyboard_listener = None
                print("✓ 键盘监听器已停止")
            
            self.logger.info("热键监听器已停止")
            print("✓ 热键监听已停止")
        except Exception as e:
            self.logger.error(f"停止热键监听器失败: {e}")
            print(f"❌ 停止热键监听时出错: {e}")
            import traceback
            print(f"详细错误信息: {traceback.format_exc()}")
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
            self.logger.info(f"正在清理 {len(self.delayed_threads)} 个延迟线程")
            for i, thread in enumerate(self.delayed_threads):
                if thread.is_alive():
                    self.logger.debug(f"等待线程 {i+1} 结束")
                    # 缩短超时时间，避免在程序退出时卡死
                    thread.join(timeout=0.1)
                    if thread.is_alive():
                        self.logger.warning(f"线程 {i+1} 未能在超时时间内结束，但继续清理流程")
            self.delayed_threads.clear()
            self.logger.info("延迟线程清理完成")
            
            # 清理回调
            self.press_callback = None
            self.release_callback = None
            
            self._cleanup_done = True
            self.logger.info("热键管理器资源清理完成")
            
        except Exception as e:
            self.logger.error(f"清理热键管理器资源失败: {e}")
    
    def get_status(self):
        """获取热键管理器当前状态"""
        try:
            # 检查键盘监听器状态
            listener_running = (self.keyboard_listener is not None and 
                              hasattr(self.keyboard_listener, 'running') and 
                              self.keyboard_listener.running)
            
            # 检查fn监听线程状态
            fn_thread_running = (self.fn_listener_thread is not None and 
                               self.fn_listener_thread.is_alive() and 
                               not self.should_stop)
            
            # 根据热键类型确定整体状态
            if self.hotkey_type == 'fn':
                is_active = listener_running and fn_thread_running
            else:
                is_active = listener_running
            
            return {
                'active': is_active,
                'hotkey_type': self.hotkey_type,
                'listener_running': listener_running,
                'fn_thread_running': fn_thread_running,
                'is_recording': self.is_recording
            }
        except Exception as e:
            self.logger.error(f"获取热键状态失败: {e}")
            return {
                'active': False,
                'hotkey_type': self.hotkey_type,
                'listener_running': False,
                'fn_thread_running': False,
                'is_recording': False
            }
    
    def __del__(self):
        """析构函数，确保资源被释放"""
        try:
            self.cleanup()
        except:
            pass