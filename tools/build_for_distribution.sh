#!/bin/bash

# 分发版本打包脚本
# 创建可在任何Mac上运行的完整应用包

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

# 应用信息
APP_NAME="Dou-flow"
DIST_DIR="dist_release"
APP_PATH="$DIST_DIR/${APP_NAME}.app"

print_info "=== 开始创建分发版本 ==="

# 清理旧的分发目录
if [[ -d "$DIST_DIR" ]]; then
    print_info "清理旧的分发目录..."
    rm -rf "$DIST_DIR"
fi

mkdir -p "$DIST_DIR"

# 更新版本号
print_info "更新版本号..."
python tools/version_manager.py

# 创建应用包结构
print_info "创建应用包结构..."
mkdir -p "${APP_PATH}/Contents/"{MacOS,Resources,Frameworks}

# 复制源代码
print_info "复制源代码..."
cp -r src "${APP_PATH}/Contents/Resources/"
cp -r resources "${APP_PATH}/Contents/Resources/"
cp requirements.txt "${APP_PATH}/Contents/Resources/"

# 复制图标
if [[ -f "app_icon.icns" ]]; then
    cp "app_icon.icns" "${APP_PATH}/Contents/Resources/"
fi

# 创建Info.plist
print_info "创建Info.plist..."
cat > "${APP_PATH}/Contents/Info.plist" << EOL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>Dou-flow</string>
    <key>CFBundleIconFile</key>
    <string>app_icon</string>
    <key>CFBundleIdentifier</key>
    <string>com.ttmouse.douflow</string>
    <key>CFBundleName</key>
    <string>${APP_NAME}</string>
    <key>CFBundleDisplayName</key>
    <string>Dou-flow 语音转文本</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>11.0</string>
    <key>NSMicrophoneUsageDescription</key>
    <string>Dou-flow需要使用麦克风来录制音频进行语音识别</string>
    <key>NSAppleEventsUsageDescription</key>
    <string>Dou-flow需要访问系统事件以支持快捷键和自动粘贴功能</string>
    <key>NSAppleEventsEnabled</key>
    <true/>
    <key>NSAccessibilityUsageDescription</key>
    <string>Dou-flow需要辅助功能权限来支持自动粘贴到其他应用</string>
    <key>LSApplicationCategoryType</key>
    <string>public.app-category.productivity</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
</dict>
</plist>
EOL

# 创建entitlements.plist
print_info "创建权限配置..."
cat > "${APP_PATH}/Contents/entitlements.plist" << EOL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.automation.apple-events</key>
    <true/>
    <key>com.apple.security.device.microphone</key>
    <true/>
    <key>com.apple.security.device.audio-input</key>
    <true/>
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
    <key>com.apple.security.temporary-exception.apple-events</key>
    <array>
        <string>com.apple.systemevents</string>
        <string>com.apple.finder</string>
        <string>*</string>
    </array>
    <key>com.apple.security.files.user-selected.read-write</key>
    <true/>
</dict>
</plist>
EOL

print_info "创建智能启动脚本..."

# 创建智能启动脚本
cat > "${APP_PATH}/Contents/MacOS/Dou-flow" << 'EOL'
#!/bin/bash

# Dou-flow 智能启动脚本
# 自动检测和安装运行环境

set -e

# 获取应用路径
APP_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
RESOURCES_DIR="$APP_DIR/Contents/Resources"
cd "$RESOURCES_DIR"

# 日志文件
LOG_FILE="$HOME/Library/Logs/Dou-flow.log"
mkdir -p "$(dirname "$LOG_FILE")"

# 日志函数
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# 显示用户友好的对话框
show_dialog() {
    local message="$1"
    local type="${2:-note}"  # note, caution, stop
    osascript -e "display dialog \"$message\" buttons {\"确定\"} default button \"确定\" with icon $type with title \"Dou-flow\""
}

show_progress() {
    local message="$1"
    osascript -e "display notification \"$message\" with title \"Dou-flow\" subtitle \"正在处理...\""
}

