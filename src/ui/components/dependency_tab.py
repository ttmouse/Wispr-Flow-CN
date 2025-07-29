#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖管理标签页组件
提供依赖检测、安装和管理的用户界面
"""

import logging
from typing import Dict, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGroupBox, QScrollArea, QProgressBar, QTextEdit, QMessageBox,
    QFrame, QSizePolicy, QSpacerItem, QDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor

try:
    from ...dependency_manager import DependencyManager, DependencyStatus, DependencyInfo
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from dependency_manager import DependencyManager, DependencyStatus, DependencyInfo

class DependencyCheckThread(QThread):
    """依赖检查线程"""
    check_completed = pyqtSignal(dict)
    check_progress = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.dependency_manager = DependencyManager()
    
    def run(self):
        """执行依赖检查"""
        try:
            print("DependencyCheckThread: 开始执行依赖检查")
            self.check_progress.emit("正在检查依赖项...")
            dependencies = self.dependency_manager.check_all_dependencies()
            print(f"DependencyCheckThread: 检查完成，找到 {len(dependencies)} 个依赖项")
            self.check_completed.emit(dependencies)
        except Exception as e:
            print(f"DependencyCheckThread: 检查失败 - {e}")
            logging.error(f"依赖检查失败: {e}")
            self.check_completed.emit({})

class DependencyInstallThread(QThread):
    """依赖安装线程"""
    install_completed = pyqtSignal(str, bool, str)
    install_progress = pyqtSignal(str)
    
    def __init__(self, dependency_name: str, dependency_manager: DependencyManager):
        super().__init__()
        self.dependency_name = dependency_name
        self.dependency_manager = dependency_manager
    
    def run(self):
        """执行依赖安装"""
        try:
            self.install_progress.emit(f"正在安装 {self.dependency_name}...")
            success, message = self.dependency_manager.install_dependency(self.dependency_name)
            self.install_completed.emit(self.dependency_name, success, message)
        except Exception as e:
            logging.error(f"安装{self.dependency_name}失败: {e}")
            self.install_completed.emit(self.dependency_name, False, str(e))

class DependencyCard(QFrame):
    """依赖项卡片组件"""
    install_requested = pyqtSignal(str)
    
    def __init__(self, dep_name: str, dep_info: DependencyInfo):
        super().__init__()
        self.dep_name = dep_name
        self.dep_info = dep_info
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(1)
        self.setContentsMargins(10, 10, 10, 10)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 标题行
        title_layout = QHBoxLayout()
        
        # 状态图标和名称
        status_label = QLabel(self._get_status_icon())
        status_label.setFont(QFont("Arial", 16))
        title_layout.addWidget(status_label)
        
        name_label = QLabel(self.dep_info.name)
        name_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_layout.addWidget(name_label)
        
        title_layout.addStretch()
        
        # 安装按钮
        if self.dep_info.status != DependencyStatus.INSTALLED:
            self.install_btn = QPushButton("安装")
            self.install_btn.clicked.connect(lambda: self.install_requested.emit(self.dep_name))
            self.install_btn.setMaximumWidth(80)
            title_layout.addWidget(self.install_btn)
        
        layout.addLayout(title_layout)
        
        # 描述
        desc_label = QLabel(self.dep_info.description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(desc_label)
        
        # 状态信息
        status_text = self._get_status_text()
        if status_text:
            status_info = QLabel(status_text)
            status_info.setWordWrap(True)
            status_info.setStyleSheet(self._get_status_style())
            layout.addWidget(status_info)
        
        # 设置卡片样式
        self._apply_card_style()
    
    def _get_status_icon(self) -> str:
        """获取状态图标"""
        if self.dep_info.status == DependencyStatus.INSTALLED:
            return "✅"
        elif self.dep_info.status == DependencyStatus.NOT_INSTALLED:
            return "❌"
        elif self.dep_info.status == DependencyStatus.VERSION_MISMATCH:
            return "⚠️"
        elif self.dep_info.status == DependencyStatus.CORRUPTED:
            return "🔧"
        else:
            return "❓"
    
    def _get_status_text(self) -> str:
        """获取状态文本"""
        texts = []
        
        if self.dep_info.version:
            texts.append(f"版本: {self.dep_info.version}")
        
        if self.dep_info.error_message:
            texts.append(f"错误: {self.dep_info.error_message}")
        
        return " | ".join(texts)
    
    def _get_status_style(self) -> str:
        """获取状态样式"""
        if self.dep_info.status == DependencyStatus.INSTALLED:
            return "color: #4CAF50; font-size: 11px;"
        elif self.dep_info.status == DependencyStatus.NOT_INSTALLED:
            return "color: #F44336; font-size: 11px;"
        elif self.dep_info.status == DependencyStatus.VERSION_MISMATCH:
            return "color: #FF9800; font-size: 11px;"
        else:
            return "color: #FFFFFF; font-size: 11px;"
    
    def _apply_card_style(self):
        """应用卡片样式"""
        if self.dep_info.status == DependencyStatus.INSTALLED:
            self.setStyleSheet("""
                QFrame {
                    background-color: rgba(255, 255, 255, 0.03);
                    border: none;
                    border-radius: 4px;
                    color: #FFFFFF;
                    padding: 8px;
                }
                QLabel {
                    color: #FFFFFF;
                }
            """)
        elif self.dep_info.status == DependencyStatus.NOT_INSTALLED:
            self.setStyleSheet("""
                QFrame {
                    background-color: rgba(128, 128, 128, 0.03);
                    border: none;
                    border-radius: 4px;
                    color: #FFFFFF;
                    padding: 8px;
                }
                QLabel {
                    color: #CCCCCC;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: rgba(192, 192, 192, 0.03);
                    border: none;
                    border-radius: 4px;
                    color: #FFFFFF;
                    padding: 8px;
                }
                QLabel {
                    color: #DDDDDD;
                }
            """)
    
    def update_dependency_info(self, dep_info: DependencyInfo):
        """更新依赖信息"""
        self.dep_info = dep_info
        # 重新创建UI
        self._clear_layout()
        self._setup_ui()
    
    def _clear_layout(self):
        """清空布局"""
        layout = self.layout()
        if layout:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

class DependencyReportDialog(QDialog):
    """依赖报告对话框"""
    
    def __init__(self, report_text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("依赖检查报告")
        self.setMinimumSize(600, 400)
        self._setup_ui(report_text)
    
    def _setup_ui(self, report_text: str):
        """设置UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 报告文本
        text_edit = QTextEdit()
        text_edit.setPlainText(report_text)
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont("Consolas", 10))
        layout.addWidget(text_edit)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        export_btn = QPushButton("导出报告")
        export_btn.clicked.connect(lambda: self._export_report(report_text))
        button_layout.addWidget(export_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _export_report(self, report_text: str):
        """导出报告"""
        from PyQt6.QtWidgets import QFileDialog
        from datetime import datetime
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "保存依赖报告",
            f"dependency_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            "Markdown文件 (*.md);;文本文件 (*.txt)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report_text)
                QMessageBox.information(self, "成功", f"报告已保存到: {filename}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存报告失败: {e}")

