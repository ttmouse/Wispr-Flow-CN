import sys
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QPushButton, QLabel, QComboBox, QTextEdit)
from PyQt6.QtCore import Qt
import time
from Foundation import *
from AppKit import *
import objc
from AVFoundation import *
import CoreAudio

class AudioSessionControl:
    """使用 CoreAudio 控制音频会话"""
    
    def __init__(self):
        self.previous_states = {}
        # 初始化 AVAudioSession
        self.session = AVAudioSession.sharedInstance()
        
    def get_running_apps(self):
        """获取正在运行的应用列表"""
        try:
            cmd = """
            osascript -e '
                tell application "System Events"
                    set appList to {}
                    repeat with p in processes
                        if background only of p is false then
                            set end of appList to name of p
                        end if
                    end repeat
                    return appList
                end tell
            '
            """
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.stdout.strip().split(", ")
        except Exception as e:
            print(f"获取应用列表失败: {e}")
            return []

    def pause_all(self):
        """暂停所有音频输出"""
        try:
            # 1. 获取所有正在运行的应用
            apps = self.get_running_apps()
            paused_count = 0
            
            # 2. 遍历应用并尝试控制音频
            for app in apps:
                try:
                    cmd = f"""
                    osascript -e '
                        tell application "System Events"
                            tell process "{app}"
                                set audioPlaying to false
                                try
                                    -- 检查是否有音频输出
                                    set audioPlaying to exists (first audio of it whose muted is false)
                                end try
                                if audioPlaying then
                                    -- 记录并暂停音频
                                    set volume output muted of (get volume settings) to true
                                    return true
                                end if
                            end tell
                        end tell
                    '
                    """
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    if "true" in result.stdout.lower():
                        self.previous_states[app] = True
                        paused_count += 1
                except Exception as e:
                    print(f"暂停 {app} 失败: {e}")
                    continue
            
            return paused_count
        except Exception as e:
            print(f"暂停音频失败: {e}")
            return 0

    def resume_all(self):
        """恢复所有暂停的音频"""
        try:
            for app in self.previous_states.keys():
                try:
                    cmd = f"""
                    osascript -e '
                        tell application "System Events"
                            tell process "{app}"
                                set volume output muted of (get volume settings) to false
                            end tell
                        end tell
                    '
                    """
                    subprocess.run(cmd, shell=True)
                except Exception as e:
                    print(f"恢复 {app} 失败: {e}")
        except Exception as e:
            print(f"恢复音频失败: {e}")
        finally:
            self.previous_states = {}

class AudioHijackControl:
    """使用 Audio Hijack 方式控制"""
    
    def __init__(self):
        self.active_apps = set()
    
    def pause_all(self):
        """暂停所有音频输出"""
        try:
            cmd = """
            osascript -e '
                tell application "System Events"
                    set activeApps to {}
                    -- 获取所有正在播放音频的应用
                    repeat with p in processes
                        try
                            if exists (first audio of p whose muted is false) then
                                set end of activeApps to name of p
                                -- 暂时禁用音频输出
                                set muted of every audio of p to true
                            end if
                        end try
                    end repeat
                    return activeApps
                end tell
            '
            """
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            apps = result.stdout.strip().split(", ")
            self.active_apps = set(app for app in apps if app)
            return len(self.active_apps)
        except Exception as e:
            print(f"暂停音频失败: {e}")
            return 0

    def resume_all(self):
        """恢复所有暂停的音频"""
        try:
            for app in self.active_apps:
                cmd = f"""
                osascript -e '
                    tell application "System Events"
                        tell process "{app}"
                            set muted of every audio to false
                        end tell
                    end tell
                '
                """
                subprocess.run(cmd, shell=True)
        except Exception as e:
            print(f"恢复音频失败: {e}")
        finally:
            self.active_apps.clear()

class AudioDeviceControl:
    """使用音频设备级别控制"""
    
    def __init__(self):
        self.previous_states = {}
        
    def get_audio_devices(self):
        """获取系统音频设备"""
        try:
            cmd = """
            osascript -e '
                tell application "System Events"
                    tell audio of current date
                        return {name, output volume}
                    end tell
                end tell
            '
            """
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.stdout.strip()
        except Exception as e:
            print(f"获取音频设备失败: {e}")
            return None

    def pause_all(self):
        """暂停所有音频设备输出"""
        try:
            # 保存当前状态
            self.previous_states["volume"] = self.get_audio_devices()
            
            cmd = """
            osascript -e '
                tell application "System Events"
                    set volume input volume 0
                    set volume alert volume 0
                    set volume output volume 0
                    return true
                end tell
            '
            """
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return 1 if "true" in result.stdout.lower() else 0
        except Exception as e:
            print(f"暂停音频设备失败: {e}")
            return 0

    def resume_all(self):
        """恢复所有音频设备"""
        try:
            if "volume" in self.previous_states:
                volume = self.previous_states["volume"]
                cmd = f"""
                osascript -e '
                    tell application "System Events"
                        set volume {volume}
                    end tell
                '
                """
                subprocess.run(cmd, shell=True)
        except Exception as e:
            print(f"恢复音频设备失败: {e}")
        finally:
            self.previous_states.clear()

class AudioControlTest(QMainWindow):
    """音频控制测试界面"""
    
    def __init__(self):
        super().__init__()
        self.init_controllers()
        self.init_ui()
        
    def init_controllers(self):
        """初始化所有控制器"""
        self.controllers = {
            "音频会话控制": AudioSessionControl(),
            "音频劫持控制": AudioHijackControl(),
            "设备级控制": AudioDeviceControl()
        }
        self.current_controller = None
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("音频控制测试 v3")
        self.setGeometry(100, 100, 600, 400)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        
        # 控制方式选择
        self.method_combo = QComboBox()
        self.method_combo.addItems(list(self.controllers.keys()))
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
            self.log(f"成功暂停了 {count} 个媒体源")
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
            self.log("没有需要恢复的媒体源")

def main():
    app = QApplication(sys.argv)
    window = AudioControlTest()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 