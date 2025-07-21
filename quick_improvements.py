#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速代码质量改进脚本
自动应用一些高优先级的代码质量改进
"""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path

class QuickImprovements:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.src_dir = self.project_root / "src"
        self.backup_dir = self.project_root / "backups" / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def create_backup(self):
        """创建代码备份"""
        print("📦 创建代码备份...")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 备份src目录
        if self.src_dir.exists():
            shutil.copytree(self.src_dir, self.backup_dir / "src")
            print(f"✓ 代码已备份到: {self.backup_dir}")
        else:
            print("❌ src目录不存在")
            return False
        return True
    
    def create_config_constants(self):
        """创建配置常量文件"""
        print("🔧 创建配置常量文件...")
        
        config_content = '''
# -*- coding: utf-8 -*-
"""
应用程序配置常量
集中管理所有硬编码值，提高可维护性
"""

class AudioConfig:
    """音频相关配置"""
    # 音频检测参数
    VOLUME_THRESHOLD = 0.001  # 音量阈值
    MIN_VALID_FRAMES = 2      # 最少有效帧数
    MAX_SILENCE_FRAMES = 50   # 最大静音帧数
    
    # 音频格式参数
    SAMPLE_RATE = 16000       # 采样率
    CHANNELS = 1              # 声道数
    CHUNK_SIZE = 1024         # 音频块大小
    
    # 音效参数
    SOUND_VOLUME = 0.3        # 音效音量
    
    # 调试参数
    DEBUG_FRAME_INTERVAL = 20 # 调试信息输出间隔（帧数）

class TimingConfig:
    """时间相关配置"""
    # 延迟和超时
    DELAY_CHECK_MS = 100           # 延迟检查时间（毫秒）
    CLEANUP_TIMEOUT_MS = 200       # 清理超时时间（毫秒）
    AUTO_STOP_SECONDS = 25         # 自动停止录音时间（秒）
    
    # UI更新间隔
    STATUS_UPDATE_INTERVAL_MS = 2000  # 状态更新间隔（毫秒）
    HOTKEY_STATUS_UPDATE_MS = 2000    # 热键状态更新间隔（毫秒）
    
    # 线程相关
    THREAD_JOIN_TIMEOUT = 1.0      # 线程等待超时（秒）
    FN_KEY_MONITOR_INTERVAL = 0.05 # Fn键监控间隔（秒）

class PathConfig:
    """路径相关配置"""
    # 资源文件路径
    HOTWORDS_FILE = "resources/hotwords.txt"
    SOUNDS_DIR = "resources"
    START_SOUND = "resources/start.wav"
    STOP_SOUND = "resources/stop.wav"
    
    # 模型路径
    MODELS_DIR = "modelscope/hub"
    ASR_MODEL_DIR = "modelscope/hub/damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch"
    PUNC_MODEL_DIR = "modelscope/hub/damo/punc_ct-transformer_zh-cn-common-vocab272727-pytorch"
    
    # 配置文件路径
    SETTINGS_FILE = "settings.json"
    HISTORY_FILE = "history.json"
    LOGS_DIR = "logs"

class UIConfig:
    """UI相关配置"""
    # 窗口尺寸
    DEFAULT_WINDOW_WIDTH = 800
    DEFAULT_WINDOW_HEIGHT = 600
    MIN_WINDOW_WIDTH = 400
    MIN_WINDOW_HEIGHT = 300
    
    # 历史记录
    MAX_HISTORY_ITEMS = 30
    HISTORY_ITEM_HEIGHT = 60
    
    # 样式
    DEFAULT_THEME = "default"
    FONT_SIZE = 12
    
    # 动画
    FADE_DURATION_MS = 200
    SLIDE_DURATION_MS = 300

class PerformanceConfig:
    """性能相关配置"""
    # 线程池
    MAX_WORKER_THREADS = 4
    MAX_DELAYED_THREADS = 5
    
    # 缓存
    MAX_BUFFER_POOL_SIZE = 10
    CACHE_EXPIRE_HOURS = 24
    
    # 内存管理
    MEMORY_WARNING_THRESHOLD_MB = 100
    GC_INTERVAL_SECONDS = 60
    
    # 重试机制
    MAX_RETRIES = 3
    RETRY_DELAYS = [1, 2, 5]  # 秒

class LogConfig:
    """日志相关配置"""
    # 日志级别
    DEFAULT_LEVEL = "INFO"
    DEBUG_LEVEL = "DEBUG"
    
    # 日志格式
    FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    # 日志文件
    LOG_FILE = "logs/app.log"
    MAX_LOG_SIZE_MB = 10
    BACKUP_COUNT = 5

class HotkeyConfig:
    """热键相关配置"""
    # 默认热键
    DEFAULT_HOTKEY = "ctrl"
    
    # 检测参数
    STABLE_COUNT_THRESHOLD = 3
    KEY_REPEAT_THRESHOLD_MS = 50
    
    # 状态
    STATUS_COLORS = {
        "normal": "#4CAF50",      # 绿色
        "recording": "#FF9800",   # 橙色
        "error": "#F44336",       # 红色
        "inactive": "#9E9E9E"     # 灰色
    }
'''
        
        config_file = self.src_dir / "config_constants.py"
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print(f"✓ 配置常量文件已创建: {config_file}")
        return config_file
    
    def create_logger_utility(self):
        """创建统一的日志工具"""
        print("📝 创建统一日志工具...")
        
        logger_content = '''
# -*- coding: utf-8 -*-
"""
统一日志工具
替换项目中的print语句，提供结构化日志
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from .config_constants import LogConfig

