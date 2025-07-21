
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误处理工具模块
统一管理异常处理逻辑
"""

import functools
import logging
import traceback
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)

def handle_exceptions(default_return: Any = None, 
                     log_error: bool = True,
                     reraise: bool = False):
    """
    统一异常处理装饰器
    
    Args:
        default_return: 异常时的默认返回值
        log_error: 是否记录错误日志
        reraise: 是否重新抛出异常
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.error(
                        f"函数 {func.__name__} 执行失败: {str(e)}\n"
                        f"参数: args={args}, kwargs={kwargs}\n"
                        f"堆栈: {traceback.format_exc()}"
                    )
                
                if reraise:
                    raise
                    
                return default_return
        return wrapper
    return decorator

def safe_execute(func: Callable, 
                *args, 
                default_return: Any = None,
                log_error: bool = True,
                **kwargs) -> Any:
    """
    安全执行函数
    
    Args:
        func: 要执行的函数
        *args: 函数参数
        default_return: 异常时的默认返回值
        log_error: 是否记录错误日志
        **kwargs: 函数关键字参数
        
    Returns:
        函数执行结果或默认返回值
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_error:
            logger.error(
                f"安全执行函数 {func.__name__} 失败: {str(e)}\n"
                f"参数: args={args}, kwargs={kwargs}\n"
                f"堆栈: {traceback.format_exc()}"
            )
        return default_return

class ErrorContext:
    """
    错误上下文管理器
    """
    
    def __init__(self, 
                 operation_name: str,
                 default_return: Any = None,
                 log_error: bool = True,
                 reraise: bool = False):
        self.operation_name = operation_name
        self.default_return = default_return
        self.log_error = log_error
        self.reraise = reraise
        self.result = None
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            if self.log_error:
                logger.error(
                    f"操作 '{self.operation_name}' 失败: {str(exc_val)}\n"
                    f"异常类型: {exc_type.__name__}\n"
                    f"堆栈: {traceback.format_exc()}"
                )
            
            if not self.reraise:
                self.result = self.default_return
                return True  # 抑制异常
                
        return False  # 不抑制异常
