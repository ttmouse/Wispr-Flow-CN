#!/bin/bash

# Dou-flow 安装脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_PATH="$SCRIPT_DIR/Dou-flow.app"
APPLICATIONS_DIR="/Applications"

echo "=== Dou-flow 安装程序 ==="
echo ""

# 检查应用是否存在
if [[ ! -d "$APP_PATH" ]]; then
    print_error "找不到 Dou-flow.app，请确保安装包完整"
    exit 1
fi

# 检查是否有管理员权限
if [[ ! -w "$APPLICATIONS_DIR" ]]; then
    print_warning "需要管理员权限来安装到应用程序文件夹"
    echo "请输入密码："
fi

# 复制应用到应用程序文件夹
print_warning "正在安装 Dou-flow 到应用程序文件夹..."

if cp -R "$APP_PATH" "$APPLICATIONS_DIR/"; then
    print_success "安装完成！"
    echo ""
    echo "您现在可以："
    echo "1. 在启动台中找到 Dou-flow"
    echo "2. 或在应用程序文件夹中找到 Dou-flow"
    echo ""
    print_warning "首次运行可能需要几分钟来设置环境"

    # 询问是否立即启动
    read -p "是否现在启动 Dou-flow？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open "$APPLICATIONS_DIR/Dou-flow.app"
    fi
else
    print_error "安装失败，请检查权限"
    exit 1
fi
