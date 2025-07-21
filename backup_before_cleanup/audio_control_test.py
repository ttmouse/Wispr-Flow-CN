import sys
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QPushButton, QLabel, QComboBox, QTextEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import time
from Foundation import *
from AppKit import *
from ScriptingBridge import SBApplication

class MediaRemoteControl:
    """使用 Media Remote Control API 控制媒体播放"""
    
    def __init__(self):
        self.paused_apps = []
    
    def get_media_playing_apps(self):
        """获取正在播放媒体的应用"""
        try:
            # 使用 osascript 获取正在播放的应用
            cmd = """
            osascript -e '
                tell application "System Events"
                    set activeApps to {}
                    repeat with proc in (every process whose background only is false)
                        try
                            if exists (proc\'s first window) then
                                if exists (value of attribute "AXTitle" of proc\'s first window) then
                                    set end of activeApps to name of proc
                                end if
                            end if
                        end try
                    end repeat
                    return activeApps
                end tell
            '
            """
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            apps = result.stdout.strip().split(", ")
            return [app for app in apps if app]  # 过滤空值
        except Exception as e:
            print(f"获取应用列表失败: {e}")
            return []

    def send_pause_command(self, app_name):
        """发送暂停命令到指定应用"""
        try:
            cmd = f"""
            osascript -e '
                tell application "{app_name}"
                    if it is running then
                        try
                            pause
                            return true
                        on error
                            return false
                        end try
                    end if
                end tell
            '
            """
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return "true" in result.stdout.lower()
        except Exception as e:
            print(f"发送暂停命令失败: {e}")
            return False

    def send_play_command(self, app_name):
        """发送播放命令到指定应用"""
        try:
            cmd = f"""
            osascript -e '
                tell application "{app_name}"
                    if it is running then
                        try
                            play
                            return true
                        on error
                            return false
                        end try
                    end if
                end tell
            '
            """
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return "true" in result.stdout.lower()
        except Exception as e:
            print(f"发送播放命令失败: {e}")
            return False

    def pause_all(self):
        """暂停所有媒体播放"""
        active_apps = self.get_media_playing_apps()
        self.paused_apps = []
        
        for app in active_apps:
            if self.send_pause_command(app):
                self.paused_apps.append(app)
                print(f"已暂停: {app}")
        
        return len(self.paused_apps)

    def resume_all(self):
        """恢复所有暂停的应用"""
        for app in self.paused_apps:
            if self.send_play_command(app):
                print(f"已恢复: {app}")
        self.paused_apps = []

class ScriptingBridgeControl:
    """使用 ScriptingBridge 控制媒体播放"""
    
    def __init__(self):
        self.paused_apps = {}
    
    def get_media_apps(self):
        """获取支持媒体控制的应用列表"""
        # 常见的媒体应用
        media_apps = ['Music', 'Spotify', 'QuickTime Player', 'VLC', 'Chrome']
        running_apps = []
        
        for app_name in media_apps:
            try:
                app = SBApplication.applicationWithBundleIdentifier_(f"com.apple.{app_name.lower()}")
                if app and app.isRunning():
                    running_apps.append(app_name)
            except Exception as e:
                print(f"检查应用 {app_name} 失败: {e}")
        
        return running_apps

    def pause_all(self):
        """暂停所有媒体应用"""
        count = 0
        for app_name in self.get_media_apps():
            try:
                app = SBApplication.applicationWithBundleIdentifier_(f"com.apple.{app_name.lower()}")
                if app and hasattr(app, 'pause'):
                    app.pause()
                    self.paused_apps[app_name] = app
                    count += 1
                    print(f"已暂停: {app_name}")
            except Exception as e:
                print(f"暂停 {app_name} 失败: {e}")
        return count

    def resume_all(self):
        """恢复所有暂停的应用"""
        for app_name, app in self.paused_apps.items():
            try:
                if hasattr(app, 'play'):
                    app.play()
                    print(f"已恢复: {app_name}")
            except Exception as e:
                print(f"恢复 {app_name} 失败: {e}")
        self.paused_apps = {}

class SystemVolumeControl:
    """使用系统音量控制方式"""
    
    def __init__(self):
        self.previous_volume = None
    
    def get_volume(self):
        """获取当前系统音量"""
        try:
            cmd = "osascript -e 'output volume of (get volume settings)'"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return int(result.stdout.strip())
        except Exception as e:
            print(f"获取音量失败: {e}")
            return None

    def set_volume(self, volume):
        """设置系统音量"""
        try:
            cmd = f"osascript -e 'set volume output volume {volume}'"
            subprocess.run(cmd, shell=True, check=True)
            return True
        except Exception as e:
            print(f"设置音量失败: {e}")
            return False

    def pause_all(self):
        """通过设置音量为0来"暂停"所有声音"""
        self.previous_volume = self.get_volume()
        if self.previous_volume is not None:
            return 1 if self.set_volume(0) else 0
        return 0

    def resume_all(self):
        """恢复之前的音量"""
        if self.previous_volume is not None:
            self.set_volume(self.previous_volume)
            self.previous_volume = None

class AudioControlTest(QMainWindow):
    """音频控制测试界面"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_controllers()
        
    def init_controllers(self):
        """初始化所有控制器"""
        self.controllers = {
            "Media Remote Control": MediaRemoteControl(),
            "ScriptingBridge": ScriptingBridgeControl(),
            "System Volume": SystemVolumeControl()
        }
        self.current_controller = None
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("音频控制测试")
        self.setGeometry(100, 100, 600, 400)
        
        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        
        # 控制方式选择
        self.method_combo = QComboBox()
        self.method_combo.addItems([
            "Media Remote Control",
            "ScriptingBridge",
            "System Volume"
        ])
        layout.addWidget(QLabel("选择控制方式:"))
        layout.addWidget(self.method_combo)
        
        # 控制按钮
        self.pause_button = QPushButton("暂停所有媒体(&P)")
        self.pause_button.clicked.connect(self.pause_all)
        layout.addWidget(self.pause_button)
        
        self.resume_button = QPushButton("恢复播放(&R)")
        self.resume_button.clicked.connect(self.resume_all)
        layout.addWidget(self.resume_button)
        
        # 日志显示
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(QLabel("操作日志:"))
        layout.addWidget(self.log_text)
        
        central_widget.setLayout(layout)
        
    def log(self, message):
        """添加日志信息"""
        self.log_text.append(f"{time.strftime('%H:%M:%S')} - {message}")
    
    def pause_all(self):
        """暂停所有媒体"""
        method = self.method_combo.currentText()
        controller = self.controllers[method]
        self.log(f"使用 {method} 方式暂停媒体...")
        
        try:
            count = controller.pause_all()
            self.log(f"成功暂停了 {count} 个应用")
            self.current_controller = controller
        except Exception as e:
            self.log(f"暂停失败: {e}")
    
    def resume_all(self):
        """恢复所有媒体"""
        if self.current_controller:
            method = self.method_combo.currentText()
            self.log(f"使用 {method} 方式恢复播放...")
            
            try:
                self.current_controller.resume_all()
                self.log("已恢复播放")
            except Exception as e:
                self.log(f"恢复失败: {e}")
        else:
            self.log("没有需要恢复的应用")

def main():
    app = QApplication(sys.argv)
    window = AudioControlTest()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 