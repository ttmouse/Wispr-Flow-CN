
# 代码冗余分析报告
生成时间: 2025-07-22 04:23:12
项目路径: .

## 🎯 主要发现

### 1. 重复函数定义

**发现的重复函数:**
- `__init__` 在 31 个文件中重复:
  - src/audio_capture.py
  - src/audio_threads.py
  - src/audio_threads.py
  - src/state_manager.py
  - src/context_manager.py
  - src/clipboard_manager.py
  - src/audio_manager.py
  - src/hotkey_manager.py
  - src/app_loader.py
  - src/app_loader.py
  - src/global_hotkey.py
  - src/funasr_engine.py
  - src/settings_manager.py
  - src/main.py
  - src/ui/simple_style_config.py
  - src/ui/main_window.py
  - src/ui/menu_manager.py
  - src/ui/clipboard_monitor_window.py
  - src/ui/hotwords_window.py
  - src/ui/hotwords_window.py
  - src/ui/hotwords_window.py
  - src/ui/hotwords_window.py
  - src/ui/hotwords_window.py
  - src/ui/hotwords_window.py
  - src/ui/settings_window.py
  - src/ui/components/modern_list_widget.py
  - src/ui/components/text_label.py
  - src/ui/components/modern_button.py
  - src/ui/components/history_manager.py
  - src/ui/components/history_item.py
  - src/ui/components/history_item.py
- `start_recording` 在 3 个文件中重复:
  - src/audio_capture.py
  - src/state_manager.py
  - src/main.py
- `stop_recording` 在 3 个文件中重复:
  - src/audio_capture.py
  - src/state_manager.py
  - src/main.py
- `cleanup` 在 7 个文件中重复:
  - src/audio_capture.py
  - src/state_manager.py
  - src/audio_manager.py
  - src/hotkey_manager.py
  - src/global_hotkey.py
  - src/funasr_engine.py
  - src/main.py
- `__del__` 在 3 个文件中重复:
  - src/audio_capture.py
  - src/hotkey_manager.py
  - src/funasr_engine.py
- `run` 在 3 个文件中重复:
  - src/audio_threads.py
  - src/audio_threads.py
  - src/main.py
- `update_status` 在 2 个文件中重复:
  - src/state_manager.py
  - src/ui/main_window.py
- `reload_hotwords` 在 2 个文件中重复:
  - src/state_manager.py
  - src/funasr_engine.py
- `set_recording_state` 在 2 个文件中重复:
  - src/context_manager.py
  - src/ui/components/modern_button.py
- `get_status` 在 2 个文件中重复:
  - src/context_manager.py
  - src/hotkey_manager.py
- `on_press` 在 2 个文件中重复:
  - src/hotkey_manager.py
  - src/global_hotkey.py
- `on_release` 在 2 个文件中重复:
  - src/hotkey_manager.py
  - src/global_hotkey.py
- `is_component_ready` 在 2 个文件中重复:
  - src/app_loader.py
  - src/main.py
- `center_on_screen` 在 3 个文件中重复:
  - src/app_loader.py
  - src/ui/main_window.py
  - src/ui/hotwords_window.py
- `get_model_paths` 在 2 个文件中重复:
  - src/funasr_engine.py
  - src/settings_manager.py
- `save_settings` 在 2 个文件中重复:
  - src/settings_manager.py
  - src/ui/settings_window.py
- `clean_html_tags` 在 3 个文件中重复:
  - src/main.py
  - src/ui/main_window.py
  - src/ui/components/history_manager.py
- `quit_application` 在 2 个文件中重复:
  - src/main.py
  - src/ui/main_window.py
- `_show_window_internal` 在 2 个文件中重复:
  - src/main.py
  - src/ui/main_window.py
- `check_permissions` 在 2 个文件中重复:
  - src/main.py
  - src/ui/menu_manager.py
- `setup_ui` 在 3 个文件中重复:
  - src/ui/main_window.py
  - src/ui/clipboard_monitor_window.py
  - src/ui/hotwords_window.py
- `setup_shortcuts` 在 2 个文件中重复:
  - src/ui/main_window.py
  - src/ui/clipboard_monitor_window.py
