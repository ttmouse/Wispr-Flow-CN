# 样式配置功能使用说明

## 概述

本应用现在支持通过配置文件自定义界面样式，包括颜色、字体、间距和布局等参数。您可以通过可视化的样式编辑器轻松调整这些参数。

## 功能特性

### 1. 配置文件管理
- **配置文件位置**: `styles_config.json`
- **自动备份**: 修改前会自动备份原配置
- **实时生效**: 配置修改后立即生效，无需重启应用

### 2. 可配置的样式参数

#### 颜色配置
- 背景色 (background)
- 文字色 (text)
- 边框色 (border)
- 悬停色 (hover)
- 选中色 (selected)
- 滚动条色 (scrollbar)
- 滚动条悬停色 (scrollbar_hover)
- 分隔线色 (separator)

#### 字体配置
- 字体族 (family): 支持系统字体
- 字体大小 (size): 8-72px
- 字体粗细 (weight): normal, bold 等

#### 间距配置
- 列表项内边距 (list_item_padding)
- 列表间距 (list_spacing)
- 文本内边距 (text_padding)
- 文本外边距 (text_margin)
- 行高 (line_height)
- 行间距倍数 (line_spacing_multiplier)

#### 布局配置
- 历史项边距 (left, top, right, bottom)
- 最小项目高度 (min_item_height)
- 最小文本宽度 (min_text_width)
- 滚动条宽度 (scrollbar_width)
- 滚动条圆角 (scrollbar_radius)
- 最小滚动条高度 (min_handle_height)
- 文本宽度边距 (text_width_margin)

## 使用方法

### 1. 打开样式编辑器
- 点击主窗口标题栏右侧的齿轮图标 (⚙)
- 或使用快捷键 `Ctrl+,` (macOS: `Cmd+,`)

### 2. 调整样式参数
1. **颜色调整**: 在"颜色"标签页中，点击"选择"按钮打开颜色选择器
2. **字体调整**: 在"字体"标签页中，修改字体族、大小和粗细
3. **间距调整**: 在"间距"标签页中，使用数值输入框调整各种间距
4. **布局调整**: 在"布局"标签页中，调整边距和尺寸参数

### 3. 预览和保存
- **预览**: 点击"预览"按钮查看效果，不满意可以继续调整
- **重置**: 点击"重置"按钮恢复到打开编辑器时的状态
- **保存**: 点击"保存"按钮保存配置并关闭编辑器
- **取消**: 点击"取消"按钮放弃所有修改

## 配置文件结构

```json
{
  "colors": {
    "background": "#ffffff",
    "text": "#333333",
    "border": "#e0e0e0",
    "hover": "#f5f5f5",
    "selected": "#007acc",
    "scrollbar": "#cccccc",
    "scrollbar_hover": "#999999",
    "separator": "#e0e0e0"
  },
  "fonts": {
    "family": "PingFang SC, Microsoft YaHei, sans-serif",
    "size": 14,
    "weight": "normal"
  },
  "spacing": {
    "list_item_padding": 8,
    "list_spacing": 0,
    "text_padding": 8,
    "text_margin": 4,
    "line_height": 1.4,
    "line_spacing_multiplier": 1.3
  },
  "layout": {
    "history_item_margins": {
      "left": 8,
      "top": 4,
      "right": 8,
      "bottom": 4
    },
    "min_item_height": 60,
    "min_text_width": 200,
    "scrollbar_width": 8,
    "scrollbar_radius": 4,
    "min_handle_height": 20,
    "text_width_margin": 40
  }
}
```

## 高级用法

### 1. 手动编辑配置文件
您也可以直接编辑 `styles_config.json` 文件来批量修改配置。修改后重启应用即可生效。

### 2. 备份和恢复
- 配置文件会在每次修改前自动备份
- 如需恢复，可以从备份文件中复制内容

### 3. 主题切换
您可以创建多个配置文件来实现主题切换：
1. 保存当前配置为 `theme_light.json`
2. 创建深色主题配置为 `theme_dark.json`
3. 需要切换时，复制对应主题文件内容到 `styles_config.json`

## 注意事项

1. **颜色格式**: 支持十六进制颜色代码 (如 #ffffff) 和颜色名称 (如 white)
2. **字体兼容性**: 请确保使用的字体在系统中已安装
3. **数值范围**: 请在合理范围内设置数值，避免界面显示异常
4. **备份重要**: 在大幅修改前建议手动备份配置文件

## 故障排除

### 配置不生效
1. 检查配置文件格式是否正确 (有效的JSON)
2. 重启应用程序
3. 检查控制台是否有错误信息

### 界面显示异常
1. 点击"重置"按钮恢复默认设置
2. 检查数值是否在合理范围内
3. 删除配置文件让应用使用默认配置

### 样式编辑器无法打开
1. 检查是否有权限访问配置文件
2. 查看控制台错误信息
3. 重启应用程序

---

通过这个样式配置系统，您可以轻松定制应用的外观，创造出符合个人喜好的界面风格。如有问题，请查看控制台输出或联系技术支持。