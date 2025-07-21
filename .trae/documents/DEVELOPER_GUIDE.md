# Wispr Flow CN 开发者指南

## 1. 快速开始

### 1.1 环境准备

**系统要求**:
- macOS 10.14+
- Python 3.8+
- Xcode Command Line Tools
- 至少 8GB RAM
- 5GB 可用存储空间

**开发工具推荐**:
- **IDE**: PyCharm Professional / VS Code
- **版本控制**: Git
- **包管理**: pip / conda
- **调试工具**: PyQt6 Designer
- **性能分析**: py-spy, memory_profiler

### 1.2 项目设置

```bash
# 1. 克隆项目
git clone <repository-url>
cd ASR-FunASR

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # macOS/Linux

# 3. 安装依赖
pip install -r requirements.txt

# 4. 安装开发依赖
pip install -r requirements-dev.txt

# 5. 设置环境变量
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# 6. 运行应用
python src/main.py
```

### 1.3 开发环境配置

**VS Code 配置** (`.vscode/settings.json`):
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "**/logs": true
    }
}
```

**PyCharm 配置**:
1. 设置 Python 解释器为虚拟环境
2. 配置代码风格为 Black
3. 启用 flake8 代码检查
4. 设置项目根目录为源码根目录

## 2. 代码规范

### 2.1 代码风格

**使用 Black 进行代码格式化**:
```bash
# 格式化所有代码
black src/

# 检查格式
black --check src/
```

**使用 isort 进行导入排序**:
```bash
# 排序导入
isort src/

# 检查导入顺序
isort --check-only src/
```

**代码风格要求**:
- 行长度限制: 88 字符 (Black 默认)
- 使用 4 个空格缩进
- 函数和类之间空 2 行
- 导入顺序: 标准库 → 第三方库 → 本地模块

### 2.2 命名规范

```python
# 类名: PascalCase
class AudioCaptureManager:
    pass

# 函数和变量: snake_case
def start_recording():
    audio_data = None

# 常量: UPPER_SNAKE_CASE
MAX_RECORDING_DURATION = 300

# 私有成员: 前缀下划线
class MyClass:
    def __init__(self):
        self._private_var = None
        self.__very_private = None

# 文件名: snake_case
# audio_capture.py, hotkey_manager.py
```

### 2.3 文档字符串

```python
def transcribe_audio(audio_data: bytes, model_name: str = "default") -> str:
    """
    将音频数据转换为文字。
    
    Args:
        audio_data: 音频数据字节流
        model_name: 使用的模型名称，默认为 "default"
    
    Returns:
        转录的文字结果
    
    Raises:
        AudioError: 音频数据无效时抛出
        ModelError: 模型加载失败时抛出
    
    Example:
        >>> audio_data = capture_audio()
        >>> text = transcribe_audio(audio_data, "paraformer-zh")
        >>> print(text)
        "你好世界"
    """
    pass
```

## 3. 开发工作流

### 3.1 分支管理

```bash
# 主分支
main          # 生产环境代码
develop       # 开发环境代码

# 功能分支
feature/audio-optimization     # 音频优化功能
feature/ui-redesign           # UI 重设计
hotfix/memory-leak            # 内存泄漏修复

# 分支命名规范
feature/<功能描述>
bugfix/<问题描述>
hotfix/<紧急修复>
refactor/<重构描述>
```

### 3.2 提交规范

```bash
# 提交消息格式
<type>(<scope>): <description>

[optional body]

[optional footer]

# 类型说明
feat:     新功能
fix:      错误修复
docs:     文档更新
style:    代码格式调整
refactor: 代码重构
test:     测试相关
chore:    构建过程或辅助工具变动

# 示例
feat(audio): 添加噪声抑制功能
fix(hotkey): 修复 macOS 权限检查问题
docs(readme): 更新安装说明
```

### 3.3 代码审查

**审查清单**:
- [ ] 代码风格符合规范
- [ ] 函数和类有适当的文档字符串
- [ ] 错误处理完善
- [ ] 性能考虑合理
- [ ] 测试覆盖充分
- [ ] 无明显的安全问题
- [ ] 向后兼容性

## 4. 测试指南

### 4.1 测试结构

```
tests/
├── unit/                    # 单元测试
│   ├── test_audio_capture.py
│   ├── test_funasr_engine.py
│   └── test_hotkey_manager.py
├── integration/             # 集成测试
│   ├── test_recording_flow.py
│   └── test_settings_sync.py
├── ui/                      # UI 测试
│   ├── test_main_window.py
│   └── test_settings_window.py
├── fixtures/                # 测试数据
│   ├── audio_samples/
│   └── config_files/
└── conftest.py             # pytest 配置
```

### 4.2 单元测试示例

```python
import pytest
from unittest.mock import Mock, patch
from src.audio_capture import AudioCapture

