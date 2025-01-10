#!/bin/bash

# 获取脚本所在目录
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR/.."

# 应用名称
APP_NAME="Dou-flow"

# 创建应用包结构
rm -rf "$APP_NAME.app"
mkdir -p "$APP_NAME.app/Contents/"{MacOS,Resources}

# 复制资源文件
cp -r resources "$APP_NAME.app/Contents/Resources/"
cp icon_1024.png "$APP_NAME.app/Contents/Resources/"

# 创建启动脚本
cat > "$APP_NAME.app/Contents/MacOS/start.sh" << 'EOL'
#!/bin/bash
cd "$(dirname "$0")"
cd ../../..
source venv/bin/activate
python3 src/main.py
EOL

chmod +x "$APP_NAME.app/Contents/MacOS/start.sh"

# 创建 Info.plist
cat > "$APP_NAME.app/Contents/Info.plist" << EOL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>start.sh</string>
    <key>CFBundleIconFile</key>
    <string>icon_1024</string>
    <key>CFBundleIdentifier</key>
    <string>com.ttmouse.douflow</string>
    <key>CFBundleName</key>
    <string>Dou-flow</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.10</string>
    <key>CFBundleSupportedPlatforms</key>
    <array>
        <string>MacOSX</string>
    </array>
</dict>
</plist>
EOL

echo "✓ 应用打包完成: $APP_NAME.app"
