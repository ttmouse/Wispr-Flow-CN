# Wispr Flow CN (Dou-flow)

一个基于 FunASR 的 macOS 语音转文字应用程序，支持全局快捷键录音和自动文本粘贴。

!\[应用截图]\(screenshot.png null)

## 特性

* 🎤 **全局快捷键录音**: 按住 Option 键即可开始录音，支持自定义快捷键

* 🔄 **实时语音识别**: 基于 FunASR 的高精度中文语音识别，支持离线模式

* 📋 **自动文本粘贴**: 识别结果自动复制到剪贴板并粘贴到当前应用

* 🖥️ **现代化界面**: 基于 PyQt6 的简洁美观界面设计，支持无边框窗口

* 📱 **系统托盘支持**: 完整的系统托盘集成，支持快速操作和状态监控

* 📝 **历史记录管理**: 持久化保存转录历史，支持点击复制和搜索

* ⚙️ **灵活配置**: 支持快捷键配置、音频参数调整、模型设置

* 🔧 **热词管理**: 自定义词典和专业术语，提高识别准确率

* 🔒 **离线工作**: 完全离线运行，基于本地 FunASR 模型，保护隐私安全

* 🚀 **性能优化**: 异步初始化、内存优化、多线程音频处理

## 安装

### 系统要求

* macOS 10.14 或更高版本

* Python 3.8 或更高版本

* 至少 4GB RAM（推荐 8GB）

* 2GB 可用存储空间（包含 FunASR 模型）

* 麦克风访问权限

* 辅助功能权限（用于全局快捷键和自动粘贴）

### 安装步骤

1. 克隆仓库：

```bash
git clone https://github.com/ttmouse/Wispr-Flow-CN.git
cd Wispr-Flow-CN
```

1. 创建虚拟环境：

```bash
python -m venv py310
source py310/bin/activate  # Linux/Mac
# 或
.\py310\Scripts\activate  # Windows
```

1. 安装依赖：

```bash
# 克隆项目
git clone <repository-url>
cd ASR-FunASR

# 安装依赖
pip install -r requirements.txt
```

主要依赖包括：

* `funasr`: FunASR 语音识别引擎

* `PyQt6`: GUI 框架 (6.4.0+)

* `PyAudio`: 音频捕获和处理

* `pynput`: 全局快捷键监听

* `pyperclip`: 剪贴板操作

* `torch`: 深度学习框架

* `modelscope`: 模型下载和管理

* `pyobjc`: macOS 系统集成

## 使用方法

### 方式一：打包应用（推荐）

```bash
bash tools/build_app.sh
```

打包后的应用会自动请求所需权限，快捷键功能可正常使用。

### 方式二：使用快捷启动脚本

1. macOS 用户：

   * 双击 `run_local.command` 文件即可启动应用

   * 首次运行可能需要在系统偏好设置中允许运行

2. Windows 用户：

   * 双击 `run_local.bat` 文件即可启动应用

### 方式三：命令行启动（开发模式）

1. 激活虚拟环境：

```bash
source py310/bin/activate  # Linux/Mac
# 或
.\py310\Scripts\activate  # Windows
```

1. 运行程序：

```bash
# 开发模式
python src/main.py

# 或者使用打包后的应用
./dist/main.app
```

⚠️ **注意：macOS 用户直接运行 Python 脚本时，快捷键功能可能无效**

### macOS 权限问题解决

如果直接运行 `python src/main.py` 时快捷键录音无效，请按以下步骤操作：

1. **检查权限状态：**

```bash
python tools/check_dev_permissions.py
```

1. **授予辅助功能权限：**

   * 打开 系统设置 > 隐私与安全性 > 辅助功能

   * 点击 '+' 按钮添加您的终端应用（如 Terminal.app、iTerm.app、PyCharm 等）

   * 确保应用已勾选

   * 重新运行程序

2. **常见终端应用路径：**

   * Terminal.app: `/System/Applications/Utilities/Terminal.app`

   * iTerm.app: `/Applications/iTerm.app`

   * PyCharm: `/Applications/PyCharm CE.app`

   * VS Code: `/Applications/Visual Studio Code.app`