class AppLogger:
    """应用程序日志器"""
    
    _loggers = {}  # 缓存已创建的日志器
    
    @classmethod
    def get_logger(cls, name):
        """获取日志器实例"""
        if name not in cls._loggers:
            cls._loggers[name] = cls._create_logger(name)
        return cls._loggers[name]
    
    @classmethod
    def _create_logger(cls, name):
        """创建日志器"""
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, LogConfig.DEFAULT_LEVEL))
        
        # 避免重复添加处理器
        if logger.handlers:
            return logger
        
        # 创建格式化器
        formatter = logging.Formatter(
            LogConfig.FORMAT,
            datefmt=LogConfig.DATE_FORMAT
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)
        
        # 文件处理器
        log_dir = Path(LogConfig.LOG_FILE).parent
        log_dir.mkdir(exist_ok=True)
        
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            LogConfig.LOG_FILE,
            maxBytes=LogConfig.MAX_LOG_SIZE_MB * 1024 * 1024,
            backupCount=LogConfig.BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        
        return logger
    
    @classmethod
    def setup_global_logging(cls):
        """设置全局日志配置"""
        # 设置根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # 禁用第三方库的详细日志
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('PyQt6').setLevel(logging.WARNING)

# 便捷函数
def get_logger(name=None):
    """获取日志器的便捷函数"""
    if name is None:
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'unknown')
    return AppLogger.get_logger(name)

