#!/bin/bash

# 获取脚本所在目录
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR/../../../"

# 激活 conda 环境
source ~/miniconda3/bin/activate funasr_env

# 运行程序
python src/main.py
