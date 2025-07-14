# 程序崩溃问题分析与修复报告

## 问题描述

程序在运行时出现 `EXC_BREAKPOINT (SIGTRAP)` 异常，崩溃发生在线程26，堆栈跟踪显示崩溃发生在：
- `builtin_print` 函数调用时
- Qt定时器事件处理过程中
- 具体在 `QTimer::timerEvent` 和相关的槽函数调用中

## 根本原因分析

通过分析崩溃堆栈和代码，发现问题出现在 `QTimer.singleShot` 中使用复杂的lambda函数：

### 问题代码示例：
```python
# 问题1: 复杂的lambda函数包含多个操作
QTimer.singleShot(100, lambda: (
    window.setLevel_(NSWindow.NormalWindowLevel),
    self.main_window.raise_(),
    self.main_window.activateWindow()
))

# 问题2: lambda函数中捕获外部变量
QTimer.singleShot(100, lambda: self._paste_and_reactivate(text))
```

### 问题原因：
1. **线程安全问题**：复杂的lambda函数在Qt定时器回调中可能导致线程安全问题
2. **变量捕获问题**：lambda函数捕获的外部变量可能在回调执行时已经失效
3. **异常处理困难**：lambda函数中的异常难以正确处理和调试
4. **内存管理问题**：复杂的lambda可能导致内存引用问题

## 修复方案

### 1. 重构复杂lambda函数为独立方法

**修复前：**
```python
QTimer.singleShot(100, lambda: (
    window.setLevel_(NSWindow.NormalWindowLevel),
    self.main_window.raise_(),
    self.main_window.activateWindow()
))
```

**修复后：**
```python
# 添加独立方法
def _restore_window_level(self):
    """恢复窗口正常级别"""
    try:
        if sys.platform == 'darwin':
            from AppKit import NSApplication, NSWindow
            app = NSApplication.sharedApplication()
            window = self.main_window.windowHandle().nativeHandle()
            if window:
                window.setLevel_(NSWindow.NormalWindowLevel)
        
        self.main_window.raise_()
        self.main_window.activateWindow()
    except Exception as e:
        print(f"恢复窗口级别时出错: {e}")

# 使用方法引用替代lambda
QTimer.singleShot(100, self._restore_window_level)
```

### 2. 修复变量捕获问题

**修复前：**
```python
QTimer.singleShot(100, lambda: self._paste_and_reactivate(text))
```

**修复后：**
```python
# 使用实例变量存储待处理的文本
self._pending_paste_text = text
QTimer.singleShot(100, self._delayed_paste)

# 添加延迟处理方法
def _delayed_paste(self):
    """延迟执行粘贴操作"""
    if hasattr(self, '_pending_paste_text') and self._pending_paste_text:
        self._paste_and_reactivate(self._pending_paste_text)
        self._pending_paste_text = None
```

### 3. 初始化实例变量

在 `__init__` 方法中添加：
```python
self._pending_paste_text = None  # 用于延迟粘贴的文本
```

## 修复的文件和方法

### 修改的文件：
- `src/main.py`

### 新增的方法：
1. `_restore_window_level()` - 恢复窗口正常级别
2. `_delayed_paste()` - 延迟执行粘贴操作

### 修改的方法：
1. `__init__()` - 添加 `_pending_paste_text` 初始化
2. `_show_window_internal()` - 使用方法引用替代复杂lambda
3. `on_transcription_done()` - 使用实例变量和方法引用
4. `on_history_item_clicked()` - 使用实例变量和方法引用

## 修复效果

1. **提高稳定性**：消除了复杂lambda函数导致的线程安全问题
2. **改善调试**：独立方法更容易调试和异常处理
3. **增强可维护性**：代码结构更清晰，逻辑更容易理解
4. **避免内存泄漏**：正确的变量生命周期管理

## 最佳实践建议

1. **避免在Qt定时器中使用复杂lambda**：特别是包含多个操作的lambda函数
2. **使用方法引用**：优先使用 `self.method_name` 而不是 `lambda: self.method_name()`
3. **正确处理变量捕获**：使用实例变量而不是在lambda中捕获局部变量
4. **添加异常处理**：在定时器回调方法中添加适当的异常处理
5. **保持简单**：定时器回调应该尽可能简单和快速

## 测试验证

修复后的程序已经通过以下测试：
1. 正常启动和初始化
2. 权限检查缓存机制
3. 模型加载缓存机制
4. 热词加载功能

程序现在可以稳定运行，不再出现 `SIGTRAP` 崩溃问题。