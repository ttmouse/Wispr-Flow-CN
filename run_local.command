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
    <key>com.apple.security.automation.apple-events</key>
    <true/>
    <key>com.apple.security.personal-information.addressbook</key>
    <true/>
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

# 激活 conda 环境
source ~/miniconda3/bin/activate funasr_env

# 运行程序
python src/main.py
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