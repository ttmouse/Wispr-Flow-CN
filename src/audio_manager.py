import Foundation
import objc
import AppKit
import subprocess
from PyQt6.QtCore import QObject, QThread

class AudioManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.paused_apps = set()
        
        # 确保在主线程中初始化
        if parent and QThread.currentThread() != parent.thread():
            self.moveToThread(parent.thread())
        
    def _pause_all_audio(self):
        """简化的音频暂停 - 只处理最常用的应用"""
        script = '''
        on run
            set didPause to false
            
            -- 暂停 Music
            try
                tell application "Music"
                    if player state is playing then
                        pause
                        set didPause to true
                    end if
                end tell
            end try
            
            -- 暂停 Spotify
            try
                tell application "Spotify"
                    if player state is playing then
                        pause
                        set didPause to true
                    end if
                end tell
            end try
            
            -- 发送通用媒体暂停键
            try
                tell application "System Events"
                    key code 16 using {command down}  -- Command + P
                    set didPause to true
                end tell
            end try
            
            return didPause
        end run
        '''
        
        try:
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and "true" in result.stdout.lower():
                return True
        except Exception as e:
            import logging
            logging.error(f"暂停音频失败: {e}")
        return False
        
    def _resume_all_audio(self):
        """简化的音频恢复 - 只处理最常用的应用"""
        script = '''
        on run
            -- 恢复 Music
            try
                tell application "Music"
                    play
                end tell
            end try
            
            -- 恢复 Spotify
            try
                tell application "Spotify"
                    play
                end tell
            end try
            
            -- 发送通用媒体播放键
            try
                tell application "System Events"
                    key code 16 using {command down}  -- Command + P
                end tell
            end try
        end run
        '''
        
        try:
            subprocess.run(['osascript', '-e', script], check=True)
            return True
        except Exception as e:
            import logging
            logging.error(f"恢复音频失败: {e}")
        return False
        
    def mute_other_apps(self):
        """暂停其他应用的媒体播放"""
        try:
            # 暂停所有音频播放
            if self._pause_all_audio():
                self.paused_apps.add("audio_paused")
            
        except Exception as e:
            import logging
            logging.error(f"暂停其他应用失败: {e}")
            
    def resume_other_apps(self):
        """恢复其他应用的媒体播放"""
        try:
            if "audio_paused" in self.paused_apps:
                self._resume_all_audio()
                self.paused_apps.clear()
            
        except Exception as e:
            import logging
            logging.error(f"恢复其他应用失败: {e}")
            
    def cleanup(self):
        """清理资源"""
        try:
            self.resume_other_apps()
        except Exception as e:
            import logging
            logging.error(f"清理音频管理器失败: {e}")