💡 **建议：** 开发时使用打包应用 (`bash tools/build_app.sh`)，可避免权限问题。

## 基本操作

1. **开始录音**: 按住配置的快捷键（默认 Option 键）
2. **停止录音**: 松开快捷键，系统自动进行语音识别
3. **查看结果**: 转录文本自动复制到剪贴板并粘贴到当前应用
4. **查看历史**: 在主界面查看所有转录历史，支持时间戳显示
5. **复制历史**: 点击历史记录项可重新复制到剪贴板
6. **系统托盘**: 通过托盘图标快速访问应用功能

## 配置说明

### 快捷键设置

* 默认快捷键：Option 键

* 支持通过设置界面自定义快捷键组合

* 快捷键：Cmd+, 或 Ctrl+, 打开设置面板

* 支持单键和复杂组合键配置

### 音频设置

* 采样率：16000 Hz（推荐，可调整）

* 声道：单声道

* 位深度：16 位

* 缓冲区大小：可在设置中调整以优化延迟和稳定性

* 音量阈值：自动检测和手动调整

### 模型配置

* FunASR 模型：支持多种预训练模型

* 热词支持：可添加自定义词典提高识别准确率

* 量化优化：减少内存使用，提高推理速度

### 高频词设置

1. 点击右上角的设置按钮（⚙）
2. 在设置窗口中输入高频词，每行一个
3. 点击保存即可生效

## 开发说明

### 项目结构

```
src/
├── main.py                 # 主程序入口和应用控制器
├── config.py              # 配置管理和版本信息
├── constants.py           # 应用常量定义
├── audio_capture.py       # 音频捕获模块
├── audio_manager.py       # 音频管理和处理
├── audio_threads.py       # 音频线程处理
├── funasr_engine.py       # FunASR 引擎封装
├── hotkey_manager.py      # 热键管理
├── global_hotkey.py       # 全局快捷键处理
├── clipboard_manager.py   # 剪贴板管理
├── state_manager.py       # 应用状态管理
├── context_manager.py     # 上下文管理
├── settings_manager.py    # 设置持久化管理
├── resource_utils.py      # 资源工具和路径管理
└── ui/                    # 用户界面模块
    ├── main_window.py     # 主窗口界面
    ├── settings_window.py # 设置窗口
    ├── hotwords_window.py # 热词管理窗口
    ├── menu_manager.py    # 菜单管理
    └── components/        # UI 组件库
```

### 技术栈

* **GUI 框架**: PyQt6 6.4.0+

* **语音识别**: FunASR (ModelScope)

* **音频处理**: PyAudio, torchaudio

* **系统集成**: pynput (热键), pyperclip (剪贴板), pyobjc (macOS API)

* **深度学习**: PyTorch, numpy

* **打包工具**: PyInstaller

* **其他工具**: watchdog (文件监控), requests (网络请求)

* **模型**: Paraformer-large

### 打包发布

使用 PyInstaller 打包成 macOS 应用：

```bash
# 基本打包
pyinstaller --windowed --onefile --icon=iconset.icns src/main.py

# 高级打包（包含所有依赖）
pyinstaller --windowed --onefile \
    --icon=iconset.icns \
    --add-data="src/ui:ui" \
    --add-data="iconset.icns:." \
    --hidden-import=funasr \
    --hidden-import=modelscope \
    src/main.py
```

### 开发工具

```bash
# 代码格式化
black src/
isort src/

# 代码检查
flake8 src/
mypy src/

# 运行测试
python -m pytest tests/
```

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 贡献指南

欢迎提交 Issue 和 Pull Request。在提交 PR 之前，请确保：

1. 代码风格符合项目规范
2. 添加了必要的测试
3. 更新了相关文档

## 致谢

* [FunASR](https://github.com/alibaba-damo-academy/FunASR)：提供了强大的语音识别能力

* [ModelScope](https://www.modelscope.cn/)：提供了优秀的模型资源

* [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)：提供了现代的 GUI 框架

## 更新日志

### v1.0.0  2025-01-02

* 初始版本发布

* 支持实时语音识别

* 支持历史记录管理

* 支持高频词配置

