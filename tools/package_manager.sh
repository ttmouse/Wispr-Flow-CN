#!/bin/bash

# 打包管理脚本
# 统一管理不同类型的打包方案

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_title() {
    echo -e "${CYAN}🎯 $1${NC}"
}

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

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# 显示菜单
show_menu() {
    clear
    print_title "=== Dou-flow 打包管理器 ==="
    echo ""
    echo "选择打包方式："
    echo ""
    echo "1) 🏠 本地开发版 (快速打包，需要conda环境)"
    echo "2) 📦 智能分发版 (自动安装环境，推荐给用户)"
    echo "3) 🔒 独立可执行版 (PyInstaller，无需Python环境)"
    echo "4) 🐳 Docker容器版 (跨平台，服务器部署)"
    echo "5) 📊 环境状态检查"
    echo "6) 🧹 清理构建文件"
    echo "0) 退出"
    echo ""
}

# 本地开发版打包
build_local() {
    print_title "本地开发版打包"
    print_info "使用现有的快速打包脚本..."
    
    if bash tools/build_app.sh; then
        print_success "本地开发版打包完成"
        print_info "输出：Dou-flow.app"
        print_warning "此版本需要用户有conda环境"
    else
        print_error "本地开发版打包失败"
    fi
}

# 智能分发版打包
build_distribution() {
    print_title "智能分发版打包"
    print_info "创建自动安装环境的分发版本..."
    
    if bash tools/build_for_distribution.sh; then
        print_success "智能分发版打包完成"
        print_info "输出：dist_release/"
        print_success "此版本会自动为用户安装Python环境"
    else
        print_error "智能分发版打包失败"
    fi
}

# 独立可执行版打包
build_standalone() {
    print_title "独立可执行版打包"
    print_warning "此过程可能需要15-20分钟..."
    
    if bash tools/build_standalone.sh; then
        print_success "独立可执行版打包完成"
        print_info "输出：dist_standalone/"
        print_success "此版本无需任何Python环境"
    else
        print_error "独立可执行版打包失败"
    fi
}

# Docker容器版打包
build_docker() {
    print_title "Docker容器版打包"
    print_warning "需要Docker Desktop运行..."
    
    if bash tools/build_docker.sh; then
        print_success "Docker容器版打包完成"
        print_info "输出：dist_docker/"
        print_success "此版本可在任何支持Docker的系统运行"
    else
        print_error "Docker容器版打包失败"
    fi
}

# 环境状态检查
check_environment() {
    print_title "环境状态检查"
    
    echo "🔍 检查开发环境..."
    bash tools/env_manager.sh status
    
    echo ""
    echo "🔍 检查打包工具..."
    
    # 检查conda
    if command -v conda >/dev/null 2>&1; then
        print_success "conda: 已安装"
    else
        print_error "conda: 未安装"
    fi
    
    # 检查PyInstaller
    if conda run -n funasr_env pip show pyinstaller >/dev/null 2>&1; then
        print_success "PyInstaller: 已安装"
    else
        print_warning "PyInstaller: 未安装 (独立版需要)"
    fi
    
    # 检查Docker
    if command -v docker >/dev/null 2>&1; then
        if docker info >/dev/null 2>&1; then
            print_success "Docker: 已安装并运行"
        else
            print_warning "Docker: 已安装但未运行"
        fi
    else
        print_warning "Docker: 未安装 (容器版需要)"
    fi
    
    echo ""
    echo "📊 磁盘空间检查..."
    df -h . | tail -1 | awk '{print "可用空间: " $4}'
}

# 清理构建文件
cleanup_builds() {
    print_title "清理构建文件"
    
    echo "🧹 清理中..."
    
    # 清理各种构建目录
    rm -rf build/ dist/ *.spec
    rm -rf dist_release/ dist_standalone/ dist_docker/
    rm -rf Dou-flow.app Dou-flow1.app
    
    # 清理Python缓存
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    
    # 清理日志
    rm -rf logs/*.log
    
    print_success "构建文件清理完成"
}

# 显示打包建议
show_recommendations() {
    echo ""
    print_title "📋 打包建议"
    echo ""
    echo "🎯 根据目标用户选择打包方式："
    echo ""
    echo "👨‍💻 开发者/技术用户："
    echo "   → 选择 1) 本地开发版 (最快)"
    echo ""
    echo "👥 普通用户："
    echo "   → 选择 2) 智能分发版 (推荐)"
    echo "   → 用户无需安装任何环境"
    echo ""
    echo "🔒 企业/离线环境："
    echo "   → 选择 3) 独立可执行版"
    echo "   → 完全自包含，但文件较大"
    echo ""
    echo "🌐 服务器/跨平台："
    echo "   → 选择 4) Docker容器版"
    echo "   → 适合服务器部署"
    echo ""
}

# 主循环
main() {
    while true; do
        show_menu
        show_recommendations
        
        read -p "请选择 (0-6): " choice
        echo ""
        
        case $choice in
            1)
                build_local
                ;;
            2)
                build_distribution
                ;;
            3)
                build_standalone
                ;;
            4)
                build_docker
                ;;
            5)
                check_environment
                ;;
            6)
                cleanup_builds
                ;;
            0)
                print_success "再见！"
                exit 0
                ;;
            *)
                print_error "无效选择，请重试"
                ;;
        esac
        
        echo ""
        read -p "按回车键继续..."
    done
}

main "$@"
