#!/bin/bash

# 开发环境启动脚本
# 确保使用正确的conda环境运行应用

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查conda环境
if ! conda env list | grep -q "funasr_env"; then
    print_error "funasr_env环境不存在"
    echo "请运行以下命令创建环境："
    echo "  conda create -n funasr_env python=3.10 -y"
    echo "  conda activate funasr_env"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# 检查是否有venv环境干扰
if [[ "$VIRTUAL_ENV" ]]; then
    print_warning "检测到激活的venv环境，正在退出..."
    deactivate 2>/dev/null || true
fi

# 激活环境并运行
print_info "使用conda funasr_env环境启动应用..."
print_warning "如果这是第一次运行，可能需要几分钟加载模型"

# 确保使用正确的conda环境
eval "$(conda shell.bash hook)"
conda activate funasr_env

# 验证环境
PYTHON_PATH=$(which python)
if [[ "$PYTHON_PATH" == *"funasr_env"* ]]; then
    print_info "✅ 环境验证通过: $PYTHON_PATH"
else
    print_error "❌ 环境验证失败: $PYTHON_PATH"
    print_error "请手动运行: conda activate funasr_env"
    exit 1
fi

# 运行应用
python src/main.py
