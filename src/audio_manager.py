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
        """暂停所有音频播放"""
        script = '''
        on run
            set didPause to false
            
            -- 获取系统音量
            set originalVolume to output volume of (get volume settings)
            
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
            
            -- 暂停 Chrome
            try
                tell application "Google Chrome"
                    tell active tab of front window
                        execute javascript "
                            const audios = document.querySelectorAll('audio, video');
                            let paused = false;
                            audios.forEach(a => {
                                if (!a.paused) {
                                    a.pause();
                                    paused = true;
                                }
                            });
                            if (paused) { return 'true'; }
                            return 'false';
                        "
                        if result is "true" then
                            set didPause to true
                        end if
                    end tell
                end tell
            end try
            
            -- 暂停 Safari
            try
                tell application "Safari"
                    tell current tab of front window
                        do JavaScript "
                            const audios = document.querySelectorAll('audio, video');
                            let paused = false;
                            audios.forEach(a => {
                                if (!a.paused) {
                                    a.pause();
                                    paused = true;
                                }
                            });
                            if (paused) { return 'true'; }
                            return 'false';
                        "
                        if result is "true" then
                            set didPause to true
                        end if
                    end tell
                end tell
            end try
            
            -- 暂停 QQ音乐
            try
                tell application "QQMusic"
                    if player state is playing then
                        pause
                        set didPause to true
                    end if
                end tell
            end try
            
            -- 暂停网易云音乐
            try
                tell application "NeteaseMusic"
                    if player state is playing then
                        pause
                        set didPause to true
                    end if
                end tell
            end try
            
            -- 暂停其他可能的音频源
            try
                tell application "System Events"
                    set frontApp to name of first application process whose frontmost is true
                    if frontApp is not in {"Music", "Spotify", "Google Chrome", "Safari", "QQMusic", "NeteaseMusic"} then
                        -- 尝试发送通用的媒体按键
                        key code 16 using {command down}  -- Command + P，通用的播放/暂停快捷键
                        set didPause to true
                    end if
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
        """恢复所有音频播放"""
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
            
            -- 恢复 Chrome
            try
                tell application "Google Chrome"
                    tell active tab of front window
                        execute javascript "
                            const audios = document.querySelectorAll('audio, video');
                            audios.forEach(a => a.play());
                        "
                    end tell
                end tell
            end try
            
            -- 恢复 Safari
            try
                tell application "Safari"
                    tell current tab of front window
                        do JavaScript "
                            const audios = document.querySelectorAll('audio, video');
                            audios.forEach(a => a.play());
                        "
                    end tell
                end tell
            end try
            
            -- 恢复 QQ音乐
            try
                tell application "QQMusic"
                    play
                end tell
            end try
            
            -- 恢复网易云音乐
            try
                tell application "NeteaseMusic"
                    play
                end tell
            end try
            
            -- 恢复其他可能的音频源
            try
                tell application "System Events"
                    set frontApp to name of first application process whose frontmost is true
                    if frontApp is not in {"Music", "Spotify", "Google Chrome", "Safari", "QQMusic", "NeteaseMusic"} then
                        -- 尝试发送通用的媒体按键
                        key code 16 using {command down}  -- Command + P，通用的播放/暂停快捷键
                    end if
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