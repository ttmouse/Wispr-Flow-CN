#!/bin/bash

# 切换到项目根目录
cd "$(dirname "$0")/.."

# 更新版本号
python tools/version_manager.py

# 安装依赖
pip install pillow

# 跳过图标处理（图标已存在）
echo "跳过图标处理，使用现有图标文件"

# 创建应用
bash run_local.command

echo "✓ 应用已创建在项目根目录：Dou-flow.app"