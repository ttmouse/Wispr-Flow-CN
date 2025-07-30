#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频处理模块
直接从原始Application类中提取音频相关的所有逻辑
保持完全相同的行为和接口
"""

import logging
import threading
from PyQt6.QtCore import QTimer, QThread, QApplication
from PyQt6.QtWidgets import QSystemTrayIcon


class AudioHandler:
    """音频处理器 - 直接替换原始Application类中的音频相关方法"""
    
    def __init__(self, app_instance):
        """
        初始化音频处理器
        
        Args:
            app_instance: Application实例的引用，用于访问所有原始属性和方法
        """
        self.app = app_instance
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 直接使用app实例的属性，保持原始行为
        # 不在这里创建新的属性，完全依赖原始Application实例
    
    def start_recording(self):
        """开始录音 - 原始逻辑的直接移植"""
        with self.app._app_lock:
            try:
                # 使用统一的状态检查方法
                if not self.is_ready_for_recording():
                    return
                    
                if not self.app.recording:
                    self.app.recording = True
                    
                    try:
                        # 先播放音效，让用户立即听到反馈
                        self.app.state_manager.start_recording()
                        
                        # 然后保存当前音量并静音系统
                        self.app.previous_volume = self._get_system_volume()
                        if self.app.previous_volume is not None:
                            self._set_system_volume(None)  # 静音
                        
                        # 重新初始化录音线程（如果之前已经使用过）
                        if self.app.audio_capture_thread.isFinished():
                            from audio_threads import AudioCaptureThread
                            self.app.audio_capture_thread = AudioCaptureThread(self.app.audio_capture)
                            self.app.audio_capture_thread.audio_captured.connect(self.on_audio_captured)
                            self.app.audio_capture_thread.recording_stopped.connect(self.stop_recording)
                        
                        # 启动录音线程
                        self.app.audio_capture_thread.start()
                        
                        # 从设置中获取录音时长并设置定时器，自动停止录音
                        if hasattr(self.app, 'recording_timer'):
                            self.app.recording_timer.stop()
                            self.app.recording_timer.deleteLater()
                        
                        # 确保定时器在主线程中创建，设置parent为self.app
                        max_duration = self.app.settings_manager.get_setting('audio.max_recording_duration', 10)
                        self.app.recording_timer = QTimer(self.app)
                        self.app.recording_timer.setSingleShot(True)
                        self.app.recording_timer.timeout.connect(self._auto_stop_recording)
                        self.app.recording_timer.start(max_duration * 1000)  # 转换为毫秒
                        
                    except Exception as e:
                        error_msg = f"开始录音时出错: {str(e)}"
                        self.logger.error(error_msg)
                        self.app.update_ui_signal.emit(f"❌ {error_msg}", "")
                        
            except Exception as e:
                import traceback
                error_msg = f"start_recording线程安全异常: {str(e)}"
                self.logger.error(f"{error_msg}")
                self.logger.error(f"当前线程: {threading.current_thread().name}")
                self.logger.error(f"详细堆栈: {traceback.format_exc()}")
                self.app.update_ui_signal.emit(f"❌ {error_msg}", "")

    def stop_recording(self):
        """停止录音 - 原始逻辑的直接移植"""
        if self._can_stop_recording():
            self.app.recording = False
            
            # 停止定时器
            if hasattr(self.app, 'recording_timer') and self.app.recording_timer.isActive():
                self.app.recording_timer.stop()
            
            # 检查录音线程是否存在
            if self.app.audio_capture_thread:
                self.app.audio_capture_thread.stop()
                self.app.audio_capture_thread.wait()
            
            # 播放停止音效（先播放音效，再恢复音量）
            self.app.state_manager.stop_recording()
            
            # 异步恢复音量，避免阻塞主线程
            if self.app.previous_volume is not None:
                # 使用QTimer延迟恢复音量，确保音效播放完成
                # 将定时器保存为实例变量，避免被垃圾回收
                if hasattr(self.app, 'volume_timer'):
                    self.app.volume_timer.stop()
                    self.app.volume_timer.deleteLater()
                
                # 保存音量值，避免在定时器回调前被重置
                volume_to_restore = self.app.previous_volume
                self.app.volume_timer = QTimer(self.app)
                self.app.volume_timer.setSingleShot(True)
                self.app.volume_timer.timeout.connect(lambda: self._restore_volume_async(volume_to_restore))
                self.app.volume_timer.start(150)  # 150ms后恢复音量
                
                # 重置 previous_volume
                self.app.previous_volume = None
            
            try:
                audio_data = self.app.audio_capture.get_audio_data()
                
                if len(audio_data) > 0:
                    # 使用统一的状态检查方法
                    if not self.app.is_component_ready('funasr_engine', 'is_ready'):
                        self.app.update_ui_signal.emit("⚠️ 语音识别引擎尚未就绪，无法处理录音", "")
                        return
                        
                    from audio_threads import TranscriptionThread
                    self.app.transcription_thread = TranscriptionThread(audio_data, self.app.funasr_engine)
                    self.app.transcription_thread.transcription_done.connect(self.app.on_transcription_done)
                    self.app.transcription_thread.start()
                else:
                    self.app.update_ui_signal.emit("❌ 未检测到声音", "")
            except Exception as e:
                self.logger.error(f"录音失败: {e}")
                self.app.update_ui_signal.emit(f"❌ 录音失败: {e}", "")
    
    def on_audio_captured(self, data):
        """音频数据捕获回调 - 原始逻辑的直接移植"""
        # 录音过程中不需要频繁更新状态，因为状态已经在start_recording时设置了
        pass
    
    def toggle_recording(self):
        """切换录音状态 - 原始逻辑的直接移植"""
        if self._can_start_recording():
            self.start_recording()
        elif self._can_stop_recording():
            self.stop_recording()
    
    def is_ready_for_recording(self):
        """检查是否准备好录音 - 原始逻辑的直接移植"""
        return (self.app.audio_capture_thread is not None and 
                self.app.funasr_engine is not None and 
                hasattr(self.app.funasr_engine, 'is_ready') and self.app.funasr_engine.is_ready and
                self.app.state_manager is not None and
                not self.app.recording)
    
    def _can_start_recording(self):
        """统一的录音开始条件检查 - 原始逻辑的直接移植"""
        return not self.app.recording
    
    def _can_stop_recording(self):
        """统一的录音停止条件检查 - 原始逻辑的直接移植"""
        return self.app.recording
    
    def _auto_stop_recording(self):
        """定时器触发的自动停止录音 - 原始逻辑的直接移植"""
        try:
            # 在打包后的应用中，避免在定时器回调中直接使用print
            # 使用信号来安全地更新UI或记录日志
            if self._can_stop_recording():
                # 发送信号到主线程进行UI更新
                self.app.update_ui_signal.emit("⏰ 录音时间达到最大时长，自动停止录音", "")
                self.stop_recording()
            # 不在录音状态时不需要特别处理
        except Exception as e:
            # 静默处理异常，避免在定时器回调中抛出异常
            pass
    
    def _set_system_volume(self, volume):
        """设置系统音量 - 原始逻辑的直接移植"""
        import subprocess
        try:
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

    def _get_system_volume(self):
        """获取当前系统音量 - 原始逻辑的直接移植"""
        import subprocess
        try:
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
    
    def _restore_volume_async(self, volume):
        """异步恢复音量 - 原始逻辑的直接移植"""
        try:
            self._set_system_volume(volume)
        except Exception as e:
            self.logger.error(f"异步恢复音量失败: {e}")
