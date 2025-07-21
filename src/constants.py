#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用程序常量配置
统一管理所有硬编码值，提高代码可维护性
"""

import os
from pathlib import Path

class AudioConstants:
    """音频相关常量"""
    
    # 音频参数
    VOLUME_THRESHOLD = 0.001  # 音量阈值
    SOUND_VOLUME = 0.3        # 提示音音量
    SAMPLE_RATE = 16000       # 采样率
    CHUNK_SIZE = 512          # 音频块大小
    
    # 录音控制参数
    MIN_VALID_FRAMES = 2      # 最少有效帧数
    MAX_SILENCE_FRAMES = 50   # 最大静音帧数
    MIN_RECORDING_DURATION = 0.5  # 最短录音时长(秒)
    MAX_RECORDING_DURATION = 30   # 最长录音时长(秒)
    
    # 音频处理参数
    PREEMPHASIS_COEFF = 0.97  # 预加重系数
    FRAME_LENGTH = 0.025      # 帧长(秒)
    FRAME_SHIFT = 0.01        # 帧移(秒)

class UIConstants:
    """UI相关常量"""
    
    # 窗口尺寸
    WINDOW_WIDTH = 400
    WINDOW_HEIGHT = 300
    MIN_WINDOW_WIDTH = 300
    MIN_WINDOW_HEIGHT = 200
    
    # 托盘图标
    TRAY_ICON_SIZE = 16
    TRAY_ICON_RECORDING_SIZE = 20
    
    # 更新间隔
    STATUS_UPDATE_INTERVAL = 2000  # 状态更新间隔(毫秒)
    UI_REFRESH_INTERVAL = 100      # UI刷新间隔(毫秒)
    
    # 历史记录
    MAX_HISTORY_ITEMS = 100        # 最大历史记录数
    HISTORY_ITEM_HEIGHT = 60       # 历史记录项高度
    
    # 样式
    BORDER_RADIUS = 8
    PADDING = 10
    MARGIN = 5

class PathConstants:
    """路径相关常量"""
    
    # 获取项目根目录
    PROJECT_ROOT = Path(__file__).parent.parent
    
    # 资源文件路径
    RESOURCES_DIR = PROJECT_ROOT / "resources"
    HOTWORDS_FILE = RESOURCES_DIR / "hotwords.txt"
    SOUNDS_DIR = RESOURCES_DIR
    START_SOUND = SOUNDS_DIR / "start.wav"
    STOP_SOUND = SOUNDS_DIR / "stop.wav"
    
    # 模型相关路径
    MODELS_DIR = PROJECT_ROOT / "modelscope" / "hub"
    CACHE_DIR = PROJECT_ROOT / "cache"
    
    # 配置和日志路径
    SETTINGS_FILE = PROJECT_ROOT / "settings.json"
    SETTINGS_BACKUP_DIR = PROJECT_ROOT / "settings_history"
    LOGS_DIR = PROJECT_ROOT / "logs"
    HISTORY_FILE = PROJECT_ROOT / "history.json"
    
    # 图标路径
    ICON_FILE = RESOURCES_DIR / "icon.icns"
    MIC_ICON = RESOURCES_DIR / "mic.svg"
    MIC_RECORDING_ICON = RESOURCES_DIR / "mic-recording.svg"
    
    @classmethod
    def ensure_directories(cls):
        """确保必要的目录存在"""
        directories = [
            cls.RESOURCES_DIR,
            cls.MODELS_DIR,
            cls.CACHE_DIR,
            cls.SETTINGS_BACKUP_DIR,
            cls.LOGS_DIR
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

class TimingConstants:
    """时间相关常量"""
    
    # 延迟和超时
    DELAY_CHECK_MS = 100          # 延迟检查间隔(毫秒)
    CLEANUP_TIMEOUT_MS = 200      # 清理超时(毫秒)
    HOTKEY_DELAY_MS = 200         # 热键延迟(毫秒)
    INIT_TIMEOUT_SECONDS = 30     # 初始化超时(秒)
    
    # 自动停止
    AUTO_STOP_SECONDS = 25        # 自动停止录音时间(秒)
    SILENCE_TIMEOUT_SECONDS = 3   # 静音超时(秒)
    
    # 重试机制
    MAX_RETRY_ATTEMPTS = 3        # 最大重试次数
    RETRY_DELAY_SECONDS = 1       # 重试延迟(秒)
    
    # 状态检查
    STATUS_CHECK_INTERVAL = 0.1   # 状态检查间隔(秒)
    PERMISSION_CHECK_INTERVAL = 5 # 权限检查间隔(秒)

class ModelConstants:
    """模型相关常量"""
    
    # FunASR模型配置
    MODEL_NAME = "paraformer-zh"
    MODEL_REVISION = "v2.0.4"
    DEVICE = "cpu"  # 或 "cuda" 如果有GPU
    
    # 模型参数
    USE_QUANTIZATION = True       # 使用量化减少内存
    DISABLE_UPDATE = True         # 禁用模型更新检查
    BATCH_SIZE = 1               # 批处理大小
    
    # 热词配置
    MAX_HOTWORDS = 1000          # 最大热词数量
    HOTWORD_WEIGHT = 10          # 热词权重
    
    # 缓存配置
    ENABLE_MODEL_CACHE = True     # 启用模型缓存
    CACHE_SIZE_LIMIT_MB = 500     # 缓存大小限制(MB)

class HotkeyConstants:
    """热键相关常量"""
    
    # 默认热键
    DEFAULT_HOTKEY = "ctrl"       # 默认热键
    ALTERNATIVE_HOTKEYS = ["fn", "alt", "cmd"]  # 备选热键
    
    # 热键检测参数
    KEY_PRESS_THRESHOLD = 0.1     # 按键检测阈值(秒)
    KEY_RELEASE_THRESHOLD = 0.05  # 释放检测阈值(秒)
    DOUBLE_PRESS_INTERVAL = 0.3   # 双击间隔(秒)
    
    # 状态管理
    MAX_PRESS_DURATION = 10       # 最大按压时长(秒)
    STATUS_RESET_DELAY = 2        # 状态重置延迟(秒)

class LoggingConstants:
    """日志相关常量"""
    
    # 日志级别
    DEFAULT_LOG_LEVEL = "INFO"
    DEBUG_LOG_LEVEL = "DEBUG"
    
    # 日志格式
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    # 日志文件
    LOG_FILE_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_FILE_BACKUP_COUNT = 5              # 保留5个备份
    
    # 日志类别
    MAIN_LOGGER = "ASR.Main"
    AUDIO_LOGGER = "ASR.Audio"
    MODEL_LOGGER = "ASR.Model"
    UI_LOGGER = "ASR.UI"
    HOTKEY_LOGGER = "ASR.Hotkey"

class PerformanceConstants:
    """性能相关常量"""
    
    # 内存管理
    MAX_MEMORY_USAGE_MB = 512     # 最大内存使用(MB)
    MEMORY_CHECK_INTERVAL = 60    # 内存检查间隔(秒)
    
    # 线程管理
    MAX_WORKER_THREADS = 4        # 最大工作线程数
    THREAD_POOL_SIZE = 2          # 线程池大小
    
    # 缓存管理
    MAX_AUDIO_CACHE_SIZE = 100    # 最大音频缓存数量
    CACHE_CLEANUP_INTERVAL = 300  # 缓存清理间隔(秒)
    
    # 性能监控
    ENABLE_PERFORMANCE_MONITORING = False  # 启用性能监控
    PERFORMANCE_LOG_INTERVAL = 30          # 性能日志间隔(秒)

class SecurityConstants:
    """安全相关常量"""
    
    # 权限检查
    REQUIRED_PERMISSIONS = [
        "microphone",      # 麦克风权限
        "accessibility",   # 辅助功能权限
    ]
    
    # 数据保护
    ENCRYPT_SETTINGS = False      # 是否加密设置文件
    ENCRYPT_HISTORY = False       # 是否加密历史记录
    
    # 隐私设置
    AUTO_CLEAR_HISTORY_DAYS = 30  # 自动清理历史记录天数
    ENABLE_ANALYTICS = False      # 启用分析统计

class DevelopmentConstants:
    """开发相关常量"""
    
    # 调试模式
    DEBUG_MODE = False            # 调试模式
    VERBOSE_LOGGING = False       # 详细日志
    
    # 开发工具
    ENABLE_DEV_TOOLS = False      # 启用开发工具
    SHOW_PERFORMANCE_STATS = False # 显示性能统计
    
    # 测试配置
    TEST_MODE = False             # 测试模式
    MOCK_AUDIO_INPUT = False      # 模拟音频输入
    
    @classmethod
    def is_development(cls):
        """检查是否为开发环境"""
        return os.getenv('ASR_DEV_MODE', '').lower() in ('1', 'true', 'yes')

# 导出所有常量类
__all__ = [
    'AudioConstants',
    'UIConstants', 
    'PathConstants',
    'TimingConstants',
    'ModelConstants',
    'HotkeyConstants',
    'LoggingConstants',
    'PerformanceConstants',
    'SecurityConstants',
    'DevelopmentConstants'
]

# 初始化时确保目录存在
PathConstants.ensure_directories()