# 检查系统要求
check_system_requirements() {
    log "检查系统要求..."

    # 检查macOS版本
    local macos_version=$(sw_vers -productVersion)
    local major_version=$(echo "$macos_version" | cut -d. -f1)

    if [[ "$major_version" -lt 11 ]]; then
        show_dialog "此应用需要 macOS 11.0 或更高版本。
当前版本：$macos_version" "stop"
        exit 1
    fi

    # 检查架构
    local arch=$(uname -m)
    log "系统架构：$arch"
    log "macOS版本：$macos_version"
}

# 检查并安装Miniconda
install_miniconda() {
    log "检查Miniconda安装状态..."

    if command -v conda >/dev/null 2>&1; then
        log "Miniconda已安装"
        return 0
    fi

    show_dialog "首次运行需要安装Python环境（Miniconda）。
这是一个一次性过程，大约需要5-10分钟。
点击确定开始安装..." "caution"

    show_progress "正在下载Miniconda..."

    # 检测架构并下载对应版本
    local arch=$(uname -m)
    local miniconda_url

    if [[ "$arch" == "arm64" ]]; then
        miniconda_url="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh"
    else
        miniconda_url="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh"
    fi

    local installer_path="/tmp/miniconda_installer.sh"

    if ! curl -L -o "$installer_path" "$miniconda_url"; then
        show_dialog "下载Miniconda失败。请检查网络连接。" "stop"
        exit 1
    fi

    show_progress "正在安装Miniconda..."

    # 静默安装到用户目录
    chmod +x "$installer_path"
    if ! bash "$installer_path" -b -p "$HOME/miniconda3"; then
        show_dialog "安装Miniconda失败。" "stop"
        exit 1
    fi

    # 清理安装文件
    rm -f "$installer_path"

    # 初始化conda
    "$HOME/miniconda3/bin/conda" init bash

    log "Miniconda安装完成"
}

# 创建和配置Python环境
setup_python_environment() {
    log "设置Python环境..."

    # 确保conda可用
    if [[ -f "$HOME/miniconda3/bin/conda" ]]; then
        export PATH="$HOME/miniconda3/bin:$PATH"
    else
        show_dialog "找不到conda，请重新安装。" "stop"
        exit 1
    fi

    # 检查环境是否存在
    if conda env list | grep -q "douflow_env"; then
        log "Python环境已存在"
    else
        show_progress "正在创建Python环境..."

        # 创建环境
        if ! conda create -n douflow_env python=3.10 -y; then
            show_dialog "创建Python环境失败。" "stop"
            exit 1
        fi

        log "Python环境创建完成"
    fi

    # 激活环境
    eval "$(conda shell.bash hook)"
    conda activate douflow_env

    # 检查并安装依赖
    show_progress "正在安装应用依赖..."

    if ! pip install -r requirements.txt; then
        show_dialog "安装应用依赖失败。请检查网络连接。" "stop"
        exit 1
    fi

    log "依赖安装完成"
}

# 启动应用
start_application() {
    log "启动Dou-flow应用..."

    # 确保在正确的环境中
    eval "$(conda shell.bash hook)"
    conda activate douflow_env

    # 启动应用
    python src/main.py 2>&1 | tee -a "$LOG_FILE"
}

# 主函数
main() {
    log "=== Dou-flow 启动 ==="

    # 检查系统要求
    check_system_requirements

    # 安装Miniconda（如果需要）
    install_miniconda

    # 设置Python环境
    setup_python_environment

    # 启动应用
    start_application
}

# 错误处理
trap 'log "启动过程中发生错误，请查看日志：$LOG_FILE"' ERR

# 运行主函数
main "$@"
EOL

chmod +x "${APP_PATH}/Contents/MacOS/Dou-flow"

# 创建用户指南
print_info "创建用户指南..."
cat > "$DIST_DIR/使用说明.md" << 'EOL'
# Dou-flow 语音转文本应用

## 📋 系统要求

