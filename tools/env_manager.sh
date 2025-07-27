#!/bin/bash

# 环境管理脚本
# 用于统一管理和切换Python环境

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查conda是否安装
check_conda() {
    if ! command -v conda &> /dev/null; then
        print_error "conda未安装，请先安装Miniconda或Anaconda"
        exit 1
    fi
}

# 显示当前环境状态
show_env_status() {
    print_info "=== 环境状态检查 ==="
    
    echo "当前Python路径: $(which python)"
    echo "当前Python版本: $(python --version)"
    
    if [[ "$CONDA_DEFAULT_ENV" ]]; then
        print_success "当前conda环境: $CONDA_DEFAULT_ENV"
    else
        print_warning "未激活conda环境"
    fi
    
    # 检查funasr_env环境
    if conda env list | grep -q "funasr_env"; then
        print_success "funasr_env环境存在"
    else
        print_warning "funasr_env环境不存在"
    fi
    
    # 检查venv环境
    if [[ -d "venv" ]]; then
        print_warning "检测到venv环境 (不推荐使用)"
    fi
    
    echo ""
}

# 创建或更新funasr_env环境
setup_conda_env() {
    print_info "=== 设置conda环境 ==="
    
    check_conda
    
    # 检查环境是否存在
    if conda env list | grep -q "funasr_env"; then
        print_info "funasr_env环境已存在，正在更新..."
    else
        print_info "创建funasr_env环境..."
        conda create -n funasr_env python=3.10 -y
    fi
    
    # 激活环境并安装依赖
    print_info "激活环境并安装依赖..."
    
    # 使用conda run来在指定环境中执行命令
    conda run -n funasr_env pip install -r requirements.txt
    
    print_success "conda环境设置完成"
    print_info "使用方法: conda activate funasr_env && python src/main.py"
}

# 清理venv环境
cleanup_venv() {
    if [[ -d "venv" ]]; then
        print_warning "检测到venv环境，是否删除? (y/N)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            rm -rf venv
            print_success "venv环境已删除"
        fi
    fi
}

# 环境对比
compare_envs() {
    print_info "=== 环境对比 ==="
    
    echo "📦 conda funasr_env环境:"
    if conda env list | grep -q "funasr_env"; then
        conda run -n funasr_env pip list | grep -E "(torch|funasr|PyQt)" || echo "  未找到关键包"
    else
        echo "  环境不存在"
    fi
    
    echo ""
    echo "📦 venv环境:"
    if [[ -d "venv" ]]; then
        ./venv/bin/pip list | grep -E "(torch|funasr|PyQt)" || echo "  未找到关键包"
    else
        echo "  环境不存在"
    fi
    
    echo ""
}

# 运行应用
run_app() {
    print_info "=== 运行应用 ==="
    
    if ! conda env list | grep -q "funasr_env"; then
        print_error "funasr_env环境不存在，请先运行: $0 setup"
        exit 1
    fi
    
    print_info "使用conda funasr_env环境运行应用..."
    conda run -n funasr_env python src/main.py
}

# 显示帮助
show_help() {
    echo "环境管理脚本 - 用于统一管理Python环境"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  status    - 显示当前环境状态"
    echo "  setup     - 创建/更新conda环境"
    echo "  cleanup   - 清理venv环境"
    echo "  compare   - 对比不同环境的包版本"
    echo "  run       - 使用推荐环境运行应用"
    echo "  help      - 显示此帮助信息"
    echo ""
    echo "推荐工作流程:"
    echo "  1. $0 setup     # 设置conda环境"
    echo "  2. $0 cleanup   # 清理旧的venv环境"
    echo "  3. $0 run       # 运行应用"
}

# 主函数
main() {
    case "${1:-status}" in
        "status")
            show_env_status
            ;;
        "setup")
            setup_conda_env
            ;;
        "cleanup")
            cleanup_venv
            ;;
        "compare")
            compare_envs
            ;;
        "run")
            run_app
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
