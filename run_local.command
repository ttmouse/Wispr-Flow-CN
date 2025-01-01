#!/bin/bash

# 激活 conda 环境
source ~/miniconda3/bin/activate funasr_env

# 切换到项目目录
cd "$(dirname "$0")"

# 运行程序
python src/main.py 