class TestAudioCapture:
    @pytest.fixture
    def audio_capture(self):
        """创建 AudioCapture 实例"""
        return AudioCapture()
    
    def test_start_recording_success(self, audio_capture):
        """测试成功开始录音"""
        with patch('pyaudio.PyAudio') as mock_pyaudio:
            mock_stream = Mock()
            mock_pyaudio.return_value.open.return_value = mock_stream
            
            result = audio_capture.start_recording()
            
            assert result is True
            mock_pyaudio.return_value.open.assert_called_once()
    
    def test_start_recording_device_error(self, audio_capture):
        """测试音频设备错误"""
        with patch('pyaudio.PyAudio') as mock_pyaudio:
            mock_pyaudio.return_value.open.side_effect = Exception("Device not found")
            
            with pytest.raises(AudioDeviceError):
                audio_capture.start_recording()
    
    @pytest.mark.parametrize("sample_rate,expected", [
        (16000, True),
        (44100, True),
        (8000, False),
    ])
    def test_validate_sample_rate(self, audio_capture, sample_rate, expected):
        """测试采样率验证"""
        result = audio_capture.validate_sample_rate(sample_rate)
        assert result == expected
```

### 4.3 集成测试示例

```python
import pytest
from src.main import Application
from PyQt6.QtCore import QTimer

class TestRecordingFlow:
    @pytest.fixture
    def app(self, qtbot):
        """创建应用实例"""
        application = Application()
        qtbot.addWidget(application.main_window)
        return application
    
    def test_complete_recording_flow(self, app, qtbot):
        """测试完整录音流程"""
        # 模拟按下热键
        app.handle_recording_start()
        
        # 等待录音开始
        qtbot.wait(100)
        assert app.state_manager.current_state == "recording"
        
        # 模拟录音数据
        with patch.object(app.audio_capture, 'get_audio_data') as mock_audio:
            mock_audio.return_value = b'fake_audio_data'
            
            # 模拟松开热键
            app.handle_recording_stop()
            
            # 等待处理完成
            qtbot.wait(1000)
            
            # 验证状态变化
            assert app.state_manager.current_state == "idle"
            
            # 验证历史记录
            assert len(app.main_window.history_manager.get_history()) > 0
```

### 4.4 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/unit/test_audio_capture.py

# 运行特定测试方法
pytest tests/unit/test_audio_capture.py::TestAudioCapture::test_start_recording_success

# 生成覆盖率报告
pytest --cov=src --cov-report=html

# 运行性能测试
pytest tests/performance/ --benchmark-only
```

## 5. 调试技巧

### 5.1 日志调试

```python
import logging

# 设置调试级别
logging.getLogger('src.audio_capture').setLevel(logging.DEBUG)
logging.getLogger('src.funasr_engine').setLevel(logging.DEBUG)

# 在代码中添加调试信息
logger = logging.getLogger(__name__)

def start_recording(self):
    logger.debug(f"开始录音，设备: {self.device_name}")
    try:
        # 录音逻辑
        pass
    except Exception as e:
        logger.error(f"录音失败: {e}", exc_info=True)
```

### 5.2 性能分析

```bash
# 使用 py-spy 进行性能分析
py-spy record -o profile.svg -- python src/main.py

# 使用 memory_profiler 分析内存使用
@profile
def memory_intensive_function():
    # 函数实现
    pass

python -m memory_profiler src/main.py
```

### 5.3 UI 调试

```python
# 启用 Qt 调试信息
os.environ['QT_LOGGING_RULES'] = '*.debug=true'

# 使用 Qt Designer 调试 UI
# 在开发模式下启用 UI 检查器
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # 启用 UI 调试
    if '--debug-ui' in sys.argv:
        from dev_inspector import UIInspector
        inspector = UIInspector()
        inspector.inspect_application()
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
```

## 6. 常见问题解决

### 6.1 音频问题

**问题**: 音频设备无法访问
```python
# 检查音频设备权限
def check_audio_permissions():
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        device_count = p.get_device_count()
        p.terminate()
        return device_count > 0
    except Exception as e:
        logger.error(f"音频权限检查失败: {e}")
        return False
```

