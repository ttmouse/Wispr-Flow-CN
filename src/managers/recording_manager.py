#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
录音管理器
专门负责录音相关的所有操作
"""

import logging
import threading
import subprocess
from typing import Optional, Callable
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QApplication

from .component_manager import ComponentManager

class RecordingManager(QObject):
    """录音管理器 - 专门负责录音相关操作"""

    # 信号定义
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()
    transcription_completed = pyqtSignal(str)  # 转写完成信号
    recording_error = pyqtSignal(str)
    volume_changed = pyqtSignal(int)  # 音量变化信号

    def __init__(self, app_context):
        super().__init__()

        # 使用组合而不是继承
        self.component_manager = ComponentManager(name="录音管理器", app_context=app_context)

        # 添加logger
        self.logger = logging.getLogger(self.__class__.__name__)
        self.app_context = app_context
        
        # 录音组件
        self.audio_capture = None
        self.funasr_engine = None
        self.audio_capture_thread = None
        self.transcription_thread = None
        
        # 状态管理
        self.recording = False
        self.previous_volume = None
        self._recording_lock = threading.RLock()
        
        # 定时器
        self.recording_timer = None
        self.volume_timer = None
        
        # 回调函数
        self._transcription_callback: Optional[Callable] = None
        self._error_callback: Optional[Callable] = None

    # 委托ComponentManager的方法
    async def initialize(self):
        # 设置内部初始化方法
        self.component_manager._initialize_internal = self._initialize_internal
        self.component_manager._cleanup_internal = self._cleanup_internal
        return await self.component_manager.initialize()

    def start(self):
        return self.component_manager.start()

    def stop(self):
        return self.component_manager.stop()

    def cleanup(self):
        return self.component_manager.cleanup()

    def get_status(self):
        return self.component_manager.get_status()

    @property
    def state(self):
        return self.component_manager.state

    @property
    def is_initialized(self):
        return self.component_manager.is_initialized

    @property
    def is_running(self):
        return self.component_manager.is_running
    
    def set_callbacks(self,
                     transcription_callback: Optional[Callable] = None,
                     error_callback: Optional[Callable] = None):
        """设置回调函数"""
        self._transcription_callback = transcription_callback
        self._error_callback = error_callback
    
    async def _initialize_internal(self) -> bool:
        """初始化录音组件"""
        try:
            # 1. 初始化音频捕获
            if not await self._initialize_audio_capture():
                return False

            # 3. 创建音频捕获线程（按照原始代码逻辑）
            if not self._init_audio_capture_thread():
                return False
            
            # 2. 初始化FunASR引擎
            if not await self._initialize_funasr_engine():
                return False
            
            # 3. 定时器将在需要时延迟创建（避免线程问题）
            # self._initialize_timers()
            
            self.logger.info("录音组件初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"录音组件初始化失败: {e}")
            return False
    
    async def _initialize_audio_capture(self) -> bool:
        """初始化音频捕获"""
        try:
            from audio_capture import AudioCapture

            self.audio_capture = AudioCapture()

            self.logger.debug("音频捕获初始化成功")
            return True

        except Exception as e:
            self.logger.error(f"音频捕获初始化失败: {e}")
            return False

    def _init_audio_capture_thread(self) -> bool:
        """初始化音频捕获线程 - 按照原始代码逻辑"""
        try:
            from audio_threads import AudioCaptureThread
            self.audio_capture_thread = AudioCaptureThread(self.audio_capture)
            self.audio_capture_thread.audio_captured.connect(self._on_audio_captured)
            self.audio_capture_thread.recording_stopped.connect(self._on_recording_stopped)

            self.logger.debug("音频捕获线程初始化成功")
            return True

        except Exception as e:
            self.logger.error(f"音频捕获线程初始化失败: {e}")
            return False
    
    async def _initialize_funasr_engine(self) -> bool:
        """初始化FunASR引擎"""
        try:
            from funasr_engine import FunASREngine
            
            self.funasr_engine = FunASREngine()
            
            self.logger.debug("FunASR引擎初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"FunASR引擎初始化失败: {e}")
            return False
    
    def _ensure_timer_created(self):
        """确保定时器在主线程中创建"""
        try:
            # 只在主线程中创建定时器
            from PyQt6.QtCore import QThread
            if QThread.currentThread() != QApplication.instance().thread():
                self.logger.warning("定时器只能在主线程中创建")
                return

            # 如果定时器还未创建，则创建它们
            if not self.recording_timer:
                self.recording_timer = QTimer()
                self.recording_timer.setSingleShot(True)
                self.recording_timer.timeout.connect(self._on_recording_timeout)
                self.logger.debug("录音定时器创建成功")

            if not self.volume_timer:
                self.volume_timer = QTimer()
                self.volume_timer.setSingleShot(True)
                self.logger.debug("音量定时器创建成功")

        except Exception as e:
            self.logger.error(f"定时器创建失败: {e}")

    def _initialize_timers(self):
        """初始化定时器（已废弃，使用_ensure_timer_created）"""
        # 这个方法已废弃，定时器现在在需要时创建
        pass
    
    # 公共接口方法
    def start_recording(self) -> bool:
        """开始录音"""
        with self._recording_lock:
            if self.recording:
                self.logger.warning("录音已在进行中")
                return True
            
            try:
                self.logger.info("开始录音")
                
                # 1. 播放开始音效
                self._play_start_sound()
                
                # 2. 保存并静音系统音量
                self._save_and_mute_system_volume()
                
                # 3. 启动音频捕获线程
                if not self._start_audio_capture_thread():
                    return False
                
                # 4. 设置录音超时（在主线程中创建定时器）
                max_duration = self._get_max_recording_duration()
                self._ensure_timer_created()
                if self.recording_timer:
                    self.recording_timer.start(max_duration * 1000)  # 转换为毫秒
                
                # 5. 更新状态
                self.recording = True
                self.recording_started.emit()
                
                self.logger.info("录音启动成功")
                return True
                
            except Exception as e:
                self.logger.error(f"启动录音失败: {e}")
                self._handle_recording_error(f"启动录音失败: {e}")
                return False
    
    def stop_recording(self) -> bool:
        """停止录音"""
        with self._recording_lock:
            if not self.recording:
                self.logger.debug("录音未在进行中")
                return True
            
            try:
                self.logger.info("停止录音")
                
                # 1. 停止定时器
                if self.recording_timer:
                    self.recording_timer.stop()
                
                # 2. 停止音频捕获线程
                self._stop_audio_capture_thread()
                
                # 3. 播放停止音效
                self._play_stop_sound()
                
                # 4. 异步恢复系统音量
                self._restore_system_volume_async()
                
                # 5. 更新状态
                self.recording = False
                self.recording_stopped.emit()
                
                # 6. 处理音频数据
                self._process_recorded_audio()
                
                self.logger.info("录音停止成功")
                return True
                
            except Exception as e:
                self.logger.error(f"停止录音失败: {e}")
                self._handle_recording_error(f"停止录音失败: {e}")
                return False
    
    def is_recording(self) -> bool:
        """检查是否正在录音"""
        with self._recording_lock:
            return self.recording
    
    def is_ready_for_recording(self) -> bool:
        """检查是否准备好录音"""
        return (self.audio_capture is not None and 
                self.funasr_engine is not None and 
                hasattr(self.funasr_engine, 'is_ready') and self.funasr_engine.is_ready and
                not self.recording)
    
    def toggle_recording(self):
        """切换录音状态"""
        if self.recording:
            self.stop_recording()
        else:
            self.start_recording()
    
    # 内部方法将在下一个文件块中实现
    def _play_start_sound(self):
        """播放开始录音音效"""
        try:
            if (self.app_context and 
                hasattr(self.app_context, 'state_manager') and 
                self.app_context.state_manager):
                self.app_context.state_manager.start_recording()
        except Exception as e:
            self.logger.error(f"播放开始音效失败: {e}")
    
    def _play_stop_sound(self):
        """播放停止录音音效"""
        try:
            if (self.app_context and 
                hasattr(self.app_context, 'state_manager') and 
                self.app_context.state_manager):
                self.app_context.state_manager.stop_recording()
        except Exception as e:
            self.logger.error(f"播放停止音效失败: {e}")
    
    def _get_max_recording_duration(self) -> int:
        """获取最大录音时长"""
        try:
            if (self.app_context and
                hasattr(self.app_context, 'settings_manager') and
                self.app_context.settings_manager):
                return self.app_context.settings_manager.get_setting('audio.max_recording_duration', 10)
            return 10  # 默认10秒
        except Exception as e:
            self.logger.error(f"获取录音时长设置失败: {e}")
            return 10

    def _save_and_mute_system_volume(self):
        """保存当前系统音量并静音"""
        try:
            self.previous_volume = self._get_system_volume()
            if self.previous_volume is not None:
                self._set_system_volume(None)  # 静音
                self.logger.debug(f"系统音量已保存({self.previous_volume})并静音")
        except Exception as e:
            self.logger.error(f"保存并静音系统音量失败: {e}")

    def _restore_system_volume_async(self):
        """异步恢复系统音量 - 按照原始代码逻辑"""
        try:
            if self.previous_volume is not None:
                # 停止并清理之前的定时器（按照原始代码逻辑）
                if hasattr(self, 'volume_timer') and self.volume_timer:
                    self.volume_timer.stop()
                    self.volume_timer.deleteLater()

                # 保存音量值，避免在定时器回调前被重置
                volume_to_restore = self.previous_volume

                # 重新创建定时器（按照原始代码逻辑）
                from PyQt6.QtCore import QTimer
                self.volume_timer = QTimer()
                self.volume_timer.setSingleShot(True)
                self.volume_timer.timeout.connect(lambda: self._restore_volume(volume_to_restore))
                self.volume_timer.start(150)  # 150ms后恢复音量

                # 重置音量变量
                self.previous_volume = None
        except Exception as e:
            self.logger.error(f"异步恢复音量失败: {e}")

    def _restore_volume(self, volume):
        """恢复指定音量"""
        try:
            self._set_system_volume(volume)
            self.logger.debug(f"系统音量已恢复到: {volume}")
        except Exception as e:
            self.logger.error(f"恢复音量失败: {e}")

    def _get_system_volume(self):
        """获取当前系统音量"""
        try:
            result = subprocess.run([
                'osascript',
                '-e', 'get volume settings'
            ], capture_output=True, text=True, check=True)

            settings = result.stdout.strip()
            volume_str = settings.split(',')[0].split(':')[1].strip()
            muted = "output muted:true" in settings

            if muted:
                return 0

            volume = int(volume_str)
            return volume
        except subprocess.CalledProcessError as e:
            self.logger.error(f"获取系统音量失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"获取系统音量时发生错误: {e}")
            return None

    def _set_system_volume(self, volume):
        """设置系统音量"""
        try:
            if volume is None:
                # 静音
                subprocess.run([
                    'osascript',
                    '-e', 'set volume output muted true'
                ], check=True)
            else:
                # 设置音量并取消静音
                volume = max(0, min(100, volume))
                subprocess.run([
                    'osascript',
                    '-e', f'set volume output volume {volume}',
                    '-e', 'set volume output muted false'
                ], check=True)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"设置系统音量失败: {e}")
        except Exception as e:
            self.logger.error(f"设置系统音量时发生错误: {e}")

    def _start_audio_capture_thread(self) -> bool:
        """启动音频捕获线程 - 按照原始代码逻辑"""
        try:
            # 按照原始代码逻辑：重新初始化录音线程（如果之前已经使用过）
            if self.audio_capture_thread and self.audio_capture_thread.isFinished():
                from audio_threads import AudioCaptureThread
                self.audio_capture_thread = AudioCaptureThread(self.audio_capture)
                self.audio_capture_thread.audio_captured.connect(self._on_audio_captured)
                self.audio_capture_thread.recording_stopped.connect(self._on_recording_stopped)

            # 启动录音线程
            if self.audio_capture_thread:
                self.audio_capture_thread.start()
                self.logger.debug("音频捕获线程启动成功")
                return True
            else:
                self.logger.error("音频捕获线程未初始化")
                return False

        except Exception as e:
            self.logger.error(f"启动音频捕获线程失败: {e}")
            return False

    def _stop_audio_capture_thread(self):
        """停止音频捕获线程"""
        try:
            if self.audio_capture_thread and self.audio_capture_thread.isRunning():
                self.audio_capture_thread.stop()
                self.audio_capture_thread.wait()
                self.logger.debug("音频捕获线程停止成功")
        except Exception as e:
            self.logger.error(f"停止音频捕获线程失败: {e}")

    def _process_recorded_audio(self):
        """处理录制的音频数据"""
        try:
            if not self.audio_capture:
                self.logger.warning("音频捕获组件未初始化")
                return

            audio_data = self.audio_capture.get_audio_data()

            if len(audio_data) > 0:
                if not (self.funasr_engine and hasattr(self.funasr_engine, 'is_ready') and self.funasr_engine.is_ready):
                    self.logger.warning("FunASR引擎尚未就绪，无法处理录音")
                    return

                self._start_transcription(audio_data)
            else:
                self.logger.warning("未检测到声音")

        except Exception as e:
            self.logger.error(f"处理录制音频失败: {e}")
            self._handle_recording_error(f"处理录制音频失败: {e}")

    def _start_transcription(self, audio_data):
        """启动转写"""
        try:
            from audio_threads import TranscriptionThread

            self.transcription_thread = TranscriptionThread(audio_data, self.funasr_engine)
            self.transcription_thread.transcription_done.connect(self._on_transcription_done)
            self.transcription_thread.start()

            self.logger.debug("转写线程启动成功")

        except Exception as e:
            self.logger.error(f"启动转写失败: {e}")
            self._handle_recording_error(f"启动转写失败: {e}")

    def _on_audio_captured(self, data):
        """音频数据捕获回调"""
        # 录音过程中不需要频繁更新状态
        pass

    def _on_recording_stopped(self):
        """处理录音停止信号"""
        self.logger.debug("收到录音停止信号")

    def _on_transcription_done(self, text):
        """转写完成的回调"""
        try:
            if text and text.strip():
                self.logger.info(f"转写完成: {text[:50]}...")

                # 发送信号
                self.transcription_completed.emit(text)

                # 调用回调
                if self._transcription_callback:
                    self._transcription_callback(text)

        except Exception as e:
            self.logger.error(f"处理转写结果失败: {e}")

    def _on_recording_timeout(self):
        """处理录音超时"""
        self.logger.warning("录音超时，自动停止")
        self.stop_recording()

    def _handle_recording_error(self, error_message: str):
        """处理录音错误"""
        self.recording_error.emit(error_message)

        if self._error_callback:
            self._error_callback(error_message)

    def _cleanup_internal(self):
        """清理录音资源"""
        try:
            # 停止录音
            if self.recording:
                self.stop_recording()

            # 清理定时器
            if self.recording_timer:
                self.recording_timer.stop()
                self.recording_timer = None

            if self.volume_timer:
                self.volume_timer.stop()
                self.volume_timer = None

            # 清理转写线程
            if self.transcription_thread and self.transcription_thread.isRunning():
                self.transcription_thread.quit()
                self.transcription_thread.wait()
                self.transcription_thread = None

            # 清理音频捕获线程
            self._stop_audio_capture_thread()
            self.audio_capture_thread = None

            # 清理音频组件
            if self.audio_capture:
                if hasattr(self.audio_capture, 'cleanup'):
                    self.audio_capture.cleanup()
                self.audio_capture = None

            if self.funasr_engine:
                if hasattr(self.funasr_engine, 'cleanup'):
                    self.funasr_engine.cleanup()
                self.funasr_engine = None

            # 恢复系统音量
            if self.previous_volume is not None:
                self._set_system_volume(self.previous_volume)
                self.previous_volume = None

            self.logger.debug("录音资源清理完成")

        except Exception as e:
            self.logger.error(f"录音资源清理失败: {e}")
