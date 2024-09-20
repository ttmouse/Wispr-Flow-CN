import sys
import os
import traceback
import logging
import PyInstaller.__main__
import funasr
import shutil
from modelscope.hub.snapshot_download import snapshot_download

# 设置日志记录
logging.basicConfig(filename='build_app.log', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

logging.info("开始执行 build_app.py")

# 获取当前脚本所在的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

try:
    logging.info("开始执行主程序")
    
    # 检查模型文件是否存在
    model_path = os.path.join(current_dir, 'models', 'paraformer-zh', 'model.pt')
    if not os.path.exists(model_path):
        logging.error(f"模型文件不存在: {model_path}")
        raise FileNotFoundError(f"模型文件不存在: {model_path}")
    logging.info(f"模型文件存在: {model_path}")

    logging.info("开始运行 PyInstaller")

    funasr_path = os.path.dirname(funasr.__file__)
    version_file = os.path.join(funasr_path, 'version.txt')

    # 确保 version.txt 文件存在
    if not os.path.exists(version_file):
        logging.warning(f"version.txt 文件不存在: {version_file}")
        with open(version_file, 'w') as f:
            f.write("0.0.0")  # 写入一个默认版本号

    # 复制 version.txt 到当前目录
    local_version_file = os.path.join(current_dir, 'funasr_version.txt')
    shutil.copy2(version_file, local_version_file)

    # 修改 .spec 文件
    spec_file = 'FunASR语音转文字.spec'
    with open(spec_file, 'r') as f:
        spec_content = f.read()

    # 添加 funasr_version.txt 到 datas
    new_data_line = f"        ('{local_version_file}', 'funasr'),"
    spec_content = spec_content.replace(
        "datas=[",
        f"datas=[\n{new_data_line}"
    )

    # 添加 entitlements 到 BUNDLE
    entitlements_file = os.path.join(current_dir, 'entitlements.plist')
    with open(entitlements_file, 'w') as f:
        f.write('''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
    <key>com.apple.security.device.audio-input</key>
    <true/>
</dict>
</plist>
''')

    # 修改 codesign_identity
    spec_content = spec_content.replace(
        "codesign_identity=None,",
        "codesign_identity='-',"
    )

    # 修改 entitlements_file
    spec_content = spec_content.replace(
        "entitlements_file=None,",
        f"entitlements_file='{entitlements_file}',"
    )

    with open(spec_file, 'w') as f:
        f.write(spec_content)

    # 运行 PyInstaller
    PyInstaller.__main__.run([
        spec_file,
        '--clean',
        '--noconfirm',
    ])

    logging.info("PyInstaller 运行完成")

    # 删除临时创建的文件
    os.remove(local_version_file)

    # 复制 Info.plist 文件
    dist_dir = os.path.join(current_dir, 'dist')
    app_name = 'FunASR语音转文字.app'
    contents_dir = os.path.join(dist_dir, app_name, 'Contents')
    shutil.copy2(os.path.join(current_dir, 'Info.plist'), contents_dir)

    logging.info("打包完成，Info.plist 已添加到应用程序包中。")

    # 重新签名应用程序
    os.system(f'codesign --force --deep --sign - {os.path.join(dist_dir, app_name)}')
    logging.info("应用程序重新签名完成")

except Exception as e:
    logging.error(f"打包过程中出现错误: {e}")
    logging.error(traceback.format_exc())
    sys.exit(1)