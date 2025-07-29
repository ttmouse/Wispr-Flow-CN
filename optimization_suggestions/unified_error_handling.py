#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一错误处理和日志系统
解决错误处理不一致问题
"""

import functools
import logging
import traceback
import sys
from typing import Callable, Any, Optional, Type, Union
from enum import Enum
from contextlib import contextmanager
from datetime import datetime

class ErrorLevel(Enum):
    """错误级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class ErrorCategory(Enum):
    """错误分类"""
    AUDIO = "AUDIO"
    UI = "UI"
    HOTKEY = "HOTKEY"
    MODEL = "MODEL"
    SYSTEM = "SYSTEM"
    NETWORK = "NETWORK"

class ErrorHandler:
    """统一错误处理器"""
    
    def __init__(self):
        self.logger = logging.getLogger('ErrorHandler')
        self._error_callbacks = {}
        self._error_stats = {}
    
    def register_error_callback(self, category: ErrorCategory, callback: Callable):
        """注册错误回调"""
        if category not in self._error_callbacks:
            self._error_callbacks[category] = []
        self._error_callbacks[category].append(callback)
    
    def handle_error(self, 
                    error: Exception, 
                    category: ErrorCategory,
                    context: str = "",
                    level: ErrorLevel = ErrorLevel.ERROR,
                    user_message: Optional[str] = None):
        """处理错误"""
        
        # 记录错误统计
        error_key = f"{category.value}_{type(error).__name__}"
        self._error_stats[error_key] = self._error_stats.get(error_key, 0) + 1
        
        # 构建错误信息
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'category': category.value,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'traceback': traceback.format_exc(),
            'count': self._error_stats[error_key]
        }
        
        # 记录日志
        log_message = f"[{category.value}] {context}: {error}"
        if level == ErrorLevel.DEBUG:
            self.logger.debug(log_message)
        elif level == ErrorLevel.INFO:
            self.logger.info(log_message)
        elif level == ErrorLevel.WARNING:
            self.logger.warning(log_message)
        elif level == ErrorLevel.ERROR:
            self.logger.error(log_message)
        elif level == ErrorLevel.CRITICAL:
            self.logger.critical(log_message)
        
        # 调用注册的回调
        if category in self._error_callbacks:
            for callback in self._error_callbacks[category]:
                try:
                    callback(error_info, user_message)
                except Exception as callback_error:
                    self.logger.error(f"错误回调执行失败: {callback_error}")
    
    def get_error_stats(self) -> dict:
        """获取错误统计"""
        return self._error_stats.copy()

# 全局错误处理器实例
error_handler = ErrorHandler()

def handle_errors(category: ErrorCategory,
                 context: str = "",
                 level: ErrorLevel = ErrorLevel.ERROR,
                 default_return: Any = None,
                 user_message: Optional[str] = None,
                 reraise: bool = False):
    """错误处理装饰器"""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 构建上下文信息
                func_context = f"{func.__name__}({context})" if context else func.__name__
                
                # 处理错误
                error_handler.handle_error(
                    error=e,
                    category=category,
                    context=func_context,
                    level=level,
                    user_message=user_message
                )
                
                # 是否重新抛出异常
                if reraise:
                    raise
                
                return default_return
        return wrapper
    return decorator

@contextmanager
def error_context(category: ErrorCategory,
                 context: str = "",
                 level: ErrorLevel = ErrorLevel.ERROR,
                 user_message: Optional[str] = None,
                 reraise: bool = False):
    """错误处理上下文管理器"""
    try:
        yield
    except Exception as e:
        error_handler.handle_error(
            error=e,
            category=category,
            context=context,
            level=level,
            user_message=user_message
        )
        
        if reraise:
            raise

