#!/bin/bash

# 测试两种打包方式的脚本

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

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=== Dou-flow 打包测试 ==="
echo ""

# 测试本地开发版打包
print_info "测试本地开发版打包..."
if ./tools/build_app.sh; then
    if [[ -d "Dou-flow.app" ]]; then
        print_success "本地开发版打包成功"
        echo "  📱 应用位置: $(pwd)/Dou-flow.app"
    else
        print_error "本地开发版打包失败：应用文件未生成"
    fi
else
    print_error "本地开发版打包脚本执行失败"
fi

echo ""

# 测试智能分发版打包
print_info "测试智能分发版打包..."
if ./tools/build_for_distribution.sh; then
    if [[ -d "dist_release/Dou-flow.app" ]]; then
        print_success "智能分发版打包成功"
        echo "  📦 分发目录: $(pwd)/dist_release/"
        echo "  📱 应用位置: $(pwd)/dist_release/Dou-flow.app"
        echo "  📖 使用说明: $(pwd)/dist_release/使用说明.md"
        echo "  🔧 安装脚本: $(pwd)/dist_release/安装.command"
    else
        print_error "智能分发版打包失败：应用文件未生成"
    fi
else
    print_error "智能分发版打包脚本执行失败"
fi

echo ""
print_success "=== 打包测试完成 ==="
echo ""
print_info "两种打包方式说明："
echo "  🔧 本地开发版 (build_app.sh): 适合开发者本地使用，依赖本地环境"
echo "  📦 智能分发版 (build_for_distribution.sh): 适合分发给用户，自动安装环境"
echo ""
print_warning "注意：智能分发版首次运行时会自动下载和安装Python环境"