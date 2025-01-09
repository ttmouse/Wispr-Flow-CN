#!/bin/bash

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 设置日志文件
LOG_FILE="$SCRIPT_DIR/asr_server.log"

# 输出日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 清理旧的日志文件
if [ -f "$LOG_FILE" ]; then
    mv "$LOG_FILE" "${LOG_FILE}.old"
fi

# 检查Python环境
PYTHON_VERSION=$(python3 -V 2>&1)
log "检测到Python版本: $PYTHON_VERSION"

if ! command -v python3 &> /dev/null; then
    log "错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查pip3命令
PIP_VERSION=$(pip3 -V 2>&1)
log "检测到pip版本: $PIP_VERSION"

if ! command -v pip3 &> /dev/null; then
    log "错误: 未找到pip3，请先安装pip3"
    exit 1
fi

# 创建虚拟环境
VENV_DIR="$SCRIPT_DIR/venv"
if [ -d "$VENV_DIR" ]; then
    log "检测到已存在的虚拟环境，正在删除..."
    rm -rf "$VENV_DIR"
fi

log "创建Python虚拟环境..."
python3 -m venv "$VENV_DIR" 2> >(tee -a "$LOG_FILE")

# 检查虚拟环境是否创建成功
if [ ! -f "$VENV_DIR/bin/activate" ]; then
    log "错误: 虚拟环境创建可能不完整，activate脚本不存在"
    exit 1
fi

# 激活虚拟环境
log "激活虚拟环境..."
source "$VENV_DIR/bin/activate"
if [ $? -ne 0 ]; then
    log "错误: 激活虚拟环境失败"
    exit 1
fi

# 验证虚拟环境
VENV_PYTHON_VERSION=$(python -V 2>&1)
log "虚拟环境Python版本: $VENV_PYTHON_VERSION"
VENV_PIP_VERSION=$(pip -V 2>&1)
log "虚拟环境pip版本: $VENV_PIP_VERSION"

# 配置pip源
mkdir -p ~/.pip
echo "[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn" > ~/.pip/pip.conf

# 安装依赖
log "安装依赖包..."

# 创建requirements.txt
cat > "$SCRIPT_DIR/requirements.txt" << EOL
--index-url https://pypi.tuna.tsinghua.edu.cn/simple
--trusted-host pypi.tuna.tsinghua.edu.cn
torch==2.1.0
torchaudio==2.1.0
funasr==0.5.1
EOL

# 使用requirements.txt安装依赖
log "使用pip安装依赖..."
pip install -r "$SCRIPT_DIR/requirements.txt"
if [ $? -ne 0 ]; then
    log "错误: 安装依赖失败"
    exit 1
fi

# 验证依赖安装
log "验证依赖安装..."
python -c "import torch; print('PyTorch版本:', torch.__version__)" || {
    log "错误: PyTorch导入失败"
    exit 1
}
python -c "import funasr; print('FunASR版本:', funasr.__version__)" || {
    log "错误: FunASR导入失败"
    exit 1
}

log "依赖安装完成"

# 检查asr_server.py是否存在
if [ ! -f "$SCRIPT_DIR/asr_server.py" ]; then
    log "错误: 未找在asr_server.py"
    exit 1
fi

# 启动ASR服务器
log "启动ASR服务器..."
cd "$SCRIPT_DIR"

# 直接运行服务器并实时输出日志
python asr_server.py 2>&1 | tee -a "$LOG_FILE" &
SERVER_PID=$!

# 等待服务器启动
log "等待服务器启动..."
for i in {1..30}; do
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:6006 > /dev/null 2>&1; then
        log "ASR服务器启动成功 (PID: $SERVER_PID)"
        echo $SERVER_PID > "$SCRIPT_DIR/server.pid"
        exit 0
    fi
    sleep 1
    log "等待服务器响应... ($i/30)"
done

# 如果服务器没有启动，输出错误信息
log "错误: ASR服务器启动失败"
if ps -p $SERVER_PID > /dev/null; then
    log "进程仍在运行，但服务器无响应"
    kill -9 $SERVER_PID
else
    log "服务器进程已终止"
fi

# 输出Python错误信息
log "Python错误信息:"
python -c "import sys; print('Python路径:', sys.path)"
python -c "import torch; print('PyTorch设备:', torch.cuda.is_available() and 'CUDA' or 'CPU')"

exit 1 