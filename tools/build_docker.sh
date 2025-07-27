#!/bin/bash

# Docker 容器化打包脚本
# 创建可在任何支持Docker的系统上运行的容器

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

print_info "=== Docker 容器化打包 ==="

# 检查Docker是否安装
if ! command -v docker >/dev/null 2>&1; then
    print_error "Docker未安装，请先安装Docker Desktop"
    exit 1
fi

# 检查Docker是否运行
if ! docker info >/dev/null 2>&1; then
    print_error "Docker未运行，请启动Docker Desktop"
    exit 1
fi

# 创建Dockerfile
print_info "创建Dockerfile..."
cat > Dockerfile << 'EOL'
# 使用官方Python镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    python3-pyaudio \
    alsa-utils \
    pulseaudio \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY src/ ./src/
COPY resources/ ./resources/

# 创建模型目录
RUN mkdir -p ./src/modelscope/hub

# 设置环境变量
ENV PYTHONPATH=/app/src
ENV MODELSCOPE_CACHE=/app/src/modelscope/hub

# 暴露端口（如果需要Web界面）
EXPOSE 8080

# 创建启动脚本
RUN echo '#!/bin/bash\n\
echo "Dou-flow Docker容器启动中..."\n\
echo "注意：Docker版本主要用于服务器部署"\n\
echo "桌面版本请使用macOS应用包"\n\
cd /app\n\
python src/main.py\n\
' > /app/start.sh && chmod +x /app/start.sh

# 设置启动命令
CMD ["/app/start.sh"]
EOL

# 创建.dockerignore
print_info "创建.dockerignore..."
cat > .dockerignore << 'EOL'
# 忽略不需要的文件
.git
.gitignore
*.md
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
build/
dist/
*.egg-info/
.pytest_cache/
.coverage
.DS_Store
logs/
*.log
Dou-flow.app/
dist_*/
tools/
docs/
EOL

# 构建Docker镜像
IMAGE_NAME="dou-flow"
IMAGE_TAG="latest"

print_info "构建Docker镜像..."
print_warning "这可能需要10-15分钟，请耐心等待..."

if docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .; then
    print_success "Docker镜像构建完成"
else
    print_error "Docker镜像构建失败"
    exit 1
fi

# 创建分发目录
DIST_DIR="dist_docker"
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"

# 导出Docker镜像
print_info "导出Docker镜像..."
docker save "${IMAGE_NAME}:${IMAGE_TAG}" | gzip > "$DIST_DIR/dou-flow-docker.tar.gz"

# 创建Docker Compose文件
print_info "创建Docker Compose配置..."
cat > "$DIST_DIR/docker-compose.yml" << 'EOL'
version: '3.8'

services:
  dou-flow:
    image: dou-flow:latest
    container_name: dou-flow-app
    restart: unless-stopped
    volumes:
      # 挂载音频设备（Linux）
      - /dev/snd:/dev/snd
      # 挂载配置目录
      - ./config:/app/config
      # 挂载日志目录
      - ./logs:/app/logs
    devices:
      # 音频设备访问
      - /dev/snd
    environment:
      - DISPLAY=${DISPLAY}
      - PULSE_RUNTIME_PATH=/run/user/1000/pulse
    network_mode: host
    privileged: true
EOL

# 创建启动脚本
print_info "创建启动脚本..."
cat > "$DIST_DIR/start.sh" << 'EOL'
#!/bin/bash

# Dou-flow Docker启动脚本

set -e

echo "=== Dou-flow Docker版本 ==="
echo ""

# 检查Docker是否安装
if ! command -v docker >/dev/null 2>&1; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

# 检查Docker是否运行
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker未运行，请启动Docker"
    exit 1
fi

# 加载镜像（如果需要）
if [[ -f "dou-flow-docker.tar.gz" ]] && ! docker images | grep -q "dou-flow"; then
    echo "📦 加载Docker镜像..."
    docker load < dou-flow-docker.tar.gz
fi

# 创建必要的目录
mkdir -p config logs

# 启动容器
echo "🚀 启动Dou-flow容器..."
docker-compose up -d

echo "✅ Dou-flow已启动"
echo ""
echo "查看日志: docker-compose logs -f"
echo "停止服务: docker-compose down"
EOL

chmod +x "$DIST_DIR/start.sh"

# 创建停止脚本
cat > "$DIST_DIR/stop.sh" << 'EOL'
#!/bin/bash

echo "🛑 停止Dou-flow容器..."
docker-compose down

echo "✅ Dou-flow已停止"
EOL

chmod +x "$DIST_DIR/stop.sh"

# 创建使用说明
cat > "$DIST_DIR/README.md" << 'EOL'
# Dou-flow Docker版本

## 系统要求

- Docker Desktop (macOS/Windows) 或 Docker Engine (Linux)
- 音频设备支持

## 安装步骤

1. **安装Docker**：
   - macOS/Windows: 下载Docker Desktop
   - Linux: 安装Docker Engine

2. **加载应用**：
   ```bash
   # 解压分发包
   tar -xzf dou-flow-docker.tar.gz
   cd dou-flow-docker/
   
   # 启动应用
   ./start.sh
   ```

3. **停止应用**：
   ```bash
   ./stop.sh
   ```

## 使用方法

Docker版本主要用于：
- 服务器部署
- 跨平台运行
- 开发环境隔离

## 注意事项

- Docker版本不支持桌面快捷键功能
- 音频设备访问可能需要额外配置
- 建议桌面用户使用macOS应用包版本

## 命令参考

```bash
# 查看运行状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 进入容器
docker-compose exec dou-flow bash

# 重启服务
docker-compose restart
```

## 故障排除

1. **音频设备问题**：确保Docker有音频设备访问权限
2. **权限问题**：可能需要以管理员身份运行
3. **网络问题**：检查防火墙设置

---
版本：Docker 1.0
开发者：ttmouse
EOL

# 清理临时文件
print_info "清理临时文件..."
rm -f Dockerfile .dockerignore

print_success "=== Docker版本打包完成 ==="
echo ""
echo "📦 Docker镜像：${IMAGE_NAME}:${IMAGE_TAG}"
echo "📁 分发包：$DIST_DIR/"
echo "📖 使用说明：$DIST_DIR/README.md"
echo ""
print_info "Docker版本适用于服务器部署和跨平台运行"
print_warning "桌面用户建议使用macOS应用包版本"
