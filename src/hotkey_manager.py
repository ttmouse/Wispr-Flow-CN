from pynput import keyboard
import time
import logging
import Quartz
import threading
from concurrent.futures import ThreadPoolExecutor

# 尝试不同的导入方式以适应不同的运行环境
try:
    # 最后尝试直接导入（当在同一目录时）
    from hotkey_manager_base import HotkeyManagerBase
    from utils.cleanup_mixin import CleanupMixin
except ImportError:
    try:
        # 然后尝试从src包导入
        from src.hotkey_manager_base import HotkeyManagerBase
        from src.utils.cleanup_mixin import CleanupMixin
    except ImportError:
        # 首先尝试相对导入（当作为模块导入时）
        from .hotkey_manager_base import HotkeyManagerBase
        from .utils.cleanup_mixin import CleanupMixin

class PythonHotkeyManager(HotkeyManagerBase, CleanupMixin):
    def __init__(self, settings_manager=None):
        # 正确的多重继承初始化
        HotkeyManagerBase.__init__(self, settings_manager)
        CleanupMixin.__init__(self)
        # 保留原有的属性初始化
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
        
        # 线程池用于优化性能
        self.thread_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="HotkeyManager")
        
        # 简化的延迟检测相关变量
        self.hotkey_press_time = 0      # 热键按下的时间
        # 从设置中读取延迟时间，默认200ms
        delay_ms = self.settings_manager.get_setting('hotkey_settings.recording_start_delay', 200) if self.settings_manager else 200
        self.delay_threshold = delay_ms / 1000.0  # 转换为秒
        
        # 配置日志
        self.logger = logging.getLogger('HotkeyManager')
        
        # 从设置管理器获取快捷键类型
        self.hotkey_type = self.settings_manager.get_hotkey() if self.settings_manager else 'fn'
        
        # 资源清理标志
        self._cleanup_done = False
        
        # 线程安全保护 - 使用可重入锁避免死锁
        self._state_lock = threading.RLock()  # 使用可重入锁避免死锁问题

    def _check_component_status(self):
        """统一的组件状态检查方法"""
        # 检查键盘监听器状态
        listener_running = (self.keyboard_listener is not None and
                          hasattr(self.keyboard_listener, 'running') and
                          self.keyboard_listener.running)

        # 检查fn监听线程状态
        fn_thread_running = False
        if self.fn_listener_thread is not None:
            fn_thread_running = (self.fn_listener_thread.is_alive() and
                               not self.should_stop)

        return listener_running, fn_thread_running

    def set_press_callback(self, callback):
        self.press_callback = callback

    def set_release_callback(self, callback):
        self.release_callback = callback

    def _schedule_delayed_check(self, key_str):
        """使用线程池的延迟检查方法"""
        def delayed_check():
            time.sleep(0.05)  # 减少等待时间到50ms
            with self._state_lock:
                self.other_keys_pressed.discard(key_str)
        
        # 使用线程池提交任务，避免频繁创建线程
        try:
            self.thread_pool.submit(delayed_check)
        except Exception as e:
            self.logger.error(f"提交延迟检查任务失败: {e}")
            # 降级处理：直接移除按键
            with self._state_lock:
                self.other_keys_pressed.discard(key_str)
    
    def reset_state(self):
        """重置所有状态"""
        with self._state_lock:
            self.other_keys_pressed.clear()
            self.hotkey_pressed = False
            self.is_recording = False
            self.last_press_time = 0
            self.last_state_check = 0
            self.hotkey_press_time = 0  # 重置热键按下时间
            
            # 线程状态已重置
        
        pass  # 热键状态已重置

    def force_reset(self):
        """强制重置所有状态并重新初始化监听器"""
        self.stop_listening()
        self.reset_state()
        self.start_listening()
        pass  # 热键管理器已强制重置

    def update_hotkey(self, hotkey_type='fn') -> bool:
        """更新快捷键设置"""
        try:
            self.hotkey_type = hotkey_type
            return True  # 快捷键设置已更新
        except Exception as e:
            self.logger.error(f"更新热键设置失败: {e}")
            return False
    
    def update_delay_settings(self):
        """更新延迟设置"""
        if self.settings_manager:
            delay_ms = self.settings_manager.get_setting('hotkey_settings.recording_start_delay', 200)
            self.delay_threshold = delay_ms / 1000.0
            pass  # 录制启动延迟已更新
        else:
            self.logger.warning("设置管理器不可用，无法更新延迟设置")

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
        """使用线程池启动延迟检测"""
        with self._state_lock:
            if self.hotkey_press_time == 0:
                self.hotkey_press_time = time.time()
                # 使用线程池提交延迟检测任务
                try:
                    self.thread_pool.submit(self._delayed_check_worker)
                except Exception as e:
                    self.logger.error(f"提交延迟检测任务失败: {e}")
                    # 重置状态
                    self.hotkey_press_time = 0
    
    def _delayed_check_worker(self):
        """简化的延迟检测工作线程 - 优化锁持有时间"""
        try:
            # 快速获取开始时间，减少锁持有时间
            with self._state_lock:
                start_time = self.hotkey_press_time
            
            # 在锁外等待，避免长时间持有锁
            time.sleep(self.delay_threshold)
            
            # 快速检查状态并设置标志
            should_trigger = False
            callback_to_call = None
            
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
                    callback_to_call = self.press_callback
            
            # 在锁外执行回调，避免回调中的操作导致死锁
            if should_trigger and callback_to_call:
                try:
                    pass  # 开始录音（延迟检测通过）
                    callback_to_call()
                except Exception as e:
                    self.logger.error(f"按键回调执行失败: {e}")
                    # 回调失败时重置状态
                    with self._state_lock:
                        self.hotkey_pressed = False
                        self.is_recording = False
                    
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
        error_count = 0
        max_errors = 10  # 最大连续错误次数
        
        self.logger.debug("Fn键监听线程已启动")
        
        try:
            while not self.should_stop:
                try:
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
                                            pass  # 开始录音
                                            self.press_callback()
                                        except Exception as e:
                                            self.logger.error(f"按键回调执行失败: {e}")
                                elif not is_fn_down and self.hotkey_pressed:
                                    self.hotkey_pressed = False
                                    # 如果正在录音，则停止录音
                                    if self.is_recording and self.release_callback:
                                        try:
                                            pass  # 停止录音
                                            self.release_callback()
                                            self.is_recording = False
                                        except Exception as e:
                                            self.logger.error(f"释放回调执行失败: {e}")
                        
                        # 重置错误计数
                        error_count = 0
                        
                        # 降低检查频率，减少系统调用和CPU使用
                        time.sleep(0.1)  # 10Hz检查频率，从50Hz降低
                    else:
                        # 非fn模式时降低检查频率
                        time.sleep(0.1)
                        
                except Exception as e:
                    error_count += 1
                    self.logger.error(f"Fn键监听循环出错 (第{error_count}次): {e}")
                    
                    if error_count >= max_errors:
                        self.logger.error(f"Fn键监听线程连续出错{max_errors}次，线程退出")
                        break
                    
                    # 出错后短暂休眠
                    time.sleep(0.1)
                    
        except Exception as e:
            self.logger.error(f"Fn键监听线程发生严重错误: {e}")
            import traceback
            self.logger.error(f"详细错误信息: {traceback.format_exc()}")
        finally:
            self.logger.debug("Fn键监听线程已退出")
            # 确保状态被重置
            with self._state_lock:
                self.hotkey_pressed = False
                if self.is_recording:
                    self.is_recording = False

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

    def _safe_on_press(self, key):
        """安全的按键按下处理器，捕获所有异常"""
        try:
            self.on_press(key)
        except Exception as e:
            # 静默处理 pynput 内部错误，避免应用程序崩溃
            self.logger.debug(f"按键处理中的内部错误（已忽略）: {e}")
            pass

    def _safe_on_release(self, key):
        """安全的按键释放处理器，捕获所有异常"""
        try:
            self.on_release(key)
        except Exception as e:
            # 静默处理 pynput 内部错误，避免应用程序崩溃
            self.logger.debug(f"按键处理中的内部错误（已忽略）: {e}")
            pass

    def start_listening(self):
        """启动热键监听"""
        try:
            listener_running, _ = self._check_component_status()
            if not listener_running:
                self.reset_state()  # 启动监听时重置状态

                # 启动键盘监听器（用于其他键）- 添加安全包装
                self.keyboard_listener = keyboard.Listener(
                    on_press=self._safe_on_press,
                    on_release=self._safe_on_release,
                    suppress=False  # 不阻止按键事件传递给其他应用
                )
                self.keyboard_listener.daemon = True
                self.keyboard_listener.start()

                # 启动 fn 键监听线程
                self.should_stop = False
                self.fn_listener_thread = threading.Thread(target=self._monitor_fn_key)
                self.fn_listener_thread.daemon = True
                self.fn_listener_thread.start()

                self.logger.debug("热键监听器已启动")
        except Exception as e:
            self.logger.error(f"启动热键监听器失败: {e}")
            import traceback
            self.logger.error(f"详细错误信息: {traceback.format_exc()}")
            self.stop_listening()
            # 不再抛出异常，而是记录错误并继续运行
            self.logger.warning("热键监听器启动失败，应用程序将继续运行但热键功能不可用")

    def stop_listening(self):
        """停止热键监听"""
        try:
            # 停止 fn 键监听线程
            self.should_stop = True
            _, fn_thread_running = self._check_component_status()
            if fn_thread_running and self.fn_listener_thread:
                # 使用更合理的超时时间，避免死锁
                self.fn_listener_thread.join(timeout=1.0)  # 增加到1秒超时
                if self.fn_listener_thread.is_alive():
                    self.logger.warning("Fn键监听线程超时未停止")
                else:
                    pass  # Fn键监听线程已停止
            
            # 停止键盘监听器
            if self.keyboard_listener:
                self.keyboard_listener.stop()
                self.keyboard_listener = None
            
            self.logger.debug("热键监听器已停止")
        except Exception as e:
            self.logger.error(f"停止热键监听器失败: {e}")
            import traceback
            self.logger.error(f"详细错误信息: {traceback.format_exc()}")
        finally:
            self.reset_state()  # 确保状态被重置
    
    def _cleanup_resources(self):
        """实现CleanupMixin要求的资源清理方法"""
        # 停止监听
        self.stop_listening()

        # 关闭线程池
        if hasattr(self, 'thread_pool') and self.thread_pool:
            try:
                # 使用简单的shutdown方法，避免版本兼容性问题
                self.thread_pool.shutdown(wait=True)
                self.logger.debug("线程池已关闭")
            except Exception as e:
                self.logger.warning(f"关闭线程池时出现异常: {e}")

        # 清理回调
        self.press_callback = None
        self.release_callback = None

    def cleanup(self) -> None:
        """实现HotkeyManagerBase要求的cleanup抽象方法"""
        # 调用CleanupMixin的cleanup方法
        CleanupMixin.cleanup(self)
    
    def get_status(self) -> dict:
        """获取热键管理器当前状态"""
        try:
            # 使用统一的状态检查方法
            listener_running, fn_thread_running = self._check_component_status()

            # 额外检查：如果线程已死但should_stop为False，说明线程意外退出
            if (self.fn_listener_thread is not None and
                not self.fn_listener_thread.is_alive() and
                not self.should_stop):
                self.logger.warning("检测到Fn监听线程意外退出")
                fn_thread_running = False
            
            # 根据热键类型确定整体状态
            if self.hotkey_type == 'fn':
                is_active = listener_running and fn_thread_running
            else:
                is_active = listener_running
            
            # 如果检测到状态异常，记录详细信息
            if not is_active:
                status_details = []
                if not listener_running:
                    status_details.append("键盘监听器未运行")
                if self.hotkey_type == 'fn' and not fn_thread_running:
                    if self.fn_listener_thread is None:
                        status_details.append("Fn监听线程未创建")
                    elif not self.fn_listener_thread.is_alive():
                        status_details.append("Fn监听线程已停止")
                    elif self.should_stop:
                        status_details.append("Fn监听线程被标记停止")
                
                if status_details:
                    self.logger.info(f"热键状态检查: {', '.join(status_details)}")
            
            return {
                'active': is_active,
                'scheme': 'python',
                'hotkey_type': self.hotkey_type,
                'listener_running': listener_running,
                'fn_thread_running': fn_thread_running,
                'is_recording': self.is_recording
            }
        except Exception as e:
            self.logger.error(f"获取热键状态失败: {e}")
            return {
                'active': False,
                'scheme': 'python',
                'hotkey_type': self.hotkey_type,
                'listener_running': False,
                'fn_thread_running': False,
                'is_recording': False
            }
    
