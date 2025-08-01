#!/bin/bash

# FunASR 语音转文字应用启动脚本
# 确保在正确的 conda 环境中运行并设置正确的图标

# 设置脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$SCRIPT_DIR"

# 检查 conda 是否可用
if ! command -v conda &> /dev/null; then
    echo "❌ 错误: 未找到 conda 命令"
    echo "请确保已安装 Anaconda 或 Miniconda"
    exit 1
fi

# 检查 funasr_env 环境是否存在
if ! conda env list | grep -q "funasr_env"; then
    echo "❌ 错误: 未找到 funasr_env conda 环境"
    echo "请先创建并配置 funasr_env 环境"
    exit 1
fi

# 激活 conda 环境并运行应用程序
echo "🚀 启动 FunASR 语音转文字应用..."
echo "📁 应用目录: $APP_DIR"

# 切换到应用目录
cd "$APP_DIR"

# 激活环境并运行
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate funasr_env

# 检查激活是否成功
if [[ "$CONDA_DEFAULT_ENV" != "funasr_env" ]]; then
    echo "❌ 错误: 无法激活 funasr_env 环境"
    exit 1
fi

echo "✅ 已激活 conda 环境: $CONDA_DEFAULT_ENV"
echo "🎯 启动应用程序..."

# 运行应用程序
python src/main.py

echo "👋 应用程序已退出"
