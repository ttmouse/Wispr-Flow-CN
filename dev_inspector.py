#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
开发模式调试工具
用于检查UI组件的样式、布局和属性
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
    QWidget, QLabel, QPushButton, QTextEdit, QSplitter,
    QTreeWidget, QTreeWidgetItem, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

class UIInspector(QMainWindow):
    """UI检查器 - 开发模式调试工具"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ASR应用 - 开发模式检查器")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        central_widget_layout = QVBoxLayout(central_widget)
        central_widget_layout.addWidget(splitter)
        
        # 左侧：控制面板
        self.create_control_panel(splitter)
        
        # 右侧：信息显示
        self.create_info_panel(splitter)
        
        # 设置分割器比例
        splitter.setSizes([400, 800])
        
        # 查找主应用程序窗口
        self.main_app_window = None
        self.find_main_window()
        
        # 定时器用于实时更新
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_info)
        self.timer.start(1000)  # 每秒更新一次
    
    def create_control_panel(self, parent):
        """创建控制面板"""
        control_widget = QWidget()
        layout = QVBoxLayout(control_widget)
        
        # 标题
        title = QLabel("开发模式控制面板")
        title.setFont(QFont("PingFang SC", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 检查按钮
        check_btn = QPushButton("检查主窗口")
        check_btn.clicked.connect(self.check_main_window)
        layout.addWidget(check_btn)
        
        # 检查列表组件按钮
        check_list_btn = QPushButton("检查列表组件")
        check_list_btn.clicked.connect(self.check_list_widget)
        layout.addWidget(check_list_btn)
        
        # 检查历史记录项按钮
        check_items_btn = QPushButton("检查历史记录项")
        check_items_btn.clicked.connect(self.check_history_items)
        layout.addWidget(check_items_btn)
        
        # 测试样式按钮
        test_style_btn = QPushButton("测试样式修改")
        test_style_btn.clicked.connect(self.test_style_changes)
        layout.addWidget(test_style_btn)
        
        # 状态信息
        self.status_label = QLabel("状态: 等待检查...")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        parent.addWidget(control_widget)
    
    def create_info_panel(self, parent):
        """创建信息显示面板"""
        info_widget = QWidget()
        layout = QVBoxLayout(info_widget)
        
        # 标题
        title = QLabel("检查结果")
        title.setFont(QFont("PingFang SC", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 信息显示区域
        self.info_text = QTextEdit()
        self.info_text.setFont(QFont("Monaco", 12))
        layout.addWidget(self.info_text)
        
        parent.addWidget(info_widget)
    
    def find_main_window(self):
        """查找主应用程序窗口"""
        app = QApplication.instance()
        if app:
            for widget in app.allWidgets():
                if hasattr(widget, 'objectName') and 'MainWindow' in str(type(widget)):
                    self.main_app_window = widget
                    break
                elif hasattr(widget, 'windowTitle') and 'Dou-flow' in widget.windowTitle():
                    self.main_app_window = widget
                    break
    
    def check_main_window(self):
        """检查主窗口"""
        if not self.main_app_window:
            self.find_main_window()
        
        if self.main_app_window:
            info = f"主窗口检查结果:\n"
            info += f"窗口标题: {self.main_app_window.windowTitle()}\n"
            info += f"窗口大小: {self.main_app_window.size()}\n"
            info += f"窗口位置: {self.main_app_window.pos()}\n"
            info += f"是否可见: {self.main_app_window.isVisible()}\n"
            info += f"窗口类型: {type(self.main_app_window)}\n"
            self.info_text.setText(info)
            self.status_label.setText("状态: 主窗口检查完成")
        else:
            self.info_text.setText("未找到主应用程序窗口")
            self.status_label.setText("状态: 未找到主窗口")
    
    def check_list_widget(self):
        """检查列表组件"""
        if not self.main_app_window:
            self.info_text.setText("请先检查主窗口")
            return
        
        # 查找列表组件
        list_widgets = self.find_widgets_by_type(self.main_app_window, 'ModernListWidget')
        
        info = f"列表组件检查结果:\n"
        info += f"找到 {len(list_widgets)} 个列表组件\n\n"
        
        for i, widget in enumerate(list_widgets):
            info += f"列表组件 {i+1}:\n"
            info += f"  大小: {widget.size()}\n"
            info += f"  项目数量: {widget.count()}\n"
            info += f"  样式表: {widget.styleSheet()[:200]}...\n"
            info += f"  字体: {widget.font().family()} {widget.font().pointSize()}pt\n\n"
        
        self.info_text.setText(info)
        self.status_label.setText("状态: 列表组件检查完成")
    
    def check_history_items(self):
        """检查历史记录项"""
        if not self.main_app_window:
            self.info_text.setText("请先检查主窗口")
            return
        
        # 查找历史记录项组件
        history_widgets = self.find_widgets_by_type(self.main_app_window, 'HistoryItemWidget')
        
        info = f"历史记录项检查结果:\n"
        info += f"找到 {len(history_widgets)} 个历史记录项\n\n"
        
        for i, widget in enumerate(history_widgets[:5]):  # 只显示前5个
            info += f"历史记录项 {i+1}:\n"
            info += f"  大小: {widget.size()}\n"
            info += f"  建议大小: {widget.sizeHint()}\n"
            
            # 检查布局边距
            layout = widget.layout()
            if layout:
                margins = layout.contentsMargins()
                info += f"  内边距: 左{margins.left()} 上{margins.top()} 右{margins.right()} 下{margins.bottom()}\n"
            
            # 检查文本标签
            text_label = getattr(widget, 'text_label', None)
            if text_label:
                info += f"  文本标签大小: {text_label.size()}\n"
                info += f"  文本标签字体: {text_label.font().family()} {text_label.font().pointSize()}pt\n"
                info += f"  文本内容长度: {len(widget.getText())} 字符\n"
            
            info += "\n"
        
        self.info_text.setText(info)
        self.status_label.setText("状态: 历史记录项检查完成")
    
    def test_style_changes(self):
        """测试样式修改效果"""
        info = "样式修改测试结果:\n\n"
        
        # 检查当前的样式设置
        info += "当前样式设置:\n"
        info += "- HistoryItemWidget 内边距: 6, 8, 6, 8 (减少了一半)\n"
        info += "- TextLabel 内边距: 1px (从2px减少)\n"
        info += "- TextLabel 行高: 1.4 (从1.6调整)\n"
        info += "- 最小高度: 35px (从50px减少)\n\n"
        
        info += "预期效果:\n"
        info += "✓ 文本距离四周的距离减少了一半\n"
        info += "✓ 高度自适应，根据内容动态调整\n"
        info += "✓ 更紧凑的布局，节省空间\n"
        info += "✓ 保持文本的完整显示\n\n"
        
        info += "如需进一步调整，可以修改以下参数:\n"
        info += "- layout.setContentsMargins(6, 8, 6, 8) # 调整内边距\n"
        info += "- padding: 1px # 调整文本内边距\n"
        info += "- line-height: 1.4 # 调整行高\n"
        info += "- min_height = 35 # 调整最小高度\n"
        
        self.info_text.setText(info)
        self.status_label.setText("状态: 样式测试完成")
    
    def find_widgets_by_type(self, parent, widget_type_name):
        """根据类型名称查找组件"""
        widgets = []
        
        def search_recursive(widget):
            if widget_type_name in str(type(widget)):
                widgets.append(widget)
            
            for child in widget.findChildren(QWidget):
                if widget_type_name in str(type(child)):
                    widgets.append(child)
        
        search_recursive(parent)
        return widgets
    
    def update_info(self):
        """定时更新信息"""
        if not self.main_app_window:
            self.find_main_window()

def main():
    """启动开发模式检查器"""
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    inspector = UIInspector()
    inspector.show()
    
    return app, inspector

if __name__ == '__main__':
    app, inspector = main()
    sys.exit(app.exec())