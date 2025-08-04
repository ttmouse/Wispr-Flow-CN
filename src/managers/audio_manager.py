#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频管理器
专门负责音频相关操作
"""

import logging
import threading
from typing import Optional, Callable
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from .component_manager import ComponentManager

class AudioManager(QObject):
    """音频管理器 - 专门负责音频相关操作"""

    # 信号定义
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()
    transcription_completed = pyqtSignal(str, str)  # text, language
    audio_error = pyqtSignal(str)

    def __init__(self, app_context):
        super().__init__()

        # 使用组合而不是继承
        self.component_manager = ComponentManager(name="音频管理器", app_context=app_context)

        # 添加logger
        self.logger = logging.getLogger(self.__class__.__name__)
        self.app_context = app_context
        
        # 音频组件
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
        
        # 回调函数
        self._transcription_callback: Optional[Callable] = None
        self._error_callback: Optional[Callable] = None

    # 委托ComponentManager的方法
    def initialize_sync(self):
        """同步初始化音频管理器"""
        try:
            return self._initialize_internal_sync()
        except Exception as e:
            self.logger.error(f"音频管理器同步初始化失败: {e}")
            return False

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

    def _initialize_internal_sync(self) -> bool:
        """同步初始化音频组件"""
        try:
            # 1. 初始化音频捕获
            if not self._initialize_audio_capture_sync():
                return False

            # 2. 初始化FunASR引擎
            if not self._initialize_funasr_engine_sync():
                return False

            # 3. 初始化录音定时器
            self._initialize_timers()

            # 4. 初始化音频捕获线程（与原始代码一致）
            if not self._initialize_audio_capture_thread():
                return False

            self.logger.info("音频组件同步初始化完成")
            return True

        except Exception as e:
            self.logger.error(f"音频组件同步初始化失败: {e}")
            return False

    async def _initialize_internal(self) -> bool:
        """初始化音频组件"""
        try:
            # 1. 初始化音频捕获
            if not await self._initialize_audio_capture():
                return False
            
            # 2. 初始化FunASR引擎
            if not await self._initialize_funasr_engine():
                return False
            
            # 3. 初始化定时器
            self._initialize_timers()
            
            self.logger.info("音频组件初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"音频组件初始化失败: {e}")
            return False

    def _initialize_audio_capture_sync(self) -> bool:
        """同步初始化音频捕获"""
        try:
            from audio_capture import AudioCapture

            self.audio_capture = AudioCapture()

            # 设置音频捕获回调
            if hasattr(self.audio_capture, 'set_callback'):
                self.audio_capture.set_callback(self._on_audio_data_received)

            self.logger.debug("音频捕获同步初始化成功")
            return True

        except Exception as e:
            self.logger.error(f"音频捕获同步初始化失败: {e}")
            return False

    def _initialize_funasr_engine_sync(self) -> bool:
        """同步初始化FunASR引擎"""
        try:
            from funasr_engine import FunASREngine

            # 获取设置管理器
            settings_manager = None
            if (self.app_context and
                hasattr(self.app_context, 'settings_manager') and
                self.app_context.settings_manager):
                settings_manager = self.app_context.settings_manager

            self.funasr_engine = FunASREngine(settings_manager)

            # 设置转写回调
            if hasattr(self.funasr_engine, 'set_callback'):
                self.funasr_engine.set_callback(self._on_transcription_completed)

            self.logger.debug("FunASR引擎同步初始化成功")
            return True

        except Exception as e:
            self.logger.error(f"FunASR引擎同步初始化失败: {e}")
            return False

    async def _initialize_audio_capture(self) -> bool:
        """初始化音频捕获"""
        try:
            from audio_capture import AudioCapture
            
            self.audio_capture = AudioCapture()
            
            # 设置音频捕获回调
            if hasattr(self.audio_capture, 'set_callback'):
                self.audio_capture.set_callback(self._on_audio_data_received)
            
            self.logger.debug("音频捕获初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"音频捕获初始化失败: {e}")
            return False
    
    async def _initialize_funasr_engine(self) -> bool:
        """初始化FunASR引擎"""
        try:
            from funasr_engine import FunASREngine
            
            self.funasr_engine = FunASREngine()
            
            # 设置转写回调
            if hasattr(self.funasr_engine, 'set_callback'):
                self.funasr_engine.set_callback(self._on_transcription_completed)
            
            self.logger.debug("FunASR引擎初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"FunASR引擎初始化失败: {e}")
            return False

    def _initialize_audio_capture_thread_sync(self) -> bool:
        """同步初始化音频捕获线程"""
        try:
            from audio_threads import AudioCaptureThread

            if self.audio_capture:
                self.audio_capture_thread = AudioCaptureThread(self.audio_capture)
                self.logger.debug("音频捕获线程同步初始化成功")
                return True
            else:
                self.logger.error("音频捕获未初始化，无法创建音频捕获线程")
                return False

        except Exception as e:
            self.logger.error(f"音频捕获线程同步初始化失败: {e}")
            return False

    def _initialize_audio_capture_thread(self) -> bool:
        """初始化音频捕获线程（与原始代码一致）"""
        return self._initialize_audio_capture_thread_sync()

    def _initialize_timers(self):
        """初始化定时器"""
        try:
            self.recording_timer = QTimer(self)  # 指定父对象
            self.recording_timer.setSingleShot(True)
            self.recording_timer.timeout.connect(self._on_recording_timeout)

            self.logger.debug("定时器初始化成功")

        except Exception as e:
            self.logger.error(f"定时器初始化失败: {e}")
    
    # 公共接口方法
    def is_ready_for_recording(self):
        """检查是否准备好录音（与原始代码一致）"""
        return (self.audio_capture_thread is not None and
                self.funasr_engine is not None and
                hasattr(self.funasr_engine, 'is_ready') and self.funasr_engine.is_ready and
                (self.app_context and hasattr(self.app_context, 'state_manager') and self.app_context.state_manager) and
                not self.recording)

    def start_recording(self) -> bool:
        """开始录音（与原始代码完全一致）"""
        with self._recording_lock:
            try:
                # 使用统一的状态检查方法（与原始代码一致）
                if not self.is_ready_for_recording():
                    return False

                if not self.recording:
                    self.recording = True

                    try:
                        # 先播放音效，让用户立即听到反馈（与原始代码一致）
                        if (self.app_context and
                            hasattr(self.app_context, 'state_manager') and
                            self.app_context.state_manager):
                            self.app_context.state_manager.start_recording()

                        # 然后保存当前音量并静音系统（与原始代码一致）
                        self.previous_volume = self._get_system_volume()
                        if self.previous_volume is not None:
                            self._set_system_volume(None)  # 静音

                        # 重新初始化录音线程（如果之前已经使用过）（与原始代码一致）
                        if self.audio_capture_thread and self.audio_capture_thread.isFinished():
                            from audio_threads import AudioCaptureThread
                            self.audio_capture_thread = AudioCaptureThread(self.audio_capture)
                            self.audio_capture_thread.audio_captured.connect(self.on_audio_captured)
                            self.audio_capture_thread.recording_stopped.connect(self.stop_recording)
                        elif not self.audio_capture_thread:
                            # 首次创建录音线程
                            from audio_threads import AudioCaptureThread
                            self.audio_capture_thread = AudioCaptureThread(self.audio_capture)
                            self.audio_capture_thread.audio_captured.connect(self.on_audio_captured)
                            self.audio_capture_thread.recording_stopped.connect(self.stop_recording)

                        # 启动录音线程（与原始代码一致）
                        self.audio_capture_thread.start()

                        # 从设置中获取录音时长并设置定时器，自动停止录音（与原始代码一致）
                        if hasattr(self, 'recording_timer') and self.recording_timer:
                            self.recording_timer.stop()
                            self.recording_timer.deleteLater()

                        # 确保定时器在主线程中创建（与原始代码一致）
                        settings_manager = None
                        if (self.app_context and
                            hasattr(self.app_context, 'settings_manager')):
                            settings_manager = self.app_context.settings_manager

                        max_duration = 10  # 默认值
                        if settings_manager:
                            max_duration = settings_manager.get_setting('audio.max_recording_duration', 10)

                        from PyQt6.QtCore import QTimer
                        self.recording_timer = QTimer(self)  # 指定父对象
                        self.recording_timer.setSingleShot(True)
                        self.recording_timer.timeout.connect(self._auto_stop_recording)
                        self.recording_timer.start(max_duration * 1000)  # 转换为毫秒

                        self.logger.info("录音已开始")
                        return True

                    except Exception as e:
                        error_msg = f"开始录音时出错: {str(e)}"
                        self.logger.error(error_msg)
                        self._handle_audio_error(error_msg)
                        return False

            except Exception as e:
                import traceback
                error_msg = f"start_recording线程安全异常: {str(e)}"
                self.logger.error(f"{error_msg}")
                self.logger.error(f"当前线程: {threading.current_thread().name}")
                self.logger.error(f"详细堆栈: {traceback.format_exc()}")
                self._handle_audio_error(error_msg)
                return False

    def _get_system_volume(self):
        """获取当前系统音量（与原始代码一致）"""
        try:
            import subprocess
            # 获取完整的音量设置
            result = subprocess.run([
                'osascript',
                '-e', 'get volume settings'
            ], capture_output=True, text=True, check=True)

            settings = result.stdout.strip()
            # 解析输出，格式类似：output volume:50, input volume:75, alert volume:75, output muted:false
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
        """设置系统音量（与原始代码一致）
        volume: 0-100 的整数，或者 None 表示静音"""
        try:
            import subprocess
            if volume is None:
                # 直接静音，不检查当前状态以减少延迟
                subprocess.run([
                    'osascript',
                    '-e', 'set volume output muted true'
                ], check=True)
            else:
                # 设置音量并取消静音
                volume = max(0, min(100, volume))  # 确保音量在 0-100 范围内
                subprocess.run([
                    'osascript',
                    '-e', f'set volume output volume {volume}',
                    '-e', 'set volume output muted false'
                ], check=True)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"设置系统音量失败: {e}")
        except Exception as e:
            self.logger.error(f"设置系统音量时发生错误: {e}")

    def on_audio_captured(self, data):
        """音频数据捕获回调（与原始代码一致）"""
        # 录音过程中不需要频繁更新状态，因为状态已经在start_recording时设置了
        pass

    def _auto_stop_recording(self):
        """定时器触发的自动停止录音（与原始代码一致）"""
        try:
            if self.recording:
                self.logger.info("录音时间达到最大时长，自动停止录音")
                self.stop_recording()
        except Exception as e:
            # 静默处理异常，避免在定时器回调中抛出异常
            self.logger.error(f"自动停止录音失败: {e}")

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
                
                # 2. 停止音频捕获线程（音频数据将通过信号传递）
                # AudioCaptureThread会自动调用stop_recording并发送最终音频数据
                
                # 3. 停止音频捕获线程
                self._stop_audio_capture_thread()
                
                # 4. 恢复系统音量
                self._restore_system_volume()
                
                # 5. 更新状态
                self.recording = False
                self.recording_stopped.emit()
                
                self.logger.info("录音停止成功")
                return True
                
            except Exception as e:
                self.logger.error(f"停止录音失败: {e}")
                self._handle_audio_error(f"停止录音失败: {e}")
                return False
    
    def is_recording(self) -> bool:
        """检查是否正在录音"""
        with self._recording_lock:
            return self.recording
    
    # 内部方法
    def _start_audio_capture_thread(self):
        """启动音频捕获线程"""
        try:
            if self.audio_capture_thread and self.audio_capture_thread.isRunning():
                self.logger.warning("音频捕获线程已在运行")
                return

            # 使用现有的AudioCaptureThread
            from audio_threads import AudioCaptureThread

            self.audio_capture_thread = AudioCaptureThread(self.audio_capture)
            # 连接信号
            self.audio_capture_thread.audio_captured.connect(self._on_audio_data_received)
            self.audio_capture_thread.recording_stopped.connect(self._on_recording_stopped)

            self.audio_capture_thread.start()

            self.logger.debug("音频捕获线程启动成功")

        except Exception as e:
            self.logger.error(f"启动音频捕获线程失败: {e}")
            import traceback
            self.logger.error(f"错误详情: {traceback.format_exc()}")
    
    def _stop_audio_capture_thread(self):
        """停止音频捕获线程"""
        try:
            if self.audio_capture_thread and self.audio_capture_thread.isRunning():
                # 先尝试优雅退出
                self.audio_capture_thread.requestInterruption()
                self.audio_capture_thread.quit()
                
                # 等待线程结束
                if not self.audio_capture_thread.wait(5000):  # 等待5秒
                    self.logger.warning("音频捕获线程未能在5秒内退出，强制终止")
                    self.audio_capture_thread.terminate()
                    self.audio_capture_thread.wait(2000)  # 再等待2秒
                
                self.logger.debug("音频捕获线程停止成功")
            
        except Exception as e:
            self.logger.error(f"停止音频捕获线程失败: {e}")
    
    def _save_system_volume(self):
        """保存当前系统音量"""
        try:
            # 这里应该实现获取系统音量的逻辑
            # self.previous_volume = get_system_volume()
            pass
        except Exception as e:
            self.logger.error(f"保存系统音量失败: {e}")
    
    def _restore_system_volume(self):
        """恢复系统音量"""
        try:
            if self.previous_volume is not None:
                # 这里应该实现设置系统音量的逻辑
                # set_system_volume(self.previous_volume)
                self.previous_volume = None
        except Exception as e:
            self.logger.error(f"恢复系统音量失败: {e}")
    
    def _on_audio_data_received(self, audio_data):
        """处理接收到的音频数据（来自AudioCaptureThread）"""
        try:
            # 安全地检查音频数据
            data_length = 'None'
            data_valid = False
            
            if audio_data is not None:
                try:
                    data_length = len(audio_data)
                    data_valid = data_length > 0
                except (TypeError, ValueError):
                    # 如果是numpy数组或其他类型，尝试不同的方法
                    try:
                        import numpy as np
                        if isinstance(audio_data, np.ndarray):
                            data_length = audio_data.size
                            data_valid = audio_data.size > 0
                        else:
                            data_length = 'unknown'
                            data_valid = True  # 假设有数据
                    except:
                        data_length = 'unknown'
                        data_valid = True
            
            self.logger.info(f"通过信号接收到音频数据: {type(audio_data)}, 长度: {data_length}")

            if data_valid:
                # 启动转写
                self._process_audio_data(audio_data)
            else:
                self.logger.warning("接收到的音频数据为空")

        except Exception as e:
            self.logger.error(f"处理音频数据失败: {e}")
            import traceback
            self.logger.error(f"错误详情: {traceback.format_exc()}")
            self._handle_audio_error(f"处理音频数据失败: {e}")

    def _on_recording_stopped(self):
        """处理录音停止信号"""
        try:
            self.logger.info("收到录音停止信号")
            # 这里可以添加录音停止后的清理工作

        except Exception as e:
            self.logger.error(f"处理录音停止信号失败: {e}")
    
    def _start_transcription(self, audio_data):
        """启动转写"""
        try:
            from PyQt6.QtCore import QThread
            
            class TranscriptionThread(QThread):
                transcription_completed = pyqtSignal(str, str)
                transcription_error = pyqtSignal(str)
                
                def __init__(self, funasr_engine, audio_data):
                    super().__init__()
                    self.funasr_engine = funasr_engine
                    self.audio_data = audio_data
                
                def run(self):
                    try:
                        # 检查是否被中断
                        if self.isInterruptionRequested():
                            return
                            
                        if self.funasr_engine:
                            result = self.funasr_engine.transcribe(self.audio_data)
                            
                            # 再次检查是否被中断
                            if self.isInterruptionRequested():
                                return
                                
                            if result:
                                # 处理不同类型的结果
                                if isinstance(result, list) and len(result) > 0:
                                    first_result = result[0]
                                    if isinstance(first_result, dict):
                                        text = first_result.get('text', '')
                                        language = first_result.get('language', 'zh')
                                    else:
                                        text = str(first_result)
                                        language = 'zh'
                                elif isinstance(result, dict):
                                    text = result.get('text', '')
                                    language = result.get('language', 'zh')
                                else:
                                    text = str(result)
                                    language = 'zh'

                                # 最后检查是否被中断
                                if not self.isInterruptionRequested():
                                    self.transcription_completed.emit(text, language)
                    except Exception as e:
                        if not self.isInterruptionRequested():
                            self.transcription_error.emit(str(e))
            
            self.transcription_thread = TranscriptionThread(self.funasr_engine, audio_data)
            self.transcription_thread.transcription_completed.connect(self._on_transcription_completed)
            self.transcription_thread.transcription_error.connect(self._on_transcription_error)
            self.transcription_thread.start()
            
        except Exception as e:
            self.logger.error(f"启动转写失败: {e}")
            self._handle_audio_error(f"启动转写失败: {e}")
    
    def _on_transcription_completed(self, text: str, language: str):
        """处理转写完成"""
        try:
            self.logger.info(f"转写完成: {text[:50]}...")
            
            # 发送信号
            self.transcription_completed.emit(text, language)
            
            # 调用回调
            if self._transcription_callback:
                self._transcription_callback(text, language)
                
        except Exception as e:
            self.logger.error(f"处理转写结果失败: {e}")
    
    def _on_transcription_error(self, error_message: str):
        """处理转写错误"""
        self.logger.error(f"转写错误: {error_message}")
        self._handle_audio_error(f"转写错误: {error_message}")
    
    def _process_audio_data(self, audio_data):
        """处理音频数据"""
        try:
            self.logger.info(f"_process_audio_data 被调用，音频数据长度: {len(audio_data) if audio_data is not None else 'None'}")
            self.logger.info(f"FunASR引擎状态: {self.funasr_engine is not None}")

            if self.funasr_engine and audio_data is not None:
                self.logger.info("开始处理音频数据")
                # 启动转写
                self._start_transcription(audio_data)
            else:
                if not self.funasr_engine:
                    self.logger.warning("FunASR引擎未初始化")
                if audio_data is None:
                    self.logger.warning("音频数据为空")
        except Exception as e:
            self.logger.error(f"处理音频数据失败: {e}")
            import traceback
            self.logger.error(f"错误详情: {traceback.format_exc()}")
            self._handle_audio_error(f"处理音频数据失败: {e}")

    def _on_recording_timeout(self):
        """处理录音超时"""
        self.logger.warning("录音超时，自动停止")
        self.stop_recording()
    
    def _handle_audio_error(self, error_message: str):
        """处理音频错误"""
        self.audio_error.emit(error_message)
        
        if self._error_callback:
            self._error_callback(error_message)
    
    def _cleanup_internal(self):
        """清理音频资源"""
        try:
            # 停止录音
            if self.recording:
                self.stop_recording()
            
            # 清理定时器
            if self.recording_timer:
                self.recording_timer.stop()
                self.recording_timer = None
            
            # 清理转写线程
            if self.transcription_thread and self.transcription_thread.isRunning():
                # 先尝试优雅退出
                self.transcription_thread.requestInterruption()
                self.transcription_thread.quit()
                
                # 等待线程结束
                if not self.transcription_thread.wait(3000):  # 等待3秒
                    self.logger.warning("转写线程未能在3秒内退出，强制终止")
                    self.transcription_thread.terminate()
                    self.transcription_thread.wait(1000)  # 再等待1秒
                
                self.transcription_thread = None
            
            # 清理音频捕获线程
            self._stop_audio_capture_thread()
            self.audio_capture_thread = None
            
            # 清理音频组件
            if self.audio_capture:
                self.audio_capture.cleanup()
                self.audio_capture = None
            
            if self.funasr_engine:
                self.funasr_engine.cleanup()
                self.funasr_engine = None
            
            self.logger.debug("音频资源清理完成")
            
        except Exception as e:
            self.logger.error(f"音频资源清理失败: {e}")
