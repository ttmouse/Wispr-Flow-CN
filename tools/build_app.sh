#!/bin/bash

# 切换到项目根目录
cd "$(dirname "$0")/.."

# 更新版本号
python tools/version_manager.py

# 安装依赖
pip install pillow

# 检查并创建图标（仅在需要时）
python tools/create_icon.py

# 创建应用
bash run_local.command

echo "✓ 应用已创建在项目根目录：Dou-flow.app"