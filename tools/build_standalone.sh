#!/bin/bash

# PyInstaller 独立打包脚本
# 创建完全独立的可执行文件，无需任何Python环境

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

print_info "=== PyInstaller 独立打包 ==="

# 检查conda环境
if ! conda env list | grep -q "funasr_env"; then
    print_error "funasr_env环境不存在，请先运行: conda create -n funasr_env python=3.10"
    exit 1
fi

# 激活环境
print_info "激活conda环境..."
eval "$(conda shell.bash hook)"
conda activate funasr_env

# 安装PyInstaller
print_info "检查PyInstaller..."
if ! pip show pyinstaller >/dev/null 2>&1; then
    print_info "安装PyInstaller..."
    pip install pyinstaller
fi

# 清理旧的构建文件
print_info "清理旧的构建文件..."
rm -rf build/ dist/ *.spec

# 创建PyInstaller配置文件
print_info "创建PyInstaller配置..."
cat > Dou-flow.spec << 'EOL'
# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 收集数据文件
datas = []
datas += collect_data_files('funasr')
datas += collect_data_files('modelscope')
datas += [('resources', 'resources')]
datas += [('src/modelscope', 'modelscope')]

# 收集隐藏导入
hiddenimports = []
hiddenimports += collect_submodules('funasr')
hiddenimports += collect_submodules('modelscope')
hiddenimports += [
    'PyQt6.QtCore',
    'PyQt6.QtGui', 
    'PyQt6.QtWidgets',
    'torch',
    'torchaudio',
    'numpy',
    'scipy',
    'librosa',
    'soundfile',
    'pyaudio',
    'pynput',
    'pyperclip',
    'pyobjc-core',
    'pyobjc-framework-Cocoa',
    'pyobjc-framework-Quartz',
    'pyobjc-framework-ApplicationServices',
]

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Dou-flow',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app_icon.icns' if os.path.exists('app_icon.icns') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Dou-flow',
)

app = BUNDLE(
    coll,
    name='Dou-flow.app',
    icon='app_icon.icns' if os.path.exists('app_icon.icns') else None,
    bundle_identifier='com.ttmouse.douflow',
    info_plist={
        'NSMicrophoneUsageDescription': 'Dou-flow需要使用麦克风来录制音频进行语音识别',
        'NSAppleEventsUsageDescription': 'Dou-flow需要访问系统事件以支持快捷键和自动粘贴功能',
        'NSAccessibilityUsageDescription': 'Dou-flow需要辅助功能权限来支持自动粘贴到其他应用',
        'LSApplicationCategoryType': 'public.app-category.productivity',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
    },
)
EOL

# 开始打包
print_info "开始PyInstaller打包..."
print_warning "这可能需要10-20分钟，请耐心等待..."

if pyinstaller Dou-flow.spec; then
    print_success "PyInstaller打包完成"
else
    print_error "PyInstaller打包失败"
    exit 1
fi

# 创建分发目录
DIST_DIR="dist_standalone"
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"

# 移动应用
if [[ -d "dist/Dou-flow.app" ]]; then
    mv "dist/Dou-flow.app" "$DIST_DIR/"
    print_success "应用已移动到 $DIST_DIR/"
else
    print_error "找不到打包后的应用"
    exit 1
fi

# 创建使用说明
cat > "$DIST_DIR/使用说明.txt" << 'EOL'
Dou-flow 语音转文本应用 - 独立版本

系统要求：
- macOS 11.0 或更高版本
- 无需安装Python或其他依赖

安装方法：
1. 将 Dou-flow.app 复制到"应用程序"文件夹
2. 首次运行时，右键点击应用，选择"打开"（绕过安全检查）
3. 授予麦克风和辅助功能权限

使用方法：
- 按住 Fn 键开始录音
- 松开 Fn 键结束录音，文本自动粘贴

注意事项：
- 首次运行可能需要几分钟加载模型
- 如果遇到问题，请查看控制台日志

版本：独立版 1.0
开发者：ttmouse
EOL

# 清理构建文件
print_info "清理构建文件..."
rm -rf build/ dist/ *.spec

print_success "=== 独立版本打包完成 ==="
echo ""
echo "📦 独立版本位置：$DIST_DIR/Dou-flow.app"
echo "📖 使用说明：$DIST_DIR/使用说明.txt"
echo ""
print_info "此版本无需任何Python环境，可直接在任何Mac上运行"
print_warning "文件较大（约1-2GB），但启动速度较慢"