**问题**: 音频质量差
```python
# 音频预处理
def preprocess_audio(audio_data):
    # 降噪处理
    audio_data = noise_reduction(audio_data)
    
    # 音量归一化
    audio_data = normalize_volume(audio_data)
    
    # 去除静音段
    audio_data = remove_silence(audio_data)
    
    return audio_data
```

### 6.2 热键问题

**问题**: 热键无响应
```python
# 检查辅助功能权限
def check_accessibility_permissions():
    try:
        from Cocoa import NSWorkspace
        from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
        
        # 尝试获取窗口信息来测试权限
        window_list = CGWindowListCopyWindowInfo(
            kCGWindowListOptionOnScreenOnly, 
            kCGNullWindowID
        )
        return len(window_list) > 0
    except Exception:
        return False
```

### 6.3 内存问题

**问题**: 内存泄漏
```python
# 使用弱引用避免循环引用
import weakref

class AudioManager:
    def __init__(self):
        self._callbacks = weakref.WeakSet()
    
    def add_callback(self, callback):
        self._callbacks.add(callback)
    
    def __del__(self):
        # 确保资源清理
        self.cleanup()
```

## 7. 部署和发布

### 7.1 打包配置

**PyInstaller 配置** (`build.spec`):
```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/ui', 'ui'),
        ('iconset.icns', '.'),
        ('resources', 'resources'),
    ],
    hiddenimports=[
        'funasr',
        'modelscope',
        'torch',
        'torchaudio',
    ],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Dou-flow',
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
    codesign_identity=None,
    entitlements_file=None,
    icon='iconset.icns',
)

app = BUNDLE(
    exe,
    name='Dou-flow.app',
    icon='iconset.icns',
    bundle_identifier='com.ttmouse.douflow',
    info_plist={
        'NSMicrophoneUsageDescription': '应用需要访问麦克风进行语音识别',
        'NSAppleEventsUsageDescription': '应用需要发送按键事件进行自动粘贴',
    },
)
```

### 7.2 构建脚本

```bash
#!/bin/bash
# build.sh

set -e

echo "开始构建 Dou-flow..."

# 清理之前的构建
rm -rf build/ dist/

# 运行测试
echo "运行测试..."
pytest tests/ --cov=src --cov-fail-under=80

# 代码质量检查
echo "代码质量检查..."
flake8 src/
black --check src/
isort --check-only src/

# 构建应用
echo "构建应用..."
pyinstaller build.spec

# 代码签名 (可选)
if [ -n "$CODESIGN_IDENTITY" ]; then
    echo "代码签名..."
    codesign --force --deep --sign "$CODESIGN_IDENTITY" dist/Dou-flow.app
fi

# 创建 DMG (可选)
if command -v create-dmg &> /dev/null; then
    echo "创建 DMG..."
    create-dmg \
        --volname "Dou-flow" \
        --window-pos 200 120 \
        --window-size 600 300 \
        --icon-size 100 \
        --icon "Dou-flow.app" 175 120 \
        --hide-extension "Dou-flow.app" \
        --app-drop-link 425 120 \
        "dist/Dou-flow.dmg" \
        "dist/"
fi

echo "构建完成！"
```

### 7.3 持续集成

**GitHub Actions 配置** (`.github/workflows/build.yml`):
```yaml
name: Build and Test

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: macos-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: |
        pytest tests/ --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
    
    - name: Build application
      run: |
        pyinstaller build.spec
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: Dou-flow-${{ github.sha }}
        path: dist/Dou-flow.app
```

## 8. 贡献指南

### 8.1 贡献流程

1. **Fork 项目**
2. **创建功能分支**: `git checkout -b feature/amazing-feature`
3. **提交更改**: `git commit -m 'feat: add amazing feature'`
4. **推送分支**: `git push origin feature/amazing-feature`
5. **创建 Pull Request**

### 8.2 代码审查标准

- 代码风格符合项目规范
- 包含适当的测试
- 文档更新完整
- 性能影响评估
- 向后兼容性考虑

### 8.3 发布流程

1. **版本号更新**: 遵循语义化版本控制
2. **更新日志**: 记录所有变更
3. **测试验证**: 完整的回归测试
4. **标签创建**: `git tag v1.2.0`
5. **发布构建**: 自动化构建和分发

---

*开发指南版本: 1.0*  
*最后更新: 2