#!/bin/bash

# 获取脚本所在目录
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR/../../../"

# 设置错误处理
set -e

# 尝试多种方式激活 conda 环境
if [ -f "$HOME/miniconda3/bin/activate" ]; then
    source "$HOME/miniconda3/bin/activate" funasr_env
elif [ -f "/opt/miniconda3/bin/activate" ]; then
    source "/opt/miniconda3/bin/activate" funasr_env
elif [ -f "$HOME/anaconda3/bin/activate" ]; then
    source "$HOME/anaconda3/bin/activate" funasr_env
elif command -v conda >/dev/null 2>&1; then
    # 如果conda在PATH中，尝试直接激活
    eval "$(conda shell.bash hook)"
    conda activate funasr_env
else
    echo "错误: 无法找到conda环境" >&2
    exit 1
fi

# 检查Python环境
if ! command -v python >/dev/null 2>&1; then
    echo "错误: 无法找到Python" >&2
    exit 1
fi

# 运行程序，并捕获错误
python src/main.py 2>&1 | tee app_error.log
