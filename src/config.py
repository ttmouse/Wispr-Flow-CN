"""配置文件"""
import os
import sys
from datetime import datetime

# 基础版本号
BASE_VERSION = "1.1.11"

# 检测运行模式
def get_app_version():
    """根据运行模式返回不同的版本号"""
    if getattr(sys, 'frozen', False):
        # 打包模式：使用基础版本号
        return BASE_VERSION
    else:
        # 开发模式：添加dev标识和时间戳
        timestamp = datetime.now().strftime('%Y%m%d.%H%M')
        return f"{BASE_VERSION}-dev.{timestamp}"

# 导出版本号
APP_VERSION = get_app_version()