- macOS 11.0 或更高版本
- 网络连接（首次运行时下载依赖）
- 麦克风权限
- 辅助功能权限（用于自动粘贴）

## 🚀 安装步骤

1. **下载应用**：将 `Dou-flow.app` 复制到您的"应用程序"文件夹

2. **首次运行**：
   - 双击 `Dou-flow.app` 启动
   - 首次运行会自动安装Python环境（需要5-10分钟）
   - 按照提示授予必要的权限

3. **权限设置**：
   - **麦克风权限**：系统设置 > 隐私与安全性 > 麦克风
   - **辅助功能权限**：系统设置 > 隐私与安全性 > 辅助功能
   - **自动化权限**：系统设置 > 隐私与安全性 > 自动化

## 🎯 使用方法

1. **启动应用**：双击应用图标
2. **开始录音**：按住 `Fn` 键开始录音
3. **结束录音**：松开 `Fn` 键，文本会自动粘贴到当前应用
4. **查看历史**：在应用窗口中查看转写历史

## 🔧 快捷键

- `Fn` 键：按住录音，松开停止
- 可在设置中修改为其他快捷键

## ❓ 常见问题

### Q: 首次运行很慢？
A: 首次运行需要下载和安装Python环境，这是正常的一次性过程。

### Q: 录音没有反应？
A: 请检查麦克风权限是否已授予。

### Q: 文本没有自动粘贴？
A: 请检查辅助功能权限是否已授予。

### Q: 应用无法启动？
A: 请查看日志文件：`~/Library/Logs/Dou-flow.log`

## 📞 技术支持

如有问题，请查看日志文件或联系开发者。

---
版本：1.0
开发者：ttmouse
EOL

# 创建安装脚本
print_info "创建安装脚本..."
cat > "$DIST_DIR/安装.command" << 'EOL'
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
EOL

chmod +x "$DIST_DIR/安装.command"

# 移除扩展属性
print_info "清理扩展属性..."
xattr -cr "${APP_PATH}"

# 代码签名（如果有开发者证书）
print_info "尝试代码签名..."
if codesign --force --deep --sign - --entitlements "${APP_PATH}/Contents/entitlements.plist" "${APP_PATH}" 2>/dev/null; then
    print_success "代码签名完成"
else
    print_warning "代码签名跳过（无开发者证书）"
fi

# 创建DMG镜像（可选）
create_dmg() {
    print_info "创建DMG安装镜像..."

    local dmg_name="${APP_NAME}-installer.dmg"
    local temp_dmg="/tmp/${dmg_name}"

    # 创建临时DMG
    hdiutil create -size 500m -fs HFS+ -volname "Dou-flow Installer" "$temp_dmg"

    # 挂载DMG
    local mount_point=$(hdiutil attach "$temp_dmg" | grep "/Volumes" | awk '{print $3}')

    # 复制文件到DMG
    cp -R "${APP_PATH}" "$mount_point/"
    cp "$DIST_DIR/使用说明.md" "$mount_point/"
    cp "$DIST_DIR/安装.command" "$mount_point/"

    # 创建应用程序文件夹的符号链接
    ln -s /Applications "$mount_point/Applications"

    # 卸载DMG
    hdiutil detach "$mount_point"

    # 压缩DMG
    hdiutil convert "$temp_dmg" -format UDZO -o "$DIST_DIR/$dmg_name"
    rm "$temp_dmg"

    print_success "DMG镜像创建完成：$DIST_DIR/$dmg_name"
}

# 询问是否创建DMG
read -p "是否创建DMG安装镜像？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    create_dmg
fi

# 完成
print_success "=== 分发版本创建完成 ==="
echo ""
echo "📦 分发文件位置：$DIST_DIR/"
echo "📱 应用文件：${APP_PATH}"
echo "📖 使用说明：$DIST_DIR/使用说明.md"
echo "🔧 安装脚本：$DIST_DIR/安装.command"
echo ""
print_info "您可以将整个 $DIST_DIR 文件夹打包分发给用户"
print_warning "用户首次运行时会自动下载和安装Python环境"