class SafeExecutor:
    """安全执行器"""
    
    @staticmethod
    def execute(func: Callable,
               *args,
               category: ErrorCategory,
               context: str = "",
               default_return: Any = None,
               **kwargs) -> Any:
        """安全执行函数"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_handler.handle_error(
                error=e,
                category=category,
                context=f"SafeExecutor.{func.__name__}({context})"
            )
            return default_return

# 特定类别的装饰器
def handle_audio_errors(context: str = "", default_return: Any = None):
    """音频错误处理装饰器"""
    return handle_errors(
        category=ErrorCategory.AUDIO,
        context=context,
        default_return=default_return,
        user_message="音频处理出现问题，请检查麦克风设置"
    )

def handle_ui_errors(context: str = "", default_return: Any = None):
    """UI错误处理装饰器"""
    return handle_errors(
        category=ErrorCategory.UI,
        context=context,
        default_return=default_return,
        level=ErrorLevel.WARNING
    )

def handle_hotkey_errors(context: str = "", default_return: Any = None):
    """热键错误处理装饰器"""
    return handle_errors(
        category=ErrorCategory.HOTKEY,
        context=context,
        default_return=default_return,
        user_message="热键功能异常，请检查权限设置"
    )

def handle_model_errors(context: str = "", default_return: Any = None):
    """模型错误处理装饰器"""
    return handle_errors(
        category=ErrorCategory.MODEL,
        context=context,
        default_return=default_return,
        user_message="语音识别模型出现问题"
    )

# 使用示例
class AudioManager:
    """音频管理器示例"""
    
    @handle_audio_errors(context="开始录音", default_return=False)
    def start_recording(self) -> bool:
        """开始录音"""
        # 可能出错的录音逻辑
        # raise Exception("麦克风权限不足")
        return True
    
    @handle_audio_errors(context="停止录音")
    def stop_recording(self):
        """停止录音"""
        # 可能出错的停止录音逻辑
        pass
    
    def process_audio_safe(self, audio_data):
        """安全处理音频数据"""
        return SafeExecutor.execute(
            self._process_audio_internal,
            audio_data,
            category=ErrorCategory.AUDIO,
            context="处理音频数据",
            default_return=None
        )
    
    def _process_audio_internal(self, audio_data):
        """内部音频处理逻辑"""
        # 实际的音频处理代码
        pass

class UIComponent:
    """UI组件示例"""
    
    @handle_ui_errors(context="更新界面")
    def update_display(self, text: str):
        """更新显示"""
        # 可能出错的UI更新逻辑
        pass
    
    def handle_click_safe(self, event):
        """安全处理点击事件"""
        with error_context(ErrorCategory.UI, "处理点击事件"):
            # 可能出错的点击处理逻辑
            pass

# 错误回调示例
def show_user_error_message(error_info: dict, user_message: Optional[str]):
    """显示用户错误消息"""
    if user_message and error_info['category'] in ['AUDIO', 'HOTKEY']:
        # 显示用户友好的错误消息
        print(f"用户提示: {user_message}")

def log_critical_errors(error_info: dict, user_message: Optional[str]):
    """记录关键错误"""
    if error_info['count'] > 5:  # 同类错误超过5次
        print(f"关键错误: {error_info['error_type']} 已发生 {error_info['count']} 次")

# 注册错误回调
error_handler.register_error_callback(ErrorCategory.AUDIO, show_user_error_message)
error_handler.register_error_callback(ErrorCategory.HOTKEY, show_user_error_message)
error_handler.register_error_callback(ErrorCategory.SYSTEM, log_critical_errors)

# 配置管理示例
class ConfigManager:
    """统一配置管理器"""

    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self._config = {}
        self._load_config()

    def _load_config(self):
        """加载配置"""
        try:
            import json
            import os
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
        except Exception as e:
            error_handler.handle_error(
                error=e,
                category=ErrorCategory.SYSTEM,
                context="加载配置文件"
            )

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self._save_config()

    def _save_config(self):
        """保存配置"""
        try:
            import json
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            error_handler.handle_error(
                error=e,
                category=ErrorCategory.SYSTEM,
                context="保存配置文件"
            )