# 装饰器：自动记录函数调用
def log_function_call(level=logging.INFO):
    """记录函数调用的装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            logger.log(level, f"调用函数: {func.__name__}")
            try:
                result = func(*args, **kwargs)
                logger.log(level, f"函数 {func.__name__} 执行成功")
                return result
            except Exception as e:
                logger.error(f"函数 {func.__name__} 执行失败: {e}")
                raise
        return wrapper
    return decorator

# 上下文管理器：临时改变日志级别
class LogLevel:
    """临时改变日志级别的上下文管理器"""
    
    def __init__(self, logger, level):
        self.logger = logger
        self.new_level = level
        self.old_level = None
    
    def __enter__(self):
        self.old_level = self.logger.level
        self.logger.setLevel(self.new_level)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.setLevel(self.old_level)
'''
        
        logger_file = self.src_dir / "logger_utils.py"
        with open(logger_file, 'w', encoding='utf-8') as f:
            f.write(logger_content)
        
        print(f"✓ 日志工具文件已创建: {logger_file}")
        return logger_file
    
    def create_exception_handler(self):
        """创建改进的异常处理工具"""
        print("🛡️ 创建异常处理工具...")
        
        exception_content = '''
# -*- coding: utf-8 -*-
"""
改进的异常处理工具
提供更精确的异常处理和恢复机制
"""

import functools
import time
from typing import Callable, Any, Optional, Type, Tuple
from .logger_utils import get_logger
from .config_constants import PerformanceConfig

logger = get_logger(__name__)

class RecoveryManager:
    """自动恢复管理器"""
    
    def __init__(self, max_retries=None, retry_delays=None):
        self.max_retries = max_retries or PerformanceConfig.MAX_RETRIES
        self.retry_delays = retry_delays or PerformanceConfig.RETRY_DELAYS
    
    def with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """带重试机制的函数执行"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt == self.max_retries - 1:
                    logger.error(f"函数 {func.__name__} 重试 {self.max_retries} 次后仍然失败")
                    raise e
                
                delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                logger.warning(f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败: {e}，{delay}秒后重试")
                time.sleep(delay)
        
        raise last_exception

def retry_on_exception(*exception_types, max_retries=None, delays=None):
    """重试装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            recovery = RecoveryManager(max_retries, delays)
            return recovery.with_retry(func, *args, **kwargs)
        return wrapper
    return decorator

def safe_execute(func: Callable, default_value=None, log_errors=True) -> Any:
    """安全执行函数，出错时返回默认值"""
    try:
        return func()
    except Exception as e:
        if log_errors:
            logger.error(f"安全执行失败: {func.__name__ if hasattr(func, '__name__') else str(func)}: {e}")
        return default_value

class ExceptionContext:
    """异常上下文管理器"""
    
    def __init__(self, operation_name: str, 
                 ignore_exceptions: Tuple[Type[Exception], ...] = (),
                 default_return=None):
        self.operation_name = operation_name
        self.ignore_exceptions = ignore_exceptions
        self.default_return = default_return
        self.exception_occurred = False
        self.exception = None
    
    def __enter__(self):
        logger.debug(f"开始执行: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.exception_occurred = True
            self.exception = exc_val
            
            if exc_type in self.ignore_exceptions:
                logger.debug(f"{self.operation_name} 发生预期异常: {exc_val}")
                return True  # 抑制异常
            else:
                logger.error(f"{self.operation_name} 发生异常: {exc_val}")
                return False  # 不抑制异常
        else:
            logger.debug(f"{self.operation_name} 执行成功")
        
        return False

# 常用异常处理装饰器
def handle_exceptions(default_return=None, log_level="error"):
    """通用异常处理装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger_func = getattr(logger, log_level, logger.error)
                logger_func(f"函数 {func.__name__} 执行失败: {e}")
                return default_return
        return wrapper
    return decorator

def handle_specific_exceptions(**exception_handlers):
    """处理特定异常类型的装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                for exc_type, handler in exception_handlers.items():
                    if isinstance(e, exc_type):
                        logger.warning(f"处理特定异常 {exc_type.__name__}: {e}")
                        return handler(e) if callable(handler) else handler
                
                # 未处理的异常继续抛出
                logger.error(f"未处理的异常: {type(e).__name__}: {e}")
                raise
        return wrapper
    return decorator
'''
        
        exception_file = self.src_dir / "exception_utils.py"
        with open(exception_file, 'w', encoding='utf-8') as f:
            f.write(exception_content)
        
        print(f"✓ 异常处理工具文件已创建: {exception_file}")
        return exception_file
    
    def generate_improvement_report(self):
        """生成改进报告"""
        print("\n📊 生成改进报告...")
        
        report_content = f"""
# 快速改进实施报告

## 实施时间
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 已创建的文件

### 1. 配置常量文件
- **文件**: `src/config_constants.py`
- **作用**: 集中管理所有硬编码值
- **使用方法**: 
  ```python
  from .config_constants import AudioConfig, TimingConfig
  
  # 替换硬编码值
  volume_threshold = AudioConfig.VOLUME_THRESHOLD
  update_interval = TimingConfig.STATUS_UPDATE_INTERVAL_MS
  ```

### 2. 统一日志工具
- **文件**: `src/logger_utils.py`
- **作用**: 替换所有print语句，提供结构化日志
- **使用方法**:
  ```python
  from .logger_utils import get_logger
  
  logger = get_logger(__name__)
  
  # 替换 print("信息") 为:
  logger.info("信息")
  
  # 替换 print(f"错误: {{e}}") 为:
  logger.error(f"错误: {{e}}")
  ```

### 3. 异常处理工具
- **文件**: `src/exception_utils.py`
- **作用**: 提供更精确的异常处理和自动重试
- **使用方法**:
  ```python
  from .exception_utils import retry_on_exception, handle_exceptions
  
  @retry_on_exception(ConnectionError, max_retries=3)
  def connect_to_service():
      # 网络连接代码
      pass
  
  @handle_exceptions(default_return=False)
  def risky_operation():
      # 可能出错的操作
      pass
  ```

## 下一步建议

### 立即实施（高优先级）
1. **替换硬编码值**
   - 在 `audio_capture.py` 中使用 `AudioConfig` 常量
   - 在 `hotkey_manager.py` 中使用 `TimingConfig` 常量
   - 在 `main.py` 中使用相应配置常量

2. **统一日志系统**
   - 在每个文件开头添加: `from .logger_utils import get_logger`
   - 创建模块级日志器: `logger = get_logger(__name__)`
   - 替换所有 `print()` 语句为相应的日志调用

3. **改进异常处理**
   - 在关键函数上添加异常处理装饰器
   - 使用具体的异常类型而不是通用的 `Exception`
   - 为网络操作和文件操作添加重试机制

### 示例改进

#### 改进前 (audio_capture.py)
```python
self.volume_threshold = 0.001
print(f"音量检测 - 当前: {{volume:.5f}}")
try:
    # 某些操作
except Exception as e:
    print(f"操作失败: {{e}}")
```

#### 改进后
```python
from .config_constants import AudioConfig
from .logger_utils import get_logger
from .exception_utils import handle_exceptions

logger = get_logger(__name__)

self.volume_threshold = AudioConfig.VOLUME_THRESHOLD
logger.debug(f"音量检测 - 当前: {{volume:.5f}}")

@handle_exceptions(default_return=None)
def audio_operation(self):
    # 某些操作
    pass
```

## 预期收益

- ✅ **代码可维护性提升**: 配置集中管理
- ✅ **调试效率提升**: 结构化日志
- ✅ **稳定性提升**: 更好的异常处理
- ✅ **开发效率提升**: 统一的工具和模式

## 备份信息

原始代码已备份到: `{self.backup_dir}`

如需回滚，请执行:
```bash
cp -r {self.backup_dir}/src/* src/
```
"""
        
        report_file = self.project_root / "QUICK_IMPROVEMENTS_REPORT.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"✓ 改进报告已生成: {report_file}")
        return report_file
    
    def run_all_improvements(self):
        """运行所有快速改进"""
        print("🚀 开始快速代码质量改进")
        print("=" * 50)
        
        try:
            # 1. 创建备份
            if not self.create_backup():
                return False
            
            # 2. 创建配置文件
            self.create_config_constants()
            
            # 3. 创建日志工具
            self.create_logger_utility()
            
            # 4. 创建异常处理工具
            self.create_exception_handler()
            
            # 5. 生成报告
            self.generate_improvement_report()
            
            print("\n" + "=" * 50)
            print("🎉 快速改进完成！")
            print("\n📋 下一步:")
            print("1. 查看 QUICK_IMPROVEMENTS_REPORT.md 了解详细使用方法")
            print("2. 逐步替换代码中的硬编码值和print语句")
            print("3. 在关键函数上添加异常处理装饰器")
            print("4. 测试改进后的代码功能")
            
            return True
            
        except Exception as e:
            print(f"❌ 改进过程中出错: {e}")
            return False

def main():
    """主函数"""
    print("🔧 代码质量快速改进工具")
    print("=" * 40)
    
    improver = QuickImprovements()
    
    choice = input("\n是否开始快速改进？(y/N): ").strip().lower()
    if choice in ['y', 'yes', '是']:
        success = improver.run_all_improvements()
        if success:
            print("\n✨ 改进成功！请查看生成的文件和报告。")
        else:
            print("\n❌ 改进失败，请检查错误信息。")
    else:
        print("\n👋 改进已取消。")

if __name__ == "__main__":
    main()