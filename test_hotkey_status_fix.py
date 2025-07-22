#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热键状态监控修复验证脚本
用于验证热键状态指示器是否能正确反映热键的真实状态
"""

import sys
import os
import time
import threading
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit
from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtGui import QFont

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from hotkey_manager import HotkeyManager
from settings_manager import SettingsManager

class HotkeyStatusVerifier(QWidget):
    """热键状态验证器"""
    
    def __init__(self):
        super().__init__()
        self.hotkey_manager = None
        self.settings_manager = None
        self.monitor_thread = None
        self.monitor_should_stop = False
        
        self.init_ui()
        self.init_hotkey_manager()
        
        # 状态检查定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status_display)
        self.status_timer.start(1000)  # 每秒检查一次
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("热键状态监控修复验证")
        self.setGeometry(100, 100, 600, 500)
        
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel("热键状态监控修复验证")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 状态显示
        self.status_label = QLabel("状态：初始化中...")
        self.status_label.setFont(QFont("Arial", 12))
        layout.addWidget(self.status_label)
        
        # 详细信息显示
        self.detail_label = QLabel("详细信息：")
        layout.addWidget(self.detail_label)
        
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
        
        self.start_monitor_btn = QPushButton("启动状态监控")
        self.start_monitor_btn.clicked.connect(self.start_status_monitor)
        layout.addWidget(self.start_monitor_btn)
        
        self.stop_monitor_btn = QPushButton("停止状态监控")
        self.stop_monitor_btn.clicked.connect(self.stop_status_monitor)
        layout.addWidget(self.stop_monitor_btn)
        
        # 日志显示
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        layout.addWidget(self.log_text)
        
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
            
            self.log("✓ 热键管理器初始化成功")
            
        except Exception as e:
            self.log(f"❌ 热键管理器初始化失败: {e}")
    
    def on_hotkey_press(self):
        """热键按下回调"""
        self.log("🔥 热键按下")
    
    def on_hotkey_release(self):
        """热键释放回调"""
        self.log("🔥 热键释放")
    
    def start_hotkey(self):
        """启动热键监听"""
        try:
            if self.hotkey_manager:
                self.hotkey_manager.start_listening()
                self.log("✓ 热键监听已启动")
            else:
                self.log("❌ 热键管理器未初始化")
        except Exception as e:
            self.log(f"❌ 启动热键监听失败: {e}")
    
    def stop_hotkey(self):
        """停止热键监听"""
        try:
            if self.hotkey_manager:
                self.hotkey_manager.stop_listening()
                self.log("✓ 热键监听已停止")
            else:
                self.log("❌ 热键管理器未初始化")
        except Exception as e:
            self.log(f"❌ 停止热键监听失败: {e}")
    
    def restart_hotkey(self):
        """重启热键管理器"""
        try:
            if self.hotkey_manager:
                self.hotkey_manager.cleanup()
                self.log("✓ 热键管理器已清理")
            
            # 重新创建
            self.init_hotkey_manager()
            self.start_hotkey()
            self.log("✓ 热键管理器已重启")
            
        except Exception as e:
            self.log(f"❌ 重启热键管理器失败: {e}")
    
    def start_status_monitor(self):
        """启动状态监控（模拟Application.start_hotkey_monitor）"""
        if not self.hotkey_manager:
            self.log("❌ 热键管理器未就绪")
            return
            
        # 停止现有监控
        self.stop_status_monitor()
        
        self.monitor_should_stop = False
        
        def monitor_hotkey_status():
            consecutive_failures = 0
            max_failures = 3
            
            while not self.monitor_should_stop:
                try:
                    check_interval = 5 if consecutive_failures < max_failures else 15
                    time.sleep(check_interval)
                    
                    if self.monitor_should_stop:
                        break
                        
                    if self.hotkey_manager:
                        status = self.hotkey_manager.get_status()
                        
                        if not status['active']:
                            consecutive_failures += 1
                            if not self.monitor_should_stop:
                                self.log(f"⚠️ 检测到热键失效 (第{consecutive_failures}次): {status}")
                        else:
                            if consecutive_failures > 0:
                                self.log("✓ 热键状态已恢复正常")
                                consecutive_failures = 0
                    else:
                        consecutive_failures += 1
                        self.log(f"⚠️ 热键管理器不存在 (第{consecutive_failures}次)")
                        
                except Exception as e:
                    consecutive_failures += 1
                    if not self.monitor_should_stop:
                        self.log(f"❌ 热键状态监控出错 (第{consecutive_failures}次): {e}")
                        
            self.log("✓ 热键状态监控已停止")
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(target=monitor_hotkey_status, daemon=True)
        self.monitor_thread.start()
        self.log("✓ 热键状态监控已启动")
    
    def stop_status_monitor(self):
        """停止状态监控"""
        if hasattr(self, 'monitor_should_stop'):
            self.monitor_should_stop = True
            self.log("✓ 状态监控停止信号已发送")
    
    def update_status_display(self):
        """更新状态显示"""
        try:
            if not self.hotkey_manager:
                self.status_label.setText("状态：❌ 热键管理器未初始化")
                self.status_label.setStyleSheet("color: red;")
                self.detail_label.setText("详细信息：热键管理器不存在")
                return
            
            # 获取热键状态
            status = self.hotkey_manager.get_status()
            
            if status['active']:
                if status['is_recording']:
                    self.status_label.setText("状态：🟠 录音中")
                    self.status_label.setStyleSheet("color: orange;")
                    tooltip = f"热键状态：录音中 ({status['hotkey_type']})"
                else:
                    self.status_label.setText("状态：🟢 正常")
                    self.status_label.setStyleSheet("color: green;")
                    tooltip = f"热键状态：正常 ({status['hotkey_type']})"
            else:
                self.status_label.setText("状态：🔴 失效")
                self.status_label.setStyleSheet("color: red;")
                tooltip_details = []
                if not status['listener_running']:
                    tooltip_details.append("监听器未运行")
                if status['hotkey_type'] == 'fn' and not status['fn_thread_running']:
                    tooltip_details.append("Fn监听线程未运行")
                
                detail_text = ", ".join(tooltip_details) if tooltip_details else "未知错误"
                tooltip = f"热键状态：失效 ({status['hotkey_type']}) - {detail_text}"
            
            self.detail_label.setText(f"详细信息：{tooltip}")
            
        except Exception as e:
            self.status_label.setText("状态：❌ 检查出错")
            self.status_label.setStyleSheet("color: red;")
            self.detail_label.setText(f"详细信息：检查出错 - {str(e)}")
    
    def log(self, message):
        """添加日志"""
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        self.log_text.append(log_message)
        print(log_message)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.stop_status_monitor()
        if self.hotkey_manager:
            self.hotkey_manager.cleanup()
        event.accept()

def main():
    app = QApplication(sys.argv)
    verifier = HotkeyStatusVerifier()
    verifier.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()