- `eventFilter` 在 2 个文件中重复:
  - src/ui/main_window.py
  - src/ui/components/modern_button.py
- `mouseReleaseEvent` 在 4 个文件中重复:
  - src/ui/main_window.py
  - src/ui/clipboard_monitor_window.py
  - src/ui/hotwords_window.py
  - src/ui/components/modern_list_widget.py
- `set_state_manager` 在 2 个文件中重复:
  - src/ui/main_window.py
  - src/ui/components/history_manager.py
- `closeEvent` 在 3 个文件中重复:
  - src/ui/main_window.py
  - src/ui/clipboard_monitor_window.py
  - src/ui/settings_window.py
- `save_history` 在 2 个文件中重复:
  - src/ui/main_window.py
  - src/ui/components/history_manager.py
- `load_history` 在 2 个文件中重复:
  - src/ui/main_window.py
  - src/ui/components/history_manager.py
- `mousePressEvent` 在 4 个文件中重复:
  - src/ui/clipboard_monitor_window.py
  - src/ui/hotwords_window.py
  - src/ui/hotwords_window.py
  - src/ui/components/modern_list_widget.py
- `mouseMoveEvent` 在 2 个文件中重复:
  - src/ui/clipboard_monitor_window.py
  - src/ui/hotwords_window.py
- `_setup_ui` 在 3 个文件中重复:
  - src/ui/hotwords_window.py
  - src/ui/components/modern_list_widget.py
  - src/ui/components/text_label.py
- `showEvent` 在 2 个文件中重复:
  - src/ui/hotwords_window.py
  - src/ui/hotwords_window.py
- `_setup_styles` 在 3 个文件中重复:
  - src/ui/components/modern_list_widget.py
  - src/ui/components/text_label.py
  - src/ui/components/history_item.py
- `setText` 在 2 个文件中重复:
  - src/ui/components/text_label.py
  - src/ui/components/history_item.py
- `sizeHint` 在 2 个文件中重复:
  - src/ui/components/text_label.py
  - src/ui/components/history_item.py
- `refresh_styles` 在 2 个文件中重复:
  - src/ui/components/text_label.py
  - src/ui/components/history_item.py
- `scale_factor` 在 2 个文件中重复:
  - src/ui/components/modern_button.py
  - src/ui/components/modern_button.py
- `getText` 在 2 个文件中重复:
  - src/ui/components/history_item.py
  - src/ui/components/history_item.py

### 2. Cleanup方法分析

**找到 7 个cleanup方法:**
- src/audio_capture.py: 1行
- src/state_manager.py: 1行
- src/audio_manager.py: 1行
- src/hotkey_manager.py: 1行
- src/global_hotkey.py: 1行
- src/funasr_engine.py: 1行
- src/main.py: 1行

### 3. 权限检查逻辑

**check_permissions:** 3 个文件

**accessibility_check:** 4 个文件

**microphone_check:** 6 个文件

**system_events:** 3 个文件

### 4. 导入语句冗余

**高频导入语句:**
- `PyQt6.QtCore`: 15 次
- `os`: 14 次
- `PyQt6.QtWidgets`: 11 次
- `datetime`: 7 次
- `sys`: 7 次
- `time`: 6 次
- `logging`: 6 次
- `PyQt6.QtGui`: 6 次
- `re`: 5 次
- `threading`: 4 次

### 5. 异常处理模式
- **generic_except:** 5 个文件
- **broad_exception:** 1 个文件
- **try_except_pass:** 4 个文件
- **exception_logging:** 20 个文件

### 6. 硬编码值统计
- **app_names:** 18 个
- **error_messages:** 206 个


## 🚀 优化建议

### 1. 重复函数优化

**优先级：高**
- 创建 `src/utils/text_utils.py` 统一管理文本处理函数
- 将 `clean_html_tags` 函数移动到工具模块
- 更新所有引用该函数的文件

### 2. 资源清理优化

**优先级：中**
- 创建基础清理接口 `CleanupMixin`
- 统一清理方法的实现模式
- 添加清理状态跟踪

### 3. 权限检查优化

**优先级：中**
- 创建 `src/utils/permission_utils.py` 统一权限检查
- 实现权限状态缓存机制
- 统一权限错误处理

