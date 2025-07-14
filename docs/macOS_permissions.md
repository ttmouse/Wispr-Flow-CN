# macOS 权限问题解决指南

## 问题描述

在 macOS 系统上，直接运行 `python src/main.py` 时，快捷键录音功能可能无效，但使用 `bash tools/build_app.sh` 打包后的应用快捷键功能正常。

## 原因分析

macOS 对应用程序的权限管理非常严格，特别是涉及到：
- **辅助功能权限**：监听全局快捷键需要此权限
- **麦克风权限**：录音功能需要此权限

打包后的应用会在 `Info.plist` 中声明所需权限，系统会自动提示用户授权。而直接运行 Python 脚本时，系统将权限检查委托给运行脚本的终端应用。

## 解决方案

### 方案一：使用打包应用（推荐）

```bash
bash tools/build_app.sh
```

打包后的应用会自动处理权限请求，是最简单的解决方案。

### 方案二：为开发环境配置权限

1. **检查当前权限状态：**
   ```bash
   python tools/check_dev_permissions.py
   ```

2. **授予辅助功能权限：**
   - 打开 **系统设置** > **隐私与安全性** > **辅助功能**
   - 点击 **锁图标** 并输入密码解锁
   - 点击 **'+'** 按钮
   - 找到并添加您的开发环境应用
   - 确保应用已勾选

3. **常见开发环境应用路径：**
   - **Terminal.app**: `/System/Applications/Utilities/Terminal.app`
   - **iTerm.app**: `/Applications/iTerm.app`
   - **PyCharm CE**: `/Applications/PyCharm CE.app`
   - **PyCharm Professional**: `/Applications/PyCharm Professional.app`
   - **Visual Studio Code**: `/Applications/Visual Studio Code.app`
   - **Cursor**: `/Applications/Cursor.app`

4. **重启开发环境并重新运行程序**

## 技术细节

### 打包应用的权限配置

打包脚本会创建包含以下权限声明的 `Info.plist`：

```xml
<key>NSMicrophoneUsageDescription</key>
<string>此应用需要访问麦克风以进行语音识别</string>

<key>NSAppleEventsUsageDescription</key>
<string>此应用需要发送 Apple 事件以实现自动化功能</string>

<key>NSAccessibilityUsageDescription</key>
<string>此应用需要辅助功能权限以监听全局快捷键</string>
```

### 开发环境的权限检查

应用启动时会自动检查权限状态：

```python
def _check_development_permissions(self):
    """在开发环境下检查权限"""
    if not self._is_packaged_app():
        # 检查辅助功能权限
        # 检查麦克风权限
        # 提供详细的解决步骤
```

## 常见问题

### Q: 为什么打包应用可以正常工作？
A: 打包应用会在 `Info.plist` 中声明所需权限，macOS 会在首次运行时自动提示用户授权。

### Q: 为什么直接运行 Python 脚本权限不足？
A: Python 脚本通过终端应用运行，权限检查会委托给终端应用。如果终端应用没有相应权限，脚本也无法获得权限。

### Q: 授权后仍然无效怎么办？
A: 
1. 确认已重启开发环境应用
2. 检查是否选择了正确的应用路径
3. 尝试移除后重新添加权限
4. 重启系统（极少数情况）

### Q: 如何确认权限已生效？
A: 运行权限检查脚本：
```bash
python tools/check_dev_permissions.py
```

## 最佳实践

1. **开发阶段**：使用打包应用进行测试，避免权限问题
2. **调试阶段**：如需直接运行脚本，确保开发环境已获得必要权限
3. **发布阶段**：始终使用打包应用，确保用户体验一致

## 相关文件

- `tools/check_dev_permissions.py` - 权限检查工具
- `tools/build_app.sh` - 应用打包脚本
- `run_local.command` - 打包配置脚本
- `src/main.py` - 主程序（包含权限检查逻辑）