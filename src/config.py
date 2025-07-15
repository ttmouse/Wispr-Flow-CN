"""配置文件"""
import os
import sys
from datetime import datetime

# 基础版本号
BASE_VERSION = "1.1.24"

# 检测运行模式
def get_app_version():
    """返回基础版本号"""
    # 统一使用基础版本号，不添加dev标识和时间戳
    return BASE_VERSION

# 导出版本号
APP_VERSION = get_app_version()