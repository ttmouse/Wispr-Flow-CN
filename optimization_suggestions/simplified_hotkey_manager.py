#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的热键管理器
移除复杂的延迟检测机制，提高响应性能
"""

import time
import threading
import logging
from abc import ABC, abstractmethod
from typing import Callable, Optional, Set
from enum import Enum

class HotkeyType(Enum):
    """热键类型"""
    FN = "fn"
    CTRL = "ctrl"
    ALT = "alt"
    CMD = "cmd"

class HotkeyState(Enum):
    """热键状态"""
    IDLE = "idle"
    PRESSED = "pressed"
    RECORDING = "recording"

class SimplifiedHotkeyManager:
    """简化的热键管理器
    
    移除了复杂的延迟检测机制，采用直接响应模式
    大幅减少代码复杂度和线程数量
    """
    
    def __init__(self, settings_manager=None):
        self.settings_manager = settings_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 简化的状态管理
        self._state = HotkeyState.IDLE
        self._hotkey_type = HotkeyType.FN
        self._state_lock = threading.Lock()
        
        # 回调函数
        self._press_callback: Optional[Callable] = None
        self._release_callback: Optional[Callable] = None
        
        # 监听器
        self._keyboard_listener = None
        self._fn_monitor_thread = None
        self._should_stop = False
        
        # 性能优化：减少系统调用频率
        self._last_check_time = 0
        self._check_interval = 0.05  # 50ms检查间隔
        
        # 防抖设置
        self._last_press_time = 0
        self._last_release_time = 0
        self._debounce_interval = 0.05  # 50ms防抖
    
    def set_callbacks(self, press_callback: Callable, release_callback: Callable):
        """设置回调函数"""
        self._press_callback = press_callback
        self._release_callback = release_callback
    
    def set_hotkey_type(self, hotkey_type: HotkeyType):
        """设置热键类型"""
        with self._state_lock:
            self._hotkey_type = hotkey_type
            self.logger.info(f"热键类型已设置为: {hotkey_type.value}")
    
    def start_listening(self) -> bool:
        """开始监听热键"""
        try:
            self._should_stop = False
            
            # 启动键盘监听器（用于非fn键）
            if self._hotkey_type != HotkeyType.FN:
                self._start_keyboard_listener()
            
            # 启动fn键监听器
            if self._hotkey_type == HotkeyType.FN:
                self._start_fn_monitor()
            
            self.logger.info("热键监听已启动")
            return True
            
        except Exception as e:
            self.logger.error(f"启动热键监听失败: {e}")
            return False
    
    def stop_listening(self):
        """停止监听热键"""
        try:
            self._should_stop = True
            
            # 停止键盘监听器
            if self._keyboard_listener:
                self._keyboard_listener.stop()
                self._keyboard_listener = None
            
            # 等待fn监听线程结束
            if self._fn_monitor_thread and self._fn_monitor_thread.is_alive():
                self._fn_monitor_thread.join(timeout=1.0)
            
            # 重置状态
            with self._state_lock:
                self._state = HotkeyState.IDLE
            
            self.logger.info("热键监听已停止")
            
        except Exception as e:
            self.logger.error(f"停止热键监听失败: {e}")
    
    def _start_keyboard_listener(self):
        """启动键盘监听器（用于ctrl、alt等键）"""
        try:
            from pynput import keyboard
            
            self._keyboard_listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release,
                suppress=False
            )
            self._keyboard_listener.daemon = True
            self._keyboard_listener.start()
            
        except Exception as e:
            self.logger.error(f"启动键盘监听器失败: {e}")
            raise
    
    def _start_fn_monitor(self):
        """启动fn键监听线程"""
        self._fn_monitor_thread = threading.Thread(
            target=self._fn_monitor_loop,
            daemon=True
        )
        self._fn_monitor_thread.start()
    
    def _fn_monitor_loop(self):
        """fn键监听循环 - 简化版本"""
        try:
            import Quartz
            
            while not self._should_stop:
                current_time = time.time()
                
                # 限制检查频率，减少CPU占用
                if current_time - self._last_check_time < self._check_interval:
                    time.sleep(0.01)
                    continue
                
                self._last_check_time = current_time
                
                # 检查fn键状态
                flags = Quartz.CGEventSourceFlagsState(
                    Quartz.kCGEventSourceStateHIDSystemState
                )
                fn_pressed = bool(flags & 0x800000)
                
                # 处理状态变化
                self._handle_fn_state_change(fn_pressed, current_time)
                
                # 适当休眠，避免过度占用CPU
                time.sleep(0.01)
                
        except Exception as e:
            self.logger.error(f"fn键监听循环出错: {e}")
        finally:
            self.logger.debug("fn键监听线程已退出")
    
    def _handle_fn_state_change(self, fn_pressed: bool, current_time: float):
        """处理fn键状态变化"""
        with self._state_lock:
            current_state = self._state
            
            if fn_pressed and current_state == HotkeyState.IDLE:
                # fn键按下
                if current_time - self._last_press_time > self._debounce_interval:
                    self._state = HotkeyState.PRESSED
                    self._last_press_time = current_time
                    self._trigger_press_callback()
                    
            elif not fn_pressed and current_state in [HotkeyState.PRESSED, HotkeyState.RECORDING]:
                # fn键释放
                if current_time - self._last_release_time > self._debounce_interval:
                    self._state = HotkeyState.IDLE
                    self._last_release_time = current_time
                    self._trigger_release_callback()
    
    def _on_key_press(self, key):
        """处理键盘按下事件"""
        if self._is_target_key(key):
            current_time = time.time()
            with self._state_lock:
                if (self._state == HotkeyState.IDLE and 
                    current_time - self._last_press_time > self._debounce_interval):
                    self._state = HotkeyState.PRESSED
                    self._last_press_time = current_time
                    self._trigger_press_callback()
    
    def _on_key_release(self, key):
        """处理键盘释放事件"""
        if self._is_target_key(key):
            current_time = time.time()
            with self._state_lock:
                if (self._state in [HotkeyState.PRESSED, HotkeyState.RECORDING] and
                    current_time - self._last_release_time > self._debounce_interval):
                    self._state = HotkeyState.IDLE
                    self._last_release_time = current_time
                    self._trigger_release_callback()
    
    def _is_target_key(self, key) -> bool:
        """检查是否是目标热键"""
        try:
            from pynput import keyboard
            
            if self._hotkey_type == HotkeyType.CTRL:
                return key in [keyboard.Key.ctrl_l, keyboard.Key.ctrl_r]
            elif self._hotkey_type == HotkeyType.ALT:
                return key in [keyboard.Key.alt_l, keyboard.Key.alt_r]
            elif self._hotkey_type == HotkeyType.CMD:
                return key in [keyboard.Key.cmd_l, keyboard.Key.cmd_r]
            
            return False
        except Exception:
            return False
    
    def _trigger_press_callback(self):
        """触发按下回调"""
        if self._press_callback:
            try:
                with self._state_lock:
                    self._state = HotkeyState.RECORDING
                
                # 在新线程中执行回调，避免阻塞监听
                threading.Thread(
                    target=self._press_callback,
                    daemon=True
                ).start()
                
            except Exception as e:
                self.logger.error(f"执行按下回调失败: {e}")
                with self._state_lock:
                    self._state = HotkeyState.IDLE
    
    def _trigger_release_callback(self):
        """触发释放回调"""
        if self._release_callback:
            try:
                # 在新线程中执行回调，避免阻塞监听
                threading.Thread(
                    target=self._release_callback,
                    daemon=True
                ).start()
                
            except Exception as e:
                self.logger.error(f"执行释放回调失败: {e}")
    
    def get_status(self) -> dict:
        """获取状态信息"""
        with self._state_lock:
            return {
                'active': not self._should_stop,
                'state': self._state.value,
                'hotkey_type': self._hotkey_type.value,
                'listener_running': self._keyboard_listener is not None,
                'fn_monitor_running': (self._fn_monitor_thread is not None and 
                                     self._fn_monitor_thread.is_alive())
            }
    
    def cleanup(self):
        """清理资源"""
        self.stop_listening()

# 使用示例
class Application:
    """应用程序示例"""
    
    def __init__(self):
        self.hotkey_manager = SimplifiedHotkeyManager()
        self.hotkey_manager.set_callbacks(
            press_callback=self.on_recording_start,
            release_callback=self.on_recording_stop
        )
    
    def on_recording_start(self):
        """开始录音"""
        print("开始录音")
        # 录音逻辑
    
    def on_recording_stop(self):
        """停止录音"""
        print("停止录音")
        # 停止录音逻辑
    
    def run(self):
        """运行应用"""
        self.hotkey_manager.start_listening()
        # 应用主循环
        
    def cleanup(self):
        """清理资源"""
        self.hotkey_manager.cleanup()
