#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试历史记录点击功能修复
验证点击历史记录项是否能正常触发事件
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from ui.components.modern_list_widget import ModernListWidget
from ui.components.history_manager import HistoryManager
from state_manager import StateManager

class TestWindow(QMainWindow):
    """测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("历史记录点击测试")
        self.setGeometry(100, 100, 400, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 状态标签
        self.status_label = QLabel("等待点击历史记录项...")
        self.status_label.setStyleSheet("padding: 10px; background: #f0f0f0; border-radius: 5px;")
        layout.addWidget(self.status_label)
        
        # 创建历史记录管理器
        self.history_manager = HistoryManager("test_history_click.json", max_history=10)
        
        # 创建状态管理器并设置热词
        state_manager = StateManager()
        if hasattr(state_manager, 'hotwords'):
            state_manager.hotwords = ["测试", "点击", "历史"]
        else:
            state_manager.get_hotwords = lambda: ["测试", "点击", "历史"]
        self.history_manager.set_state_manager(state_manager)
        
        # 创建历史记录列表
        self.history_list = ModernListWidget()
        self.history_list.itemClicked.connect(self.on_history_item_clicked)
        layout.addWidget(self.history_list)
        
        # 添加测试数据
        self.add_test_data()
        
        print("✓ 测试窗口初始化完成")
        print("请点击历史记录项测试功能")
    
    def add_test_data(self):
        """添加测试数据"""
        test_texts = [
            "这是第一条测试历史记录",
            "点击这条记录测试功能",
            "历史记录点击测试项目",
            "验证修复后的点击响应",
            "最后一条测试数据"
        ]
        
        for text in test_texts:
            # 添加到历史管理器
            self.history_manager.add_history_item(text)
            # 添加到UI列表
            highlighted_text = self.history_manager.apply_hotword_highlight(text)
            self.history_list.addItem(highlighted_text)
        
        print(f"✓ 已添加 {len(test_texts)} 条测试数据")
    
    def on_history_item_clicked(self, item):
        """处理历史记录项点击事件"""
        try:
            # 获取点击项的索引
            index = self.history_list.row(item)
            
            # 通过历史记录管理器获取原始文本
            original_text = self.history_manager.get_original_text_by_index(index)
            
            if original_text:
                self.status_label.setText(f"✅ 点击成功！索引: {index}, 文本: {original_text[:30]}...")
                self.status_label.setStyleSheet("padding: 10px; background: #d4edda; border-radius: 5px; color: #155724;")
                print(f"✅ 历史记录点击成功: 索引={index}, 文本='{original_text}'")
            else:
                self.status_label.setText(f"❌ 获取文本失败！索引: {index}")
                self.status_label.setStyleSheet("padding: 10px; background: #f8d7da; border-radius: 5px; color: #721c24;")
                print(f"❌ 获取原始文本失败: 索引={index}")
                
        except Exception as e:
            error_msg = f"❌ 点击处理失败: {str(e)}"
            self.status_label.setText(error_msg)
            self.status_label.setStyleSheet("padding: 10px; background: #f8d7da; border-radius: 5px; color: #721c24;")
            print(error_msg)
            import traceback
            traceback.print_exc()

def main():
    """主函数"""
    print("=== 历史记录点击功能修复测试 ===")
    
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    window = TestWindow()
    window.show()
    
    print("测试说明:")
    print("1. 窗口中显示了5条测试历史记录")
    print("2. 点击任意历史记录项")
    print("3. 观察状态标签是否显示点击成功信息")
    print("4. 控制台会输出详细的点击处理信息")
    print("")
    
    # 运行应用
    sys.exit(app.exec())

if __name__ == "__main__":
    main()