class DependencyTab(QWidget):
    """依赖管理标签页"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        print("DependencyTab: 初始化开始")
        self.dependency_manager = DependencyManager()
        self.dependencies = {}
        self.dependency_cards = {}
        self.check_thread = None
        self.install_thread = None
        self._setup_ui()
        
        # 自动检查依赖
        print("DependencyTab: 设置500ms后自动检查依赖")
        QTimer.singleShot(500, self._check_dependencies)
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 标题和操作按钮
        header_layout = QHBoxLayout()
        
        title_label = QLabel("依赖管理")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新检查")
        refresh_btn.clicked.connect(self._check_dependencies)
        header_layout.addWidget(refresh_btn)
        
        # 一键安装按钮
        self.install_all_btn = QPushButton("一键安装全部")
        self.install_all_btn.clicked.connect(self._install_all_missing)
        self.install_all_btn.setEnabled(False)
        header_layout.addWidget(self.install_all_btn)
        
        # 查看报告按钮
        report_btn = QPushButton("查看报告")
        report_btn.clicked.connect(self._show_report)
        header_layout.addWidget(report_btn)
        
        layout.addLayout(header_layout)
        
        # 状态摘要
        self.summary_label = QLabel("正在检查依赖项...")
        self.summary_label.setStyleSheet("color: #FFFFFF; font-size: 12px; padding: 10px;")
        layout.addWidget(self.summary_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #FFFFFF; font-size: 11px; padding: 5px;")
        layout.addWidget(self.status_label)
        
        # 依赖项列表（滚动区域）
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.dependencies_widget = QWidget()
        self.dependencies_layout = QVBoxLayout()
        self.dependencies_widget.setLayout(self.dependencies_layout)
        
        scroll_area.setWidget(self.dependencies_widget)
        layout.addWidget(scroll_area)
    
    def _check_dependencies(self):
        """检查依赖项"""
        print("DependencyTab: _check_dependencies 方法被调用")
        if self.check_thread and self.check_thread.isRunning():
            print("DependencyTab: 检查线程正在运行，跳过")
            return
        
        print("DependencyTab: 开始启动依赖检查线程")
        self.summary_label.setText("正在检查依赖项...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 无限进度条
        
        self.check_thread = DependencyCheckThread()
        self.check_thread.check_completed.connect(self._on_check_completed)
        self.check_thread.check_progress.connect(self._on_check_progress)
        self.check_thread.start()
        print("DependencyTab: 依赖检查线程已启动")
    
    def _on_check_completed(self, dependencies: Dict[str, DependencyInfo]):
        """检查完成回调"""
        self.dependencies = dependencies
        self.progress_bar.setVisible(False)
        self.status_label.setText("")
        
        # 手动计算摘要以确保使用最新的依赖状态
        summary = {
            'total': len(dependencies),
            'installed': 0,
            'not_installed': 0,
            'issues': 0
        }
        
        for dep in dependencies.values():
            if dep.status == DependencyStatus.INSTALLED:
                summary['installed'] += 1
            elif dep.status == DependencyStatus.NOT_INSTALLED:
                summary['not_installed'] += 1
            elif dep.status in [DependencyStatus.VERSION_MISMATCH, DependencyStatus.CORRUPTED]:
                summary['issues'] += 1
            # UNKNOWN状态的依赖不计入任何类别
        
        summary_text = f"总计: {summary['total']} | 已安装: {summary['installed']} | 未安装: {summary['not_installed']} | 有问题: {summary['issues']}"
        self.summary_label.setText(summary_text)
        
        # 调试输出
        print(f"依赖检查完成，状态统计: {summary}")
        for dep_name, dep_info in dependencies.items():
            print(f"{dep_name}: {dep_info.status} (枚举值: {dep_info.status.value})")
        
        # 更新依赖卡片
        self._update_dependency_cards()
        
        # 更新一键安装按钮状态
        has_missing = summary['not_installed'] > 0 or summary['issues'] > 0
        self.install_all_btn.setEnabled(has_missing)
    
    def _on_check_progress(self, message: str):
        """检查进度回调"""
        self.status_label.setText(message)
    
    def _update_dependency_cards(self):
        """更新依赖卡片"""
        # 清空现有卡片
        for card in self.dependency_cards.values():
            card.deleteLater()
        self.dependency_cards.clear()
        
        # 创建新卡片
        for dep_name, dep_info in self.dependencies.items():
            card = DependencyCard(dep_name, dep_info)
            card.install_requested.connect(self._install_dependency)
            self.dependency_cards[dep_name] = card
            self.dependencies_layout.addWidget(card)
        
        # 添加弹性空间
        self.dependencies_layout.addStretch()
    
    def _install_dependency(self, dep_name: str):
        """安装单个依赖"""
        if self.install_thread and self.install_thread.isRunning():
            QMessageBox.warning(self, "警告", "已有安装任务在进行中，请稍候...")
            return
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        self.install_thread = DependencyInstallThread(dep_name, self.dependency_manager)
        self.install_thread.install_completed.connect(self._on_install_completed)
        self.install_thread.install_progress.connect(self._on_install_progress)
        self.install_thread.start()
    
    def _install_all_missing(self):
        """安装所有缺失的依赖"""
        missing_deps = []
        for dep_name, dep_info in self.dependencies.items():
            if dep_info.status != DependencyStatus.INSTALLED:
                missing_deps.append(dep_name)
        
        if not missing_deps:
            QMessageBox.information(self, "信息", "所有依赖项都已安装")
            return
        
        reply = QMessageBox.question(
            self, "确认", 
            f"将安装以下依赖项:\n{', '.join(missing_deps)}\n\n是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 这里可以实现批量安装逻辑
            QMessageBox.information(self, "提示", "批量安装功能待实现，请逐个安装")
    
    def _on_install_completed(self, dep_name: str, success: bool, message: str):
        """安装完成回调"""
        self.progress_bar.setVisible(False)
        self.status_label.setText("")
        
        if success:
            QMessageBox.information(self, "成功", f"{dep_name} 安装成功")
            # 重新检查依赖
            QTimer.singleShot(1000, self._check_dependencies)
        else:
            QMessageBox.critical(self, "失败", f"{dep_name} 安装失败:\n{message}")
    
    def _on_install_progress(self, message: str):
        """安装进度回调"""
        self.status_label.setText(message)
    
    def _show_report(self):
        """显示依赖报告"""
        if not self.dependencies:
            QMessageBox.information(self, "提示", "请先检查依赖项")
            return
        
        report_text = self.dependency_manager.export_dependency_report()
        dialog = DependencyReportDialog(report_text, self)
        dialog.exec()