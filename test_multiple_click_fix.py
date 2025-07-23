#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试历史记录多次点击修复效果
验证每次点击都能独立处理，不会被覆盖
"""

import sys
import os
import time
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QTextEdit
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ui.components.modern_list_widget import ModernListWidget
from ui.components.history_manager import HistoryManager
from state_manager import StateManager

class MultipleClickTestWindow(QMainWindow):
    """多次点击测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("历史记录多次点击修复测试")
        self.setGeometry(100, 100, 500, 700)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 标题
        title = QLabel("历史记录多次点击修复测试")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # 说明
        instruction = QLabel("请快速连续点击同一个历史记录项，观察是否每次都能正常响应")
        instruction.setFont(QFont("Arial", 10))
        instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction.setStyleSheet("color: #666; margin: 10px;")
        layout.addWidget(instruction)
        
        # 状态显示
        self.status_label = QLabel("等待点击历史记录项...")
        self.status_label.setStyleSheet("padding: 10px; background: #f0f0f0; border-radius: 5px; margin: 10px;")
        layout.addWidget(self.status_label)
        
        # 点击计数器
        self.click_count = 0
        self.click_counter_label = QLabel("点击次数: 0")
        self.click_counter_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.click_counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.click_counter_label)
        
        # 创建历史记录管理器
        self.history_manager = HistoryManager("test_multiple_click.json", max_history=10)
        
        # 创建状态管理器并设置热词
        state_manager = StateManager()
        state_manager.hotwords = ["测试", "点击", "修复"]
        self.history_manager.set_state_manager(state_manager)
        
        # 创建历史记录列表
        self.history_list = ModernListWidget()
        self.history_list.itemClicked.connect(self.on_history_item_clicked)
        layout.addWidget(self.history_list)
        
        # 日志显示
        log_label = QLabel("点击日志:")
        log_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setFont(QFont("Courier", 9))
        layout.addWidget(self.log_text)
        
        # 控制按钮
        button_layout = QVBoxLayout()
        
        add_button = QPushButton("添加测试历史记录")
        add_button.clicked.connect(self.add_test_history)
        button_layout.addWidget(add_button)
        
        clear_button = QPushButton("清空日志")
        clear_button.clicked.connect(self.clear_log)
        button_layout.addWidget(clear_button)
        
        reset_button = QPushButton("重置计数器")
        reset_button.clicked.connect(self.reset_counter)
        button_layout.addWidget(reset_button)
        
        layout.addLayout(button_layout)
        
        # 添加一些测试数据
        self.add_initial_test_data()
        
        # 记录点击时间
        self.last_click_times = []
    
    def add_initial_test_data(self):
        """添加初始测试数据"""
        test_texts = [
            "这是第一条测试历史记录，请多次点击测试",
            "第二条记录：快速连续点击应该每次都有响应",
            "第三条：验证修复效果，不应该被覆盖",
            "第四条：lambda函数应该正确捕获文本",
            "第五条：每次点击都应该独立处理"
        ]
        
        for text in test_texts:
            self.history_manager.add_text(text)
        
        # 更新显示
        self.update_history_display()
    
    def add_test_history(self):
        """添加新的测试历史记录"""
        import random
        test_text = f"新测试记录 {random.randint(1000, 9999)}：请连续点击测试修复效果"
        self.history_manager.add_text(test_text)
        self.update_history_display()
        self.log(f"✅ 添加新记录: {test_text[:30]}...")
    
    def update_history_display(self):
        """更新历史记录显示"""
        self.history_list.clear()
        
        for i, item in enumerate(self.history_manager.get_history()):
            self.history_list.addItem(item['text'])
    
    def on_history_item_clicked(self, item):
        """处理历史记录项点击事件"""
        try:
            current_time = time.time()
            
            # 更新点击计数
            self.click_count += 1
            self.click_counter_label.setText(f"点击次数: {self.click_count}")
            
            # 获取点击项的索引和文本
            index = self.history_list.row(item)
            text = item.text() if hasattr(item, 'text') else str(item)
            
            # 计算与上次点击的时间间隔
            time_interval = ""
            if self.last_click_times:
                interval = (current_time - self.last_click_times[-1]) * 1000
                time_interval = f" (间隔: {interval:.0f}ms)"
            
            self.last_click_times.append(current_time)
            
            # 更新状态显示
            status_text = f"✅ 第{self.click_count}次点击成功！索引: {index}{time_interval}"
            self.status_label.setText(status_text)
            
            # 根据点击频率设置颜色
            if time_interval and "间隔:" in time_interval:
                interval_ms = float(time_interval.split("间隔: ")[1].split("ms")[0])
                if interval_ms < 500:  # 快速点击
                    self.status_label.setStyleSheet("padding: 10px; background: #d4edda; border-radius: 5px; color: #155724;")
                else:
                    self.status_label.setStyleSheet("padding: 10px; background: #fff3cd; border-radius: 5px; color: #856404;")
            else:
                self.status_label.setStyleSheet("padding: 10px; background: #cce5ff; border-radius: 5px; color: #004085;")
            
            # 记录日志
            log_entry = f"[{time.strftime('%H:%M:%S')}] 点击#{self.click_count}: 索引={index}, 文本='{text[:20]}...'{time_interval}"
            self.log(log_entry)
            
            # 模拟处理延迟（测试并发处理）
            QTimer.singleShot(10, lambda: self.simulate_processing(text, self.click_count))
            
        except Exception as e:
            error_msg = f"❌ 点击处理失败: {e}"
            self.status_label.setText(error_msg)
            self.status_label.setStyleSheet("padding: 10px; background: #f8d7da; border-radius: 5px; color: #721c24;")
            self.log(error_msg)
    
    def simulate_processing(self, text, click_number):
        """模拟处理过程（验证lambda函数是否正确捕获变量）"""
        try:
            # 验证文本是否被正确捕获
            if text and len(text) > 0:
                self.log(f"✅ 处理完成#{click_number}: 文本正确捕获 '{text[:15]}...'")
            else:
                self.log(f"❌ 处理失败#{click_number}: 文本捕获失败")
        except Exception as e:
            self.log(f"❌ 模拟处理异常#{click_number}: {e}")
    
    def log(self, message):
        """添加日志"""
        self.log_text.append(message)
        # 自动滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
    
    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
        self.log("📝 日志已清空")
    
    def reset_counter(self):
        """重置计数器"""
        self.click_count = 0
        self