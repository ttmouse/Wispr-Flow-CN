import sys
import os
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class AppReloader(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.last_restart = 0
        self.restart_app()

    def restart_app(self):
        # 确保上一个进程已经终止
        if self.process:
            self.process.terminate()
            self.process.wait()

        # 启动新进程
        print("\n🔄 重启应用...")
        env = os.environ.copy()
        env['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))
        self.process = subprocess.Popen([sys.executable, 'src/main.py'], env=env)
        self.last_restart = time.time()

    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            # 防止短时间内多次重启
            if time.time() - self.last_restart > 1:
                print(f"\n📝 检测到文件变化: {os.path.basename(event.src_path)}")
                self.restart_app()

def main():
    # 创建文件监视器1
    event_handler = AppReloader()
    observer = Observer()
    
    # 监视src目录
    src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
    observer.schedule(event_handler, src_path, recursive=True)
    observer.start()

    print("🚀 开发模式已启动")
    print("📝 监视 src 目录下的文件变化...")
    print("按 Ctrl+C 退出")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 停止开发模式...")
        if event_handler.process:
            event_handler.process.terminate()
        observer.stop()
    observer.join()

if __name__ == '__main__':
    main() 