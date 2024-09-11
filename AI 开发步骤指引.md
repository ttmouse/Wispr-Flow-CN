# FunASR 语音转文字项目指南

## 1. 项目结构设置

创建以下项目结构：

```
funasr_app/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── audio_capture.py
│   ├── funasr_engine.py
│   ├── hotkey_manager.py
│   ├── clipboard_manager.py
│   └── ui/
│       ├── __init__.py
│       └── main_window.py
├── tests/
│   ├── __init__.py
│   ├── test_audio_capture.py
│   ├── test_funasr_engine.py
│   ├── test_hotkey_manager.py
│   └── test_clipboard_manager.py
├── requirements.txt
└── README.md
```

## 2. 环境设置

1. 创建虚拟环境
2. 在`requirements.txt`中列出所需依赖：
   - funasr
   - PyAudio
   - pynput
   - pyperclip
   - PyQt6 (用于GUI)

## 3. 实现核心模块

### 3.1 音频捕获模块 (audio_capture.py)

1. 使用PyAudio库创建`AudioCapture`类
2. 实现以下方法：
   - `__init__`: 初始化PyAudio和音频流
   - `start_recording`: 开始录音
   - `stop_recording`: 停止录音并返回音频数据
   - `__del__`: 清理资源

### 3.2 FunASR 引擎模块 (funasr_engine.py)

1. 创建`FunASREngine`类
2. 实现以下方法：
   - `__init__`: 初始化FunASR模型
   - `transcribe`: 接收音频数据并返回转写文本
   - `load_model`: 加载预训练模型（支持多语言，特别是中文）

### 3.3 全局热键管理模块 (hotkey_manager.py)

1. 使用pynput库创建`HotkeyManager`类
2. 实现以下方法：
   - `__init__`: 设置默认热键（Option键）
   - `start_listening`: 开始监听全局热键
   - `stop_listening`: 停止监听
   - `on_press`: 处理Option键按下事件
   - `on_release`: 处理Option键释放事件

### 3.4 剪贴板管理模块 (clipboard_manager.py)

1. 使用pyperclip库创建`ClipboardManager`类
2. 实现以下方法：
   - `copy_to_clipboard`: 将文本复制到剪贴板
   - `paste_to_current_app`: 将剪贴板内容粘贴到当前活动应用

## 4. 用户界面实现 (ui/main_window.py)

1. 使用PyQt6创建`MainWindow`类
2. 设计简单的用户界面，包括：
   - 状态指示器（显示当前是否正在录音）
   - 设置按钮（用于将来的快捷键自定义）
   - 最小化到系统托盘的功能

## 5. 主程序逻辑 (main.py)

1. 创建`Application`类，整合所有模块
2. 实现以下方法：
   - `__init__`: 初始化所有模块
   - `run`: 启动应用程序
   - `on_option_press`: 处理Option键按下事件，开始录音和转写
   - `on_option_release`: 处理Option键释放事件，停止录音，获取转写结果并粘贴

## 6. FunASR 特性优化

1. 利用FunASR的流式识别功能，实现实时转写
2. 配置FunASR以支持离线模式
3. 优化FunASR模型加载和推理速度

## 7. 测试

为每个核心模块编写单元测试，确保功能正确性和稳定性。特别关注FunASR的识别准确性和响应速度。

## 8. 性能优化

1. 使用多线程处理音频捕获和转写，避免UI卡顿
2. 优化内存使用，确保长时间运行时性能稳定

## 9. 错误处理和日志

1. 实现全局异常处理
2. 添加日志系统，记录关键操作和潜在问题

## 10. macOS 特定优化

1. 确保与macOS的兼容性，特别是最新版本
2. 优化全局快捷键监听，确保在不同macOS版本中稳定工作

## 11. 打包和分发

1. 使用PyInstaller将应用打包成macOS可执行文件
2. 创建macOS安装程序（可选）

## 12. 文档和用户指南

1. 编写详细的README文件，包括安装步骤和使用说明
2. 创建用户手册，解释所有功能和设置选项

## 13. 扩展功能实现（可选）

1. 实现用户自定义词典功能
2. 添加自动标点符号功能
3. 开发基本的语音命令功能

按照这个指南，逐步实现各个模块，最终集成成一个完整的macOS应用程序。每个步骤都应该经过充分的测试和验证，确保功能正确和性能优越，特别是在macOS环境下的兼容性和流畅性。