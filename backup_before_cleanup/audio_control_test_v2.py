import sys
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QPushButton, QLabel, QComboBox, QTextEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import time
from Foundation import *
from AppKit import *
import Quartz

class MediaKeyControl:
    """使用媒体键模拟方式控制"""
    
    def __init__(self):
        self.is_paused = False
    
    def simulate_media_key(self):
        """模拟媒体键按下"""
        try:
            # 使用 NSEvent 发送系统级媒体键事件
            event = NSEvent.otherEventWithType_location_modifierFlags_timestamp_windowNumber_context_subtype_data1_data2_(
                14,  # NSEventTypeSystemDefined
                NSPoint(0, 0),
                0xa00,  # NSEventModifierFlagSystemKeyPressed
                0,
                0,
                None,
                8,  # NX_SUBTYPE_AUX_CONTROL
                (16 << 16) | (0xa << 8),  # NX_KEYTYPE_PLAY << 16 | NX_KEYSTATE_DOWN << 8
                -1
            )
            event.CGEvent().post(kCGHIDEventTap)
            return True
        except Exception as e:
            print(f"模拟媒体键失败: {e}")
            return False

    def pause_all(self):
        """使用播放/暂停键控制"""
        if not self.is_paused:
            success = self.simulate_media_key()
            if success:
                self.is_paused = True
                return 1
        return 0

    def resume_all(self):
        """恢复播放"""
        if self.is_paused:
            success = self.simulate_media_key()
            if success:
                self.is_paused = False

class ChromeTabControl:
    """专门控制 Chrome 标签页的音频"""
    
    def __init__(self):
        self.paused_tabs = []
    
    def pause_all(self):
        """暂停所有 Chrome 标签页的音频"""
        try:
            cmd = """
            osascript -e '
                tell application "Google Chrome"
                    set foundTabs to false
                    repeat with w in windows
                        repeat with t in tabs of w
                            try
                                -- 检查标签页是否在播放音频
                                execute t javascript "document.querySelectorAll('video, audio').length > 0"
                                if result is true then
                                    -- 发送空格键来暂停
                                    tell application "System Events"
                                        keystroke space
                                    end tell
                                    set foundTabs to true
                                end if
                            end try
                        end repeat
                    end repeat
                    return foundTabs
                end tell
            '
            """
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            success = "true" in result.stdout.lower()
            return 1 if success else 0
        except Exception as e:
            print(f"暂停 Chrome 标签页失败: {e}")
            return 0

    def resume_all(self):
        """恢复所有暂停的标签页"""
        try:
            cmd = """
            osascript -e '
                tell application "Google Chrome"
                    repeat with w in windows
                        repeat with t in tabs of w
                            try
                                -- 检查标签页是否有媒体元素
                                execute t javascript "document.querySelectorAll('video, audio').length > 0"
                                if result is true then
                                    -- 发送空格键来播放
                                    tell application "System Events"
                                        keystroke space
                                    end tell
                                end if
                            end try
                        end repeat
                    end repeat
                end tell
            '
            """
            subprocess.run(cmd, shell=True)
        except Exception as e:
            print(f"恢复 Chrome 标签页失败: {e}")

class SpotifyControl:
    """专门控制 Spotify"""
    
    def __init__(self):
        self.was_playing = False
    
    def pause_all(self):
        """暂停 Spotify 播放"""
        try:
            cmd = """
            osascript -e '
                if application "Spotify" is running then
                    tell application "Spotify"
                        if player state is playing then
                            set wasPlaying to true
                            pause
                            return true
                        end if
                    end tell
                end if
                return false
            '
            """
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            self.was_playing = "true" in result.stdout.lower()
            return 1 if self.was_playing else 0
        except Exception as e:
            print(f"暂停 Spotify 失败: {e}")
            return 0

    def resume_all(self):
        """恢复 Spotify 播放"""
        if self.was_playing:
            try:
                cmd = """
                osascript -e '
                    if application "Spotify" is running then
                        tell application "Spotify"
                            play
                        end tell
                    end if
                '
                """
                subprocess.run(cmd, shell=True)
            except Exception as e:
                print(f"恢复 Spotify 失败: {e}")
            finally:
                self.was_playing = False

class CombinedControl:
    """组合多种控制方式"""
    
    def __init__(self):
        self.controllers = [
            MediaKeyControl(),
            ChromeTabControl(),
            SpotifyControl()
        ]
        self.active_controllers = []
    
    def pause_all(self):
        """使用所有控制器暂停播放"""
        total_paused = 0
        self.active_controllers = []
        
        for controller in self.controllers:
            count = controller.pause_all()
            if count > 0:
                total_paused += count
                self.active_controllers.append(controller)
        
        return total_paused

    def resume_all(self):
        """恢复所有暂停的播放"""
        for controller in self.active_controllers:
            controller.resume_all()
        self.active_controllers = []

class AudioControlTest(QMainWindow):
    """音频控制测试界面"""
    
    def __init__(self):
        super().__init__()
        self.init_controllers()
        self.init_ui()
        
    def init_controllers(self):
        """初始化所有控制器"""
        self.controllers = {
            "媒体键控制": MediaKeyControl(),
            "Chrome 标签控制": ChromeTabControl(),
            "Spotify 控制": SpotifyControl(),
            "组合控制": CombinedControl()
        }
        self.current_controller = None
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("音频控制测试 v2")
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