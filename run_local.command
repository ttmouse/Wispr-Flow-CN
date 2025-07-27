#!/bin/bash

# 设置应用名称
APP_NAME="Dou-flow"

# 创建应用包结构
mkdir -p "${APP_NAME}.app/Contents/"{MacOS,Resources}

# 创建 Info.plist
cat > "${APP_NAME}.app/Contents/Info.plist" << EOL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>run.command</string>
    <key>CFBundleIconFile</key>
    <string>app_icon</string>
    <key>CFBundleIdentifier</key>
    <string>com.douba.douflow</string>
    <key>CFBundleName</key>
    <string>${APP_NAME}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.10</string>
    <key>NSMicrophoneUsageDescription</key>
    <string>需要使用麦克风来录制音频</string>
    <key>NSAppleEventsUsageDescription</key>
    <string>需要访问系统事件以支持快捷键和粘贴功能</string>
    <key>NSAppleEventsEnabled</key>
    <true/>
    <key>NSAccessibilityUsageDescription</key>
    <string>需要辅助功能权限来支持自动粘贴</string>
</dict>
</plist>
EOL

# 创建 entitlements.plist
cat > "${APP_NAME}.app/Contents/entitlements.plist" << EOL
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

# 创建启动脚本
cat > "${APP_NAME}.app/Contents/MacOS/run.command" << 'EOL'
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

# 检查并安装conda环境
check_and_install_conda() {
    # 检查conda是否安装
    if ! command -v conda >/dev/null 2>&1; then
        show_error "未检测到conda环境。请先安装Miniconda：

1. 访问 https://docs.conda.io/en/latest/miniconda.html
2. 下载适合您系统的版本
3. 安装后重新运行此应用"
        return 1
    fi

    # 检查funasr_env环境是否存在
    if ! conda env list | grep -q "funasr_env"; then
        show_info "首次运行需要安装依赖环境，这可能需要几分钟时间..."

        # 创建环境
        conda create -n funasr_env python=3.10 -y || show_error "创建conda环境失败"

        # 激活环境并安装依赖
        eval "$(conda shell.bash hook)"
        conda activate funasr_env
        pip install -r requirements.txt || show_error "安装依赖失败"

        show_info "环境安装完成！"
    fi
}

# 主要逻辑
main() {
    # 检查并安装环境
    check_and_install_conda

    # 激活环境
    if [ -f "$HOME/miniconda3/bin/activate" ]; then
        source "$HOME/miniconda3/bin/activate" funasr_env
    elif [ -f "/opt/miniconda3/bin/activate" ]; then
        source "/opt/miniconda3/bin/activate" funasr_env
    elif [ -f "$HOME/anaconda3/bin/activate" ]; then
        source "$HOME/anaconda3/bin/activate" funasr_env
    elif command -v conda >/dev/null 2>&1; then
        eval "$(conda shell.bash hook)"
        conda activate funasr_env
    else
        show_error "无法激活conda环境"
    fi

    # 检查Python环境
    if ! command -v python >/dev/null 2>&1; then
        show_error "Python环境异常"
    fi

    # 运行程序
    python src/main.py 2>&1 | tee app_error.log
}

main "$@"
EOL

# 设置执行权限
chmod +x "${APP_NAME}.app/Contents/MacOS/run.command"

# 复制图标
if [ -f "app_icon.icns" ]; then
    cp "app_icon.icns" "${APP_NAME}.app/Contents/Resources/"
fi

# 移除扩展属性
xattr -cr "${APP_NAME}.app"

# 对应用进行签名
codesign --force --deep --sign - --entitlements "${APP_NAME}.app/Contents/entitlements.plist" "${APP_NAME}.app"