# 样式配置编辑器 - 提供可视化界面来调整UI样式
# 支持实时预览和保存配置

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QSpinBox, QDoubleSpinBox, QLineEdit, QPushButton,
    QColorDialog, QGroupBox, QGridLayout, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from .style_config_manager import style_config

class StyleEditor(QDialog):
    """样式配置编辑器
    
    提供可视化界面来调整：
    - 颜色配置
    - 字体配置
    - 间距配置
    - 布局配置
    """
    
    # 样式更新信号
    style_updated = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("样式配置编辑器")
        self.setModal(True)
        self.resize(500, 600)
        
        # 存储当前配置的副本
        self.current_config = style_config.get_all_config()
        
        self._setup_ui()
        self._load_current_values()
    
    def _setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout(self)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # 颜色配置页
        self._create_colors_tab()
        
        # 字体配置页
        self._create_fonts_tab()
        
        # 间距配置页
        self._create_spacing_tab()
        
        # 布局配置页
        self._create_layout_tab()
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.preview_btn = QPushButton("预览")
        self.preview_btn.clicked.connect(self._apply_preview)
        
        self.reset_btn = QPushButton("重置")
        self.reset_btn.clicked.connect(self._reset_values)
        
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self._save_config)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.preview_btn)
        button_layout.addWidget(self.reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _create_colors_tab(self):
        """创建颜色配置页"""
        colors_widget = QWidget()
        layout = QGridLayout(colors_widget)
        
        self.color_inputs = {}
        color_labels = {
            'background': '背景色',
            'text': '文字色',
            'border': '边框色',
            'hover': '悬停色',
            'selected': '选中色',
            'scrollbar': '滚动条色',
            'scrollbar_hover': '滚动条悬停色',
            'separator': '分隔线色'
        }
        
        row = 0
        for key, label in color_labels.items():
            layout.addWidget(QLabel(label + ":"), row, 0)
            
            color_input = QLineEdit()
            color_input.setReadOnly(True)
            self.color_inputs[key] = color_input
            layout.addWidget(color_input, row, 1)
            
            color_btn = QPushButton("选择")
            color_btn.clicked.connect(lambda checked, k=key: self._choose_color(k))
            layout.addWidget(color_btn, row, 2)
            
            row += 1
        
        self.tab_widget.addTab(colors_widget, "颜色")
    
    def _create_fonts_tab(self):
        """创建字体配置页"""
        fonts_widget = QWidget()
        layout = QGridLayout(fonts_widget)
        
        # 字体族
        layout.addWidget(QLabel("字体族:"), 0, 0)
        self.font_family_input = QLineEdit()
        layout.addWidget(self.font_family_input, 0, 1)
        
        # 字体大小
        layout.addWidget(QLabel("字体大小:"), 1, 0)
        self.font_size_input = QSpinBox()
        self.font_size_input.setRange(8, 72)
        layout.addWidget(self.font_size_input, 1, 1)
        
        # 字体粗细
        layout.addWidget(QLabel("字体粗细:"), 2, 0)
        self.font_weight_input = QLineEdit()
        layout.addWidget(self.font_weight_input, 2, 1)
        
        self.tab_widget.addTab(fonts_widget, "字体")
    
    def _create_spacing_tab(self):
        """创建间距配置页"""
        spacing_widget = QWidget()
        layout = QGridLayout(spacing_widget)
        
        self.spacing_inputs = {}
        spacing_labels = {
            'list_item_padding': '列表项内边距',
            'list_spacing': '列表间距',
            'text_padding': '文本内边距',
            'text_margin': '文本外边距',
            'line_height': '行高',
            'line_spacing_multiplier': '行间距倍数'
        }
        
        row = 0
        for key, label in spacing_labels.items():
            layout.addWidget(QLabel(label + ":"), row, 0)
            
            if key in ['line_height', 'line_spacing_multiplier']:
                input_widget = QDoubleSpinBox()
                input_widget.setRange(0.1, 5.0)
                input_widget.setSingleStep(0.1)
                input_widget.setDecimals(1)
            else:
                input_widget = QSpinBox()
                input_widget.setRange(0, 100)
            
            self.spacing_inputs[key] = input_widget
            layout.addWidget(input_widget, row, 1)
            
            row += 1
        
        self.tab_widget.addTab(spacing_widget, "间距")
    
    def _create_layout_tab(self):
        """创建布局配置页"""
        layout_widget = QWidget()
        main_layout = QVBoxLayout(layout_widget)
        
        # 历史项边距组
        margins_group = QGroupBox("历史项边距")
        margins_layout = QGridLayout(margins_group)
        
        self.margin_inputs = {}
        margin_labels = {
            'left': '左边距',
            'top': '上边距',
            'right': '右边距',
            'bottom': '下边距'
        }
        
        row = 0
        for key, label in margin_labels.items():
            margins_layout.addWidget(QLabel(label + ":"), row, 0)
            
            input_widget = QSpinBox()
            input_widget.setRange(0, 50)
            self.margin_inputs[key] = input_widget
            margins_layout.addWidget(input_widget, row, 1)
            
            row += 1
        
        main_layout.addWidget(margins_group)
        
        # 其他布局参数
        other_layout = QGridLayout()
        
        self.layout_inputs = {}
        layout_labels = {
            'min_item_height': '最小项目高度',
            'min_text_width': '最小文本宽度',
            'scrollbar_width': '滚动条宽度',
            'scrollbar_radius': '滚动条圆角',
            'min_handle_height': '最小滚动条高度',
            'text_width_margin': '文本宽度边距'
        }
        
        row = 0
        for key, label in layout_labels.items():
            other_layout.addWidget(QLabel(label + ":"), row, 0)
            
            input_widget = QSpinBox()
            input_widget.setRange(1, 1000)
            self.layout_inputs[key] = input_widget
            other_layout.addWidget(input_widget, row, 1)
            
            row += 1
        
        other_widget = QWidget()
        other_widget.setLayout(other_layout)
        main_layout.addWidget(other_widget)
        
        self.tab_widget.addTab(layout_widget, "布局")
    
    def _load_current_values(self):
        """加载当前配置值"""
        # 加载颜色
        for key, input_widget in self.color_inputs.items():
            color = style_config.get_color(key)
            input_widget.setText(color)
            input_widget.setStyleSheet(f"background-color: {color};")
        
        # 加载字体
        self.font_family_input.setText(style_config.get_font_family())
        self.font_size_input.setValue(style_config.get_font_size())
        self.font_weight_input.setText(style_config.get_font_weight())
        
        # 加载间距
        for key, input_widget in self.spacing_inputs.items():
            value = style_config.get_spacing(key)
            input_widget.setValue(value)
        
        # 加载边距
        margins = style_config.get_history_item_margins()
        for key, input_widget in self.margin_inputs.items():
            value = margins.get(key, 0)
            input_widget.setValue(value)
        
        # 加载其他布局参数
        for key, input_widget in self.layout_inputs.items():
            value = style_config.get_layout(key)
            input_widget.setValue(value)
    
    def _choose_color(self, color_key):
        """选择颜色"""
        current_color = self.color_inputs[color_key].text()
        color = QColorDialog.getColor(QColor(current_color), self)
        
        if color.isValid():
            color_name = color.name()
            self.color_inputs[color_key].setText(color_name)
            self.color_inputs[color_key].setStyleSheet(f"background-color: {color_name};")
    
    def _apply_preview(self):
        """应用预览"""
        # 收集当前输入的配置
        new_config = self._collect_config()
        
        # 更新配置
        style_config.update_config(new_config)
        
        # 发送更新信号
        self.style_updated.emit()
        
        QMessageBox.information(self, "预览", "样式已更新，请查看效果")
    
    def _reset_values(self):
        """重置为原始值"""
        # 恢复原始配置
        style_config.update_config(self.current_config)
        
        # 重新加载界面值
        self._load_current_values()
        
        # 发送更新信号
        self.style_updated.emit()
    
    def _save_config(self):
        """保存配置"""
        # 收集配置
        new_config = self._collect_config()
        
        # 更新并保存
        style_config.update_config(new_config)
        style_config.save_config()
        
        # 发送更新信号
        self.style_updated.emit()
        
        QMessageBox.information(self, "保存", "样式配置已保存")
        self.accept()
    
    def _collect_config(self):
        """收集当前输入的配置"""
        config = {
            'colors': {},
            'fonts': {},
            'spacing': {},
            'layout': {
                'history_item_margins': {}
            }
        }
        
        # 收集颜色
        for key, input_widget in self.color_inputs.items():
            config['colors'][key] = input_widget.text()
        
        # 收集字体
        config['fonts']['family'] = self.font_family_input.text()
        config['fonts']['size'] = self.font_size_input.value()
        config['fonts']['weight'] = self.font_weight_input.text()
        
        # 收集间距
        for key, input_widget in self.spacing_inputs.items():
            config['spacing'][key] = input_widget.value()
        
        # 收集边距
        for key, input_widget in self.margin_inputs.items():
            config['layout']['history_item_margins'][key] = input_widget.value()
        
        # 收集其他布局参数
        for key, input_widget in self.layout_inputs.items():
            config['layout'][key] = input_widget.value()
        
        return config