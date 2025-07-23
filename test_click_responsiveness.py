#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试历史记录点击响应性优化
验证点击延迟和响应性问题是否已解决
"""

import sys
import time
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton
from PyQt6.QtCore import QTimer

# 添加src目录到路径
sys.path.insert(0, 'src')

from ui.components.modern_list_widget import ModernListWidget
from ui.components.history_manager import HistoryManager

class ResponsivenessTestWindow(QMainWindow):
    """响应性测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("历史记录点击响应性测试")
        self.setGeometry(100, 100, 500, 700)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 状态标签
        self.status_label = QLabel("等待点击测试...")
        self.status_label.setStyleSheet("""
            padding: 15px;
            background: #f8f9fa;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            font-size: 14px;
            font-weight: bold;
        """)
        layout.addWidget(self.status_label)
        
        # 响应时间标签
        self.response_time_label = QLabel("响应时间: 未测试")
        self.response_time_label.setStyleSheet("""
            padding: 10px;
            background: #e9ecef;
            border-radius: 5px;
            font-size: 12px;
        """)
        layout.addWidget(self.response_time_label)
        
        # 测试计数器
        self.click_count_label = QLabel("点击次数: 0")
        self.click_count_label.setStyleSheet("""
            padding: 10px;
            background: #e9ecef;
            border-radius: 5px;
            font-size: 12px;
        """)
        layout.addWidget(self.click_count_label)
        
        # 创建历史记录管理器
        self.history_manager = HistoryManager("test_responsiveness_history.json", max_history=20)
        
        # 创建历史记录列表
        self.history_list = ModernListWidget()
        self.history_list.itemClicked.connect(self.on_history_item_clicked)
        layout.addWidget(self.history_list)
        
        # 重置按钮
        reset_button = QPushButton("重置测试")
        reset_button.clicked.connect(self.reset_test)
        reset_button.setStyleSheet("""
            QPushButton {
                padding: 10px;
                background: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #0056b3;
            }
        """)
        layout.addWidget(reset_button)
        
        # 测试数据
        self.click_count = 0
        self.last_click_time = None
        
        # 添加测试数据
        self.add_test_data()
    
    def add_test_data(self):
        """添加测试数据"""
        test_texts = [
            "快速响应测试 - 第1条记录",
            "点击延迟测试 - 第2条记录",
            "连续点击测试 - 第3条记录",
            "响应性优化验证 - 第4条记录",
            "无延迟点击测试 - 第5条记录",
            "即时反馈测试 - 第6条记录",
            "用户体验优化 - 第7条记录",
            "最终测试项目 - 第8条记录"
        ]
        
        for text in test_texts:
            # 添加到历史管理器
            self.history_manager.add_history_item(text)
            
            # 添加到列表显示
            self.history_list.addItem(text)
        
        print(f"✓ 已添加 {len(test_texts)} 条测试数据")
    
    def on_history_item_clicked(self, item):
        """处理历史记录项点击事件"""
        try:
            current_time = time.time()
            
            # 记录点击时间
            if self.last_click_time is not None:
                response_time = (current_time - self.last_click_time) * 1000  # 转换为毫秒
                self.response_time_label.setText(f"响应时间: {response_time:.1f}ms")
                
                # 根据响应时间设置颜色
                if response_time < 50:
                    color = "#d4edda"  # 绿色 - 优秀
                    text_color = "#155724"
                elif response_time < 100:
                    color = "#fff3cd"  # 黄色 - 良好
                    text_color = "#856404"
                else:
                    color = "#f8d7da"  # 红色 - 需要改进
                    text_color = "#721c24"
                
                self.response_time_label.setStyleSheet(f"""
                    padding: 10px;
                    background: {color};
                    border-radius: 5px;
                    font-size: 12px;
                    color: {text_color};
                    font-weight: bold;
                """)
            
            self.last_click_time = current_time
            
            # 更新点击计数
            self.click_count += 1
            self.click_count_label.setText(f"点击次数: {self.click_count}")
            
            # 获取点击项的索引和文本
            index = self.history_list.row(item)
            original_text = self.history_manager.get_original_text_by_index(index)
            
            if original_text:
                self.status_label.setText(f"✅ 点击成功！索引: {index}, 文本: {original_text[:40]}...")
                self.status_label.setStyleSheet("""
                    padding: 15px;
                    background: #d4edda;
                    border: 2px solid #c3e6cb;
                    border-radius: 8px;
                    color: #155724;
                    font-size: 14px;
                    font-weight: bold;
                """)
                print(f"✅ 点击响应成功: 索引={index}, 响应时间={response_time:.1f}ms, 文本='{original_text}'")
            else:
                self.status_label.setText(f"❌ 获取文本失败！索引: {index}")
                self.status_label.setStyleSheet("""
                    padding: 15px;
                    background: #f8d7da;
                    border: 2px solid #f5c6cb;
                    border-radius: 8px;
                    color: #721c24;
                    font-size: 14px;
                    font-weight: bold;
                """)
                print(f"❌ 获取原始文本失败: 索引={index}")
                
        except Exception as e:
            error_msg = f"❌ 点击处理失败: {str(e)}"
            self.status_label.setText(error_msg)
            self.status_label.setStyleSheet("""
                padding: 15px;
                background: #f8d7da;
                border: 2px solid #f5c6cb;
                border-radius: 8px;
                color: #721c24;
                font-size: 14px;
                font-weight: bold;
            """)
            print(error_msg)
            import traceback
            print(traceback.format_exc())
    
    def reset_test(self):
        """重置测试"""
        self.click_count = 0
        self.last_click_time = None
        self.click_count_label.setText("点击次数: 0")
        self.response_time_label.setText("响应时间: 未测试")
        self.response_time_label.setStyleSheet("""
            padding: 10px;
            background: #e9ecef;
            border-radius: 5px;
            font-size: 12px;
        """)
        self.status_label.setText("测试已重置，等待点击...")
        self.status_label.setStyleSheet("""
            padding: 15px;
            background: #f8f9fa;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            font-size: 14px;
            font-weight: bold;
        """)
        print("✓ 测试已重置")

def main():
    """主函数"""
    print("=== 历史记录点击响应性测试 ===")
    print("")
    print("测试说明:")
    print("1. 窗口显示了8条测试历史记录")
    print("2. 点击任意历史记录项测试响应性")
    print("3. 观察响应时间和状态反馈")
    print("4. 绿色表示优秀(<50ms)，黄色表示良好(<100ms)，红色表示需要改进")
    print("5. 可以连续快速点击测试稳定性")
    print("6. 使用'重置测试'按钮清除计数")
    print("")
    
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    window = ResponsivenessTestWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec())

if __name__ == "__main__":
    main()