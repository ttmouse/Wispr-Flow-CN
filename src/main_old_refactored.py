#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重构后的主程序
使用管理器模式，大幅简化Application类
"""

import sys
import os
import logging
import asyncio
import atexit
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

# 添加src目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from managers.application_context import ApplicationContext

# 应用程序常量
APP_NAME = "Dou-flow"
APP_VERSION = "1.1.89"

class RefactoredApplication(QObject):
    """重构后的Application类 - 轻量级协调器
    
    职责大幅简化：
    1. 创建和管理Qt应用程序
    2. 协调ApplicationContext
    3. 处理应用程序生命周期
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
        
        # 5. 连接信号
        self._connect_signals()
        
        # 6. 注册清理函数
        atexit.register(self.cleanup)
        
        # 7. 初始化日志
        self._setup_logging()
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"{APP_NAME} v{APP_VERSION} 启动")
    
    def _setup_application_properties(self):
        """设置应用程序基本属性"""
        self.app.setApplicationName(APP_NAME)
        self.app.setApplicationDisplayName(APP_NAME)
        self.app.setApplicationVersion(APP_VERSION)
        self.app.setQuitOnLastWindowClosed(False)
    
    def _setup_logging(self):
        """设置日志系统"""
        try:
            # 创建logs目录
            logs_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
            os.makedirs(logs_dir, exist_ok=True)
            
            # 配置日志
            import time
            log_filename = f"app_{time.strftime('%Y%m%d_%H%M%S')}.log"
            log_filepath = os.path.join(logs_dir, log_filename)
            
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_filepath, encoding='utf-8'),
                    logging.StreamHandler(sys.stdout)
                ]
            )
            
            print(f"✓ 日志系统已初始化，日志文件: {log_filepath}")
            
        except Exception as e:
            print(f"✗ 日志系统初始化失败: {e}")
    
    def _connect_signals(self):
        """连接信号"""
        # 连接上下文信号
        self.context.initialization_progress.connect(self._on_initialization_progress)
        self.context.initialization_completed.connect(self._on_initialization_completed)
        self.context.initialization_failed.connect(self._on_initialization_failed)
    
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
            return 1
        finally:
            self.cleanup()
    
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
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(
            None,
            "初始化失败",
            f"应用程序初始化失败：\n{error_message}\n\n请检查日志文件获取详细信息。"
        )
        
        # 退出应用程序
        self.app.quit()
    
    def cleanup(self):
        """清理资源"""
        try:
            if hasattr(self, 'logger'):
                self.logger.info("开始清理应用程序资源")
            else:
                print("开始清理应用程序资源")
            
            # 清理应用程序上下文
            if hasattr(self, 'context') and self.context:
                try:
                    self.context.cleanup()
                    if hasattr(self, 'logger'):
                        self.logger.debug("应用程序上下文清理完成")
                except Exception as e:
                    if hasattr(self, 'logger'):
                        self.logger.error(f"清理应用程序上下文失败: {e}")
                    else:
                        print(f"清理应用程序上下文失败: {e}")
            
            # 处理Qt应用程序退出
            if hasattr(self, 'app') and self.app:
                try:
                    # 处理所有待处理的事件
                    self.app.processEvents()
                    
                    # 如果应用程序还在运行，则退出
                    if not self.app.closingDown():
                        self.app.quit()
                        
                except Exception as e:
                    if hasattr(self, 'logger'):
                        self.logger.error(f"退出Qt应用程序失败: {e}")
                    else:
                        print(f"退出Qt应用程序失败: {e}")
            
            if hasattr(self, 'logger'):
                self.logger.info("应用程序资源清理完成")
            else:
                print("应用程序资源清理完成")
            
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"清理资源时出错: {e}")
            else:
                print(f"清理资源时出错: {e}")

def main():
    """主函数"""
    try:
        # 检查Python版本
        if sys.version_info < (3, 8):
            print("错误: 需要Python 3.8或更高版本")
            return 1
        
        # 检查环境
        print("🚀 启动 Dou-flow...")
        
        # 检查conda环境
        conda_env = os.environ.get('CONDA_DEFAULT_ENV')
        if conda_env:
            if conda_env == 'funasr_env':
                print("✅ 当前使用conda funasr_env环境 (推荐)")
            else:
                print(f"⚠️ 当前使用conda {conda_env}环境，推荐使用funasr_env环境")
        else:
            print("ℹ️ 未检测到conda环境")
        
        print("✓ 应用程序正在启动...")
        
        # 创建并运行应用程序
        app = RefactoredApplication()
        return app.run()
        
    except Exception as e:
        print(f"❌ 应用程序启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
