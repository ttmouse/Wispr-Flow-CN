#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的拖拽禁用测试
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont, QMouseEvent

class TestMainWindow(QMainWindow):
    """测试主窗口"""
    
    def __init__(self):
        super().__init__()
        self._initialization_complete = False  # 初始化完成标志
        self._is_dragging = False
        self._drag_start_pos = None
        self.setup_ui()
        self.start_initialization()
        
    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("拖拽禁用测试窗口")
        self.setGeometry(200, 200, 500, 400)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # 主容器
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # 标题栏（可拖拽区域）
        self.title_bar = QLabel("📋 拖拽测试 - 点击此处拖拽窗口")
        self.title_bar.setFixedHeight(40)
        self.title_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_bar.setStyleSheet("""
            QLabel {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
                margin: 5px;
            }
        """)
        # 绑定鼠标事件
        self.title_bar.mousePressEvent = self._on_title_bar_mouse_press
        self.title_bar.mouseMoveEvent = self._on_title_bar_mouse_move
        self.title_bar.mouseReleaseEvent = self._on_title_bar_mouse_release
        layout.addWidget(self.title_bar)
        
        # 状态显示
        self.status_label = QLabel("🔄 正在初始化...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("Arial", 16))
        self.status_label.setStyleSheet("""
            QLabel {
                color: #FF9800;
                margin: 20px;
                padding: 20px;
                border: 2px dashed #FF9800;
                border-radius: 10px;
            }
        """)
        layout.addWidget(self.status_label)
        
        # 说明文字
        info_label = QLabel(
            "测试说明:\n"
            "1. 窗口启动后立即尝试拖拽标题栏\n"
            "2. 初始化期间拖拽应该被禁用\n"
            "3. 等待初始化完成后再次尝试拖拽\n"
            "4. 初始化完成后拖拽应该正常工作"
        )
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("""
            QLabel {
                color: #666;
                background-color: #f5f5f5;
                padding: 15px;
                border-radius: 8px;
                margin: 10px;
                line-height: 1.5;
            }
        """)
        layout.addWidget(info_label)
        
        central_widget.setLayout(layout)
        
    def start_initialization(self):
        """开始初始化过程"""
        print("🚀 开始初始化过程")
        print("📝 请立即尝试拖拽窗口标题栏，应该看到禁用提示")
        
        # 模拟初始化过程（3秒）
        self.init_timer = QTimer()
        self.init_timer.timeout.connect(self.complete_initialization)
        self.init_timer.start(3000)  # 3秒后完成初始化
        
    def complete_initialization(self):
        """完成初始化"""
        try:
            self._initialization_complete = True
            self.status_label.setText("✅ 初始化完成 - 现在可以拖拽窗口了")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #4CAF50;
                    margin: 20px;
                    padding: 20px;
                    border: 2px solid #4CAF50;
                    border-radius: 10px;
                }
            """)
            self.init_timer.stop()
            # 移除print语句，避免在定时器回调中可能的崩溃
        except Exception as e:
            # 静默处理异常，避免在定时器回调中抛出异常
            pass
        
    def _on_title_bar_mouse_press(self, event):
        """标题栏鼠标按下事件"""
        try:
            print(f"\n🖱️  标题栏鼠标按下事件触发")
            print(f"   初始化状态: {'完成' if self._initialization_complete else '进行中'}")
            
            # 检查初始化是否完成
            if not self._initialization_complete:
                print("⚠️  界面尚未完全加载，拖拽功能暂时禁用")
                return
            
            # 检查事件对象
            if not event or not hasattr(event, 'button'):
                print("⚠️  无效的鼠标事件对象")
                return
                
            if event.button() == Qt.MouseButton.LeftButton:
                self._is_dragging = True
                self._drag_start_pos = event.globalPosition().toPoint()
                print(f"✓ 开始拖拽，起始位置: {self._drag_start_pos}")
                
        except Exception as e:
            print(f"❌ 标题栏鼠标按下事件处理出错: {e}")
            import traceback
            print(f"详细错误: {traceback.format_exc()}")
            
    def _on_title_bar_mouse_move(self, event):
        """标题栏鼠标移动事件"""
        try:
            # 检查初始化是否完成
            if not self._initialization_complete:
                return
                
            # 检查事件对象
            if not event or not hasattr(event, 'globalPosition'):
                return
                
            if self._is_dragging and self._drag_start_pos:
                current_pos = event.globalPosition().toPoint()
                diff = current_pos - self._drag_start_pos
                new_pos = self.pos() + diff
                self.move(new_pos)
                self._drag_start_pos = current_pos
                
        except Exception as e:
            print(f"❌ 标题栏鼠标移动事件处理出错: {e}")
            
    def _on_title_bar_mouse_release(self, event):
        """标题栏鼠标释放事件"""
        try:
            if self._is_dragging:
                print("✓ 拖拽结束")
            self._is_dragging = False
            self._drag_start_pos = None
            
        except Exception as e:
            print(f"❌ 标题栏鼠标释放事件处理出错: {e}")

def main():
    """主函数"""
    print("🧪 启动简单拖拽禁用测试")
    print("📋 测试目标: 验证初始化期间拖拽被正确禁用")
    print("\n" + "="*50)
    
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    window = TestMainWindow()
    window.show()
    
    print("✓ 测试窗口已显示")
    print("💡 请立即尝试拖拽窗口标题栏")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()