#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化后的主程序
使用重构后的管理器架构，大幅简化Application类
"""

import sys
import os
import logging
import asyncio
import atexit
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread

# 添加src目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from managers.application_context import ApplicationContext
from managers.event_bus import EventType, get_event_bus

# 应用程序常量
APP_NAME = "Dou-flow"
APP_VERSION = "1.1.89"

class SimplifiedApplication(QObject):
    """简化后的Application类 - 轻量级协调器
    
    职责大幅简化：
    1. 创建和管理Qt应用程序
    2. 协调ApplicationContext
    3. 处理应用程序生命周期
    4. 处理全局事件
    """
    
    def __init__(self):
        # 1. 创建Qt应用程序
        self.app = QApplication(sys.argv)
        
        # 2. 初始化QObject
        super().__init__()
        
        # 3. 设置基本属性
        self._setup_application_properties()
        
        # 4. 创建应用程序上下文
        self.context = ApplicationContext(self.app)
        
        # 5. 获取事件总线
        self.event_bus = get_event_bus()
        
        # 6. 连接信号和事件
        self._connect_signals()
        self._subscribe_events()
        
        # 7. 注册清理函数
        atexit.register(self.cleanup)
        
        # 8. 初始化日志
        self._setup_logging()
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"{APP_NAME} v{APP_VERSION} 启动")
    
    def _setup_application_properties(self):
        """设置应用程序基本属性"""
        self.app.setApplicationName(APP_NAME)
        self.app.setApplicationDisplayName(APP_NAME)
        self.app.setApplicationVersion(APP_VERSION)
        self.app.setQuitOnLastWindowClosed(False)
        
        # 设置环境变量以隐藏系统日志
        os.environ['QT_LOGGING_RULES'] = '*.debug=false;qt.qpa.*=false;qt.core.qobject.timer=false'
        os.environ['QT_MAC_DISABLE_FOREGROUND_APPLICATION_TRANSFORM'] = '1'
    
    def _setup_logging(self):
        """设置日志系统"""
        try:
            # 创建logs目录
            logs_dir = os.path.join(project_root, "logs")
            os.makedirs(logs_dir, exist_ok=True)
            
            # 配置日志
            from datetime import datetime
            log_filename = f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            log_filepath = os.path.join(logs_dir, log_filename)
            
            # 创建文件处理器（保留详细日志）
            file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            
            # 创建控制台处理器（只显示警告和错误）
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.WARNING)
            console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
            
            # 配置根日志记录器
            root_logger = logging.getLogger()
            root_logger.setLevel(logging.INFO)
            root_logger.handlers.clear()  # 清除现有处理器
            root_logger.addHandler(file_handler)
            root_logger.addHandler(console_handler)
            
            print(f"✓ 日志系统已初始化，日志文件: {log_filepath}")
            
        except Exception as e:
            print(f"✗ 日志系统初始化失败: {e}")
    
    def _connect_signals(self):
        """连接信号"""
        # 连接上下文信号
        self.context.initialization_progress.connect(self._on_initialization_progress)
        self.context.initialization_completed.connect(self._on_initialization_completed)
        self.context.initialization_failed.connect(self._on_initialization_failed)
    
    def _subscribe_events(self):
        """订阅事件总线事件"""
        # 订阅热键事件
        self.event_bus.subscribe(EventType.HOTKEY_PRESSED, self._on_hotkey_pressed, "SimplifiedApplication")
        self.event_bus.subscribe(EventType.HOTKEY_RELEASED, self._on_hotkey_released, "SimplifiedApplication")
        
        # 订阅窗口事件
        self.event_bus.subscribe(EventType.WINDOW_SHOW_REQUESTED, self._on_window_show_requested, "SimplifiedApplication")
        
        # 订阅系统事件
        self.event_bus.subscribe(EventType.QUIT_REQUESTED, self._on_quit_requested, "SimplifiedApplication")
        
        # 订阅转写完成事件
        self.event_bus.subscribe(EventType.TRANSCRIPTION_COMPLETED, self._on_transcription_completed, "SimplifiedApplication")
    
    async def initialize(self) -> bool:
        """异步初始化应用程序"""
        try:
            self.logger.info("开始初始化应用程序")
            
            # 显示启动界面
            self.context.show_splash()
            
            # 异步初始化上下文
            success = await self.context.initialize()
            
            if success:
                self.logger.info("应用程序初始化成功")
                return True
            else:
                self.logger.error("应用程序初始化失败")
                return False
                
        except Exception as e:
            self.logger.error(f"应用程序初始化异常: {e}")
            self.logger.error(traceback.format_exc())
            return False
    
    def run(self) -> int:
        """运行应用程序"""
        try:
            # 创建异步事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 异步初始化
            init_success = loop.run_until_complete(self.initialize())
            
            if not init_success:
                self.logger.error("应用程序初始化失败，退出")
                return 1
            
            # 运行Qt事件循环
            self.logger.info("进入主事件循环")
            return self.app.exec()
            
        except KeyboardInterrupt:
            self.logger.info("收到中断信号，正在退出...")
            return 0
        except Exception as e:
            self.logger.error(f"应用程序运行异常: {e}")
            self.logger.error(traceback.format_exc())
            return 1
        finally:
            self.cleanup()
    
    # 事件处理方法
    def _on_initialization_progress(self, message: str, progress: int):
        """处理初始化进度"""
        self.logger.debug(f"初始化进度: {message} ({progress}%)")
        self.context.update_splash_progress(message, progress)
    
    def _on_initialization_completed(self):
        """处理初始化完成"""
        self.logger.info("应用程序初始化完成")
        
        # 隐藏启动界面
        self.context.hide_splash()
        
        # 显示主窗口
        self.context.show_main_window()
    
    def _on_initialization_failed(self, error_message: str):
        """处理初始化失败"""
        self.logger.error(f"应用程序初始化失败: {error_message}")
        
        # 隐藏启动界面
        self.context.hide_splash()
        
        # 显示错误信息
        QMessageBox.critical(
            None,
            "初始化失败",
            f"应用程序初始化失败：\n{error_message}\n\n请检查日志文件获取详细信息。"
        )
        
        # 退出应用程序
        self.app.quit()
    
    def _on_hotkey_pressed(self, event):
        """处理热键按下事件"""
        self.logger.debug("热键按下")
        if self.context.is_ready_for_recording():
            self.context.start_recording()
    
    def _on_hotkey_released(self, event):
        """处理热键释放事件"""
        self.logger.debug("热键释放")
        if self.context.is_recording():
            self.context.stop_recording()
    
    def _on_window_show_requested(self, event):
        """处理显示窗口请求"""
        self.logger.debug("收到显示窗口请求")
        self.context.show_main_window()
    
    def _on_quit_requested(self, event):
        """处理退出请求"""
        self.logger.info("收到退出请求")
        self.quit_application()
    
    def _on_transcription_completed(self, event):
        """处理转写完成事件"""
        text = event.data
        if text and text.strip():
            self.logger.info(f"转写完成: {text[:50]}...")
            # 这里可以添加更多的转写完成处理逻辑
    
    def quit_application(self):
        """退出应用程序"""
        try:
            self.logger.info("开始退出应用程序")
            
            # 清理资源
            self.cleanup()
            
            # 退出Qt应用程序
            if hasattr(self, 'app') and self.app:
                self.app.quit()
                
        except Exception as e:
            self.logger.error(f"退出应用程序时出错: {e}")
            # 强制退出
            os._exit(0)
    
    def cleanup(self):
        """清理资源"""
        try:
            self.logger.info("开始清理应用程序资源")
            
            # 清理应用程序上下文
            if hasattr(self, 'context') and self.context:
                self.context.cleanup()
            
            # 清理事件总线
            if hasattr(self, 'event_bus') and self.event_bus:
                from managers.event_bus import cleanup_event_bus
                cleanup_event_bus()
            
            self.logger.info("应用程序资源清理完成")
            
        except Exception as e:
            print(f"清理资源时出错: {e}")

def check_environment():
    """检查当前Python环境并给出提示"""
    python_path = sys.executable
    
    # 检查是否为本地打包版本
    if getattr(sys, 'frozen', False) or 'Dou-flow.app' in python_path:
        print("✅ 本地打包版本，跳过环境检查")
        return True

    # 检查是否在正确的conda环境中
    if 'funasr_env' in python_path:
        print("✅ 当前使用conda funasr_env环境 (推荐)")
        return True
    elif 'venv' in python_path:
        print("⚠️  当前使用项目venv环境")
        print("💡 建议使用: conda activate funasr_env && python src/simplified_main.py")
        return False
    else:
        print(f"❌ 当前环境: {python_path}")
        print("💡 建议使用: conda activate funasr_env && python src/simplified_main.py")
        return False

def main():
    """主函数"""
    try:
        # 检查Python版本
        if sys.version_info < (3, 8):
            print("错误: 需要Python 3.8或更高版本")
            return 1
        
        # 检查环境
        print("🚀 启动 Dou-flow...")
        check_environment()
        
        print("✓ 应用程序正在启动...")
        
        # 创建并运行应用程序
        app = SimplifiedApplication()
        return app.run()
        
    except Exception as e:
        print(f"❌ 应用程序启动失败: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
