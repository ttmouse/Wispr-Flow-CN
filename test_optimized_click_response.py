#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试优化后的历史记录点击响应时间
"""

import sys
import os
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ui.components.modern_list_widget import ModernListWidget
from history_manager import HistoryManager
from clipboard_manager import ClipboardManager

class ResponseTimeTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("历史记录点击响应时间测试")
        self.setGeometry(100, 100, 600, 500)
        
        # 初始化管理器
        self.history_manager = HistoryManager()
        self.clipboard_manager = ClipboardManager(debug_mode=True)
        
        # 创建测试数据
        self.create_test_data()
        
        # 设置UI
        self.setup_ui()
        
        # 响应时间记录
        self.click_start_time = None
        self.response_times = []
        
    def create_test_data(self):
        """创建测试数据"""
        test_items = [
            "快速响应测试 - 第1条记录",
            "零延迟测试 - 第2条记录", 
            "优化后测试 - 第3条记录",
            "性能提升测试 - 第4条记录",
            "即时反馈测试 - 第5条记录"
        ]
        
        for item in test_items:
            self.history_manager.add_to_history(item)
            
    def setup_ui(self):
        """设置用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # 状态标签
        self.status_label = QLabel("点击历史记录项目测试响应时间")
        layout.addWidget(self.status_label)
        
        # 历史记录列表
        self.history_list = ModernListWidget()
        self.history_list.itemClicked.connect(self.on_history_item_clicked)
        layout.addWidget(self.history_list)
        
        # 测试按钮
        self.test_button = QPushButton("开始自动测试")
        self.test_button.clicked.connect(self.start_auto_test)
        layout.addWidget(self.test_button)
        
        # 结果标签
        self.result_label = QLabel("")
        layout.addWidget(self.result_label)
        
        # 加载历史记录
        self.load_history()
        
    def load_history(self):
        """加载历史记录到列表"""
        self.history_list.clear()
        history_items = self.history_manager.get_history()
        
        for item in history_items:
            self.history_list.add_item(item)
            
    def on_history_item_clicked(self, item):
        """处理历史记录项目点击"""
        if self.click_start_time is not None:
            # 计算响应时间
            response_time = (time.time() - self.click_start_time) * 1000  # 转换为毫秒
            self.response_times.append(response_time)
            
            # 获取文本内容
            text = self.history_manager.get_original_text(item.text())
            
            # 显示结果
            result_text = f"✅ 点击响应: 响应时间={response_time:.1f}ms, 文本='{text}'"
            print(result_text)
            self.status_label.setText(result_text)
            
            # 执行剪贴板操作（模拟实际使用）
            self.clipboard_manager.safe_copy_and_paste(text)
            
            # 重置计时器
            self.click_start_time = None
            
    def start_auto_test(self):
        """开始自动测试"""
        self.response_times.clear()
        self.test_button.setEnabled(False)
        self.result_label.setText("正在进行自动测试...")
        
        # 开始测试序列
        self.test_index = 0
        self.run_next_test()
        
    def run_next_test(self):
        """运行下一个测试"""
        if self.test_index >= self.history_list.count():
            # 测试完成，显示结果
            self.show_test_results()
            return
            
        # 记录开始时间
        self.click_start_time = time.time()
        
        # 模拟点击
        item = self.history_list.item(self.test_index)
        self.history_list.itemClicked.emit(item)
        
        self.test_index += 1
        
        # 延迟后进行下一个测试
        QTimer.singleShot(100, self.run_next_test)
        
    def show_test_results(self):
        """显示测试结果"""
        if self.response_times:
            avg_time = sum(self.response_times) / len(self.response_times)
            min_time = min(self.response_times)
            max_time = max(self.response_times)
            
            result_text = f"""测试完成！
平均响应时间: {avg_time:.1f}ms
最快响应时间: {min_time:.1f}ms
最慢响应时间: {max_time:.1f}ms
测试次数: {len(self.response_times)}"""
            
            print("\n" + "="*50)
            print("响应时间测试结果:")
            print(f"平均响应时间: {avg_time:.1f}ms")
            print(f"最快响应时间: {min_time:.1f}ms")
            print(f"最慢响应时间: {max_time:.1f}ms")
            print(f"测试次数: {len(self.response_times)}")
            print("="*50)
            
            self.result_label.setText(result_text)
        else:
            self.result_label.setText("测试失败，没有记录到响应时间")
            
        self.test_button.setEnabled(True)

def main():
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    test_window = ResponseTimeTestWindow()
    test_window.show()
    
    print("历史记录点击响应时间测试窗口已启动")
    print("请点击历史记录项目或使用'开始自动测试'按钮")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()