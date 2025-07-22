#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热键状态监控测试脚本
用于验证热键状态显示是否准确反映实际功能
"""

import sys
import os
import time
import threading
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit
from PyQt6.QtCore import QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from hotkey_manager import HotkeyManager
from settings_manager import SettingsManager

class HotkeyStatusTester(QWidget):
    """热键状态测试器"""
    
    def __init__(self):
        super().__init__()
        self.hotkey_manager = None
        self.settings_manager = None
        self.init_ui()
        self.init_hotkey_manager()
        
        # 状态检查定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)  # 每秒检查一次
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("热键状态监控测试器")
        self.setGeometry(100, 100, 600, 400)
        
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel("热键状态监控测试")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 状态显示
        self.status_label = QLabel("状态：检查中...")
        self.status_label.setFont(QFont("Arial", 12))
        layout.addWidget(self.status_label)
        
        # 详细信息
        self.detail_text = QTextEdit()
        self.detail_text.setMaximumHeight(200)
        layout.addWidget(self.detail_text)
        
        # 控制按钮
        self.start_btn = QPushButton("启动热键监听")
        self.start_btn.clicked.connect(self.start_hotkey)
        layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("停止热键监听")
        self.stop_btn.clicked.connect(self.stop_hotkey)
        layout.addWidget(self.stop_btn)
        
        self.restart_btn = QPushButton("重启热键管理器")
        self.restart_btn.clicked.connect(self.restart_hotkey)
        layout.addWidget(self.restart_btn)
        
        self.setLayout(layout)
        
    def init_hotkey_manager(self):
        """初始化热键管理器"""
        try:
            # 创建设置管理器
            self.settings_manager = SettingsManager()
            
            # 创建热键管理器
            self.hotkey_manager = HotkeyManager(self.settings_manager)
            
            # 设置回调函数
            self.hotkey_manager.set_press_callback(self.on_hotkey_press)
            self.hotkey_manager.set_release_callback(self.on_hotkey_release)
            
            self.log("热键管理器初始化成功")
            
        except Exception as e:
            self.log(f"热键管理器初始化失败: {e}")
            
    def start_hotkey(self):
        """启动热键监听"""
        try:
            if self.hotkey_manager:
                self.hotkey_manager.start_listening()
                self.log("热键监听已启动")
            else:
                self.log("热键管理器未初始化")
        except Exception as e:
            self.log(f"启动热键监听失败: {e}")
            
    def stop_hotkey(self):
        """停止热键监听"""
        try:
            if self.hotkey_manager:
                self.hotkey_manager.stop_listening()
                self.log("热键监听已停止")
            else:
                self.log("热键管理器未初始化")
        except Exception as e:
            self.log(f"停止热键监听失败: {e}")
            
    def restart_hotkey(self):
        """重启热键管理器"""
        try:
            if self.hotkey_manager:
                self.hotkey_manager.cleanup()
                
            # 重新创建
            self.init_hotkey_manager()
            self.log("热键管理器已重启")
            
        except Exception as e:
            self.log(f"重启热键管理器失败: {e}")
            
    def update_status(self):
        """更新状态显示"""
        try:
            if not self.hotkey_manager:
                self.status_label.setText("状态：热键管理器未初始化")
                self.status_label.setStyleSheet("color: red;")
                return
                
            # 获取状态
            status = self.hotkey_manager.get_status()
            
            # 更新状态标签
            if status['active']:
                if status['is_recording']:
                    self.status_label.setText(f"状态：录音中 ({status['hotkey_type']})")
                    self.status_label.setStyleSheet("color: orange;")
                else:
                    self.status_label.setText(f"状态：正常 ({status['hotkey_type']})")
                    self.status_label.setStyleSheet("color: green;")
            else:
                self.status_label.setText(f"状态：失效 ({status['hotkey_type']})")
                self.status_label.setStyleSheet("color: red;")
                
            # 更新详细信息
            details = []
            details.append(f"热键类型: {status['hotkey_type']}")
            details.append(f"整体状态: {'正常' if status['active'] else '失效'}")
            details.append(f"键盘监听器: {'运行中' if status['listener_running'] else '已停止'}")
            details.append(f"Fn监听线程: {'运行中' if status['fn_thread_running'] else '已停止'}")
            details.append(f"录音状态: {'录音中' if status['is_recording'] else '待机'}")
            
            # 添加时间戳
            details.append(f"检查时间: {time.strftime('%H:%M:%S')}")
            
            self.detail_text.setPlainText('\n'.join(details))
            
        except Exception as e:
            self.status_label.setText(f"状态：检查出错 - {str(e)}")
            self.status_label.setStyleSheet("color: red;")
            
    def on_hotkey_press(self):
        """热键按下回调"""
        self.log("🔴 热键按下")
        
    def on_hotkey_release(self):
        """热键释放回调"""
        self.log("🟢 热键释放")
        
    def log(self, message):
        """记录日志"""
        timestamp = time.strftime('%H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        # 也可以在UI中显示
        current_text = self.detail_text.toPlainText()
        if current_text:
            self.detail_text.setPlainText(current_text + '\n' + log_message)
        else:
            self.detail_text.setPlainText(log_message)
            
        # 滚动到底部
        cursor = self.detail_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.detail_text.setTextCursor(cursor)
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        try:
            if self.hotkey_manager:
                self.hotkey_manager.cleanup()
            self.status_timer.stop()
        except Exception as e:
            print(f"清理资源失败: {e}")
        event.accept()

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 创建测试器
    tester = HotkeyStatusTester()
    tester.show()
    
    # 运行应用
    sys.exit(app.exec())

if __name__ == '__main__':
    main()