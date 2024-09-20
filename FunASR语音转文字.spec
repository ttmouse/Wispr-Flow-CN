# -*- mode: python ; coding: utf-8 -*-


import os
import funasr

a = Analysis(
    ['src/main.py'],  # 确保这里的路径正确
    pathex=[],
    binaries=[],
    datas=[
        ('/Users/douba/Downloads/GPT插件/ASR-FunASR/funasr_version.txt', 'funasr'),
        ('/Users/douba/Downloads/GPT插件/ASR-FunASR/funasr_version.txt', 'funasr'),
        ('src', 'src'),
        ('app_icon.icns', '.'),
        ('Info.plist', '.'),
        ('requirements.txt', '.'),
        ('src/ui/settings_window.py', 'src/ui'),
        ('src/ui/main_window.py', 'src/ui'),
        (os.path.join(os.path.dirname(funasr.__file__), 'version.txt'), 'funasr'),
        ('models/paraformer-zh', 'models/paraformer-zh'),  # 修改这行以包含正确的模型路径
    ],
    hiddenimports=['funasr', 'PyQt6', 'pyaudio', 'keyboard', 'pyperclip', 'numpy', 'modelscope', 'AVFoundation'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='FunASR语音转文字',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity='-',
    entitlements_file='entitlements.plist',
    icon='app_icon.icns',
)

app = BUNDLE(
    exe,
    name='FunASR语音转文字.app',
    icon='app_icon.icns',
    bundle_identifier='com.yourcompany.FunASR语音转文字',
    info_plist={
        'CFBundleName': 'FunASR语音转文字',
        'CFBundleDisplayName': 'FunASR语音转文字',
        'NSHumanReadableCopyright': '© 2023 Your Company',
        'NSAppleEventsUsageDescription': '需要访问权限以监听全局热键。',
        'NSMicrophoneUsageDescription': '需要访问麦克风以进行语音识别。',
        'NSAppleEventsUsageDescription': '需要辅助功能权限以使用全局热键功能。',
    },
    entitlements_file='entitlements.plist',
)
