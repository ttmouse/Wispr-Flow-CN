
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本处理工具模块
统一管理所有文本处理相关的函数
"""

import re
import html

def clean_html_tags(text: str) -> str:
    """
    清理HTML标签和解码HTML实体
    
    Args:
        text: 包含HTML标签的文本
        
    Returns:
        清理后的纯文本
    """
    if not text:
        return ""
    
    # 移除HTML标签
    clean_text = re.sub(r'<[^>]+>', '', text)
    
    # 解码HTML实体
    clean_text = html.unescape(clean_text)
    
    # 清理多余的空白字符
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    return clean_text

def normalize_text(text: str) -> str:
    """
    标准化文本格式
    
    Args:
        text: 原始文本
        
    Returns:
        标准化后的文本
    """
    if not text:
        return ""
    
    # 统一换行符
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # 移除多余空行
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    # 清理首尾空白
    text = text.strip()
    
    return text

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本到指定长度
    
    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 截断后缀
        
    Returns:
        截断后的文本
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix
