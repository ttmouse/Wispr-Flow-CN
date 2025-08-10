# CLAUDE.md

此文件为 Claude Code (claude.ai/code) 在此代码库中工作时提供指导。

## 项目概述

这是 **Dou-flow** (Wispr Flow CN)，一个基于 FunASR 的 macOS 语音转文字应用程序。它提供实时中文语音识别、全局热键录音、自动文本粘贴和现代化的 PyQt6 图形界面。

## 常用开发命令

### 运行应用程序

#### 开发模式（推荐用于测试）
```bash
# 使用 conda 环境（推荐）
./start_dev.sh

# 或直接使用 Python（需要设置权限）
python src/main.py
```

#### 生产构建
```bash
# 创建打包的 macOS 应用
bash tools/build_app.sh

# 或使用便捷脚本
./run_local.command
```

### 环境设置
```bash
# 创建 conda 环境
conda create -n funasr_env python=3.10 -y
conda activate funasr_env
pip install -r requirements.txt
```

### 测试
```bash
# 运行基础功能测试
python tests/test_context.py

# 测试音频设备配置
python test_audio_devices.py

# 检查开发权限
python tools/check_dev_permissions.py
```

### 调试和验证
```bash
# 检查代码重构完整性
python validate_refactoring.py

# 诊断 ASR 问题
python diagnose_asr.py

# 简单功能测试
python simple_test.py
```

## 架构概览

### 核心应用结构

应用程序采用模块化架构的**管理器-包装器模式**：

```
src/
├── main.py                 # 应用程序入口和主控制器
├── managers/               # 管理器包装器模式实现
│   ├── ui_manager_wrapper.py
│   ├── audio_manager_wrapper.py
│   ├── state_manager_wrapper.py
│   └── [其他管理器包装器]
├── funasr_engine.py       # FunASR 语音识别引擎
├── audio_capture.py       # 音频录制功能
├── hotkey_manager.py      # 全局热键处理
├── clipboard_manager.py   # 剪贴板操作
└── ui/                    # PyQt6 用户界面组件
```

### 核心组件

1. **FunASR 引擎** (`funasr_engine.py`)：使用 ModelScope 模型处理离线中文语音识别
2. **音频管理** (`audio_manager.py`, `audio_capture.py`)：录制和处理音频输入，支持可配置参数
3. **热键系统** (`hotkey_manager.py`, `global_hotkey.py`)：管理全局键盘快捷键（默认：Option 键）
4. **UI 系统** (`ui/`)：基于 PyQt6 的现代界面，包含设置、历史记录和系统托盘集成
5. **管理器包装器** (`managers/`)：为所有子系统提供统一接口的抽象层

### 配置和常量

- **`config.py`**：版本管理和基础配置
- **`constants.py`**：按类别组织的综合应用常量（音频、UI、路径、时间、模型等）
- **`settings.json`**：运行时设置，自动备份到 `settings_history/`

## macOS 特定注意事项

### 权限要求
应用程序需要特定的 macOS 权限：
- **麦克风访问**：用于音频录制
- **辅助功能**：用于全局热键和自动粘贴功能

### 开发环境 vs 生产环境权限
- **开发环境**：终端/IDE 需要辅助功能权限以支持热键功能
- **生产环境**：打包应用通过 `Info.plist` 自动请求权限

### 权限问题故障排除
运行 `python tools/check_dev_permissions.py` 诊断权限问题。详细解决方案请参见 `docs/macOS_permissions.md`。

## 模型和依赖项

### FunASR 模型
应用程序使用存储在 `src/modelscope/hub/damo/` 中的本地 ModelScope 模型：
- **语音识别**：`speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch`
- **标点符号**：`punc_ct-transformer_zh-cn-common-vocab272727-pytorch`

### 核心依赖项
- **PyQt6 6.4.0+**：现代 GUI 框架
- **FunASR**：阿里巴巴语音识别引擎
- **PyAudio**：音频捕获和处理
- **pynput**：全局热键检测
- **torch/torchaudio**：深度学习推理
- **modelscope**：模型管理

## 开发指南

### 代码模式
- **管理器-包装器模式**：所有主要子系统使用包装器类进行抽象
- **清理混入**：使用 `CleanupMixin` 基类进行适当的资源清理
- **错误处理**：使用 `utils.error_handler` 进行集中错误处理
- **日志记录**：使用特定类别记录器的结构化日志

### 文件组织
- **主要逻辑**：将应用程序逻辑保持在 `main.py` 中
- **UI 组件**：将 UI 逻辑分离到 `ui/` 目录中，采用基于组件的结构
- **工具**：将通用工具放在 `utils/` 目录中
- **设置**：使用 `SettingsManagerWrapper` 进行所有配置持久化

### macOS 应用打包
构建过程创建完整的 macOS 应用包，包含：
- 带有权限声明的合适 `Info.plist`
- 使用授权文件进行代码签名
- 资源打包和图标集成
- Conda 环境兼容性

## 重要注意事项

### 内存管理
- 应用程序加载大型 ML 模型 - 在开发过程中监控内存使用情况
- 使用 `constants.ModelConstants` 中的模型量化和缓存优化

### 音频处理
- 默认采样率：16000 Hz（针对中文 ASR 优化）
- 基于块的处理，实现实时性能
- 自动音量阈值检测

### 开发环境
- **推荐**：使用带有 `funasr_env` 环境的 conda
- **测试**：始终测试打包应用以验证权限相关功能
- **调试**：检查 `logs/` 目录中的运行时问题日志

### 设置和历史
- 设置在更改时自动备份
- 历史记录持久化且可搜索
- 可通过设置 UI 自定义热词