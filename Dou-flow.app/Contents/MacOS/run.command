#!/bin/bash

# 获取脚本所在目录
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR/../../../"

# 设置错误处理
set -e

# 显示用户友好的错误信息
show_error() {
    osascript -e "display dialog \"$1\" buttons {\"确定\"} default button \"确定\" with icon stop with title \"Dou-flow 启动错误\""
    exit 1
}

show_info() {
    osascript -e "display dialog \"$1\" buttons {\"确定\"} default button \"确定\" with icon note with title \"Dou-flow\""
}

# 本地打包版本 - 改进的环境检查
check_local_environment() {
    # 获取当前用户的home目录
    USER_HOME="$HOME"

    # 设置常见的Python路径
    COMMON_PATHS=(
        "$USER_HOME/miniconda3/envs/funasr_env/bin"
        "$USER_HOME/miniconda3/bin"
        "$USER_HOME/anaconda3/envs/funasr_env/bin"
        "$USER_HOME/anaconda3/bin"
        "/opt/homebrew/bin"
        "/usr/local/bin"
        "/usr/bin"
    )

    # 添加常见路径到PATH
    for path in "${COMMON_PATHS[@]}"; do
        if [ -d "$path" ]; then
            export PATH="$path:$PATH"
        fi
    done

    # 检查Python是否可用 - 优先使用conda环境中的Python
    PYTHON_CMD=""

    # 首先尝试conda环境中的Python
    if [ -f "$USER_HOME/miniconda3/envs/funasr_env/bin/python" ]; then
        PYTHON_CMD="$USER_HOME/miniconda3/envs/funasr_env/bin/python"
    elif [ -f "$USER_HOME/anaconda3/envs/funasr_env/bin/python" ]; then
        PYTHON_CMD="$USER_HOME/anaconda3/envs/funasr_env/bin/python"
    # 然后尝试系统Python
    elif command -v python3 >/dev/null 2>&1; then
        PYTHON_CMD="python3"
    elif command -v python >/dev/null 2>&1; then
        PYTHON_CMD="python"
    else
        # 最后尝试直接路径
        for path in "${COMMON_PATHS[@]}"; do
            if [ -f "$path/python" ]; then
                PYTHON_CMD="$path/python"
                break
            elif [ -f "$path/python3" ]; then
                PYTHON_CMD="$path/python3"
                break
            fi
        done

        if [ -z "$PYTHON_CMD" ]; then
            show_error "Python环境异常，请确保Python已正确安装"
            return 1
        fi
    fi

    echo "找到Python: $PYTHON_CMD"
    echo "本地打包版本，跳过依赖检查..."
}

# 主要逻辑
main() {
    # 本地打包版本 - 检查本地环境
    check_local_environment

    # 尝试激活conda环境（如果存在）
    if command -v conda >/dev/null 2>&1; then
        # 如果conda可用，尝试激活funasr_env环境
        if conda env list | grep -q "funasr_env"; then
            echo "激活conda环境: funasr_env"
            eval "$(conda shell.bash hook)"
            conda activate funasr_env 2>/dev/null || true
            # 重新检查Python路径，确保使用conda环境中的Python
            if [ -f "$HOME/miniconda3/envs/funasr_env/bin/python" ]; then
                PYTHON_CMD="$HOME/miniconda3/envs/funasr_env/bin/python"
                echo "使用conda环境中的Python: $PYTHON_CMD"
            fi
        fi
    fi

    # 运行程序 - 使用检测到的Python命令
    echo "启动应用程序..."
    $PYTHON_CMD src/main.py 2>&1 | tee app_error.log
}

main "$@"
