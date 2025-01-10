from pynput import keyboard
import subprocess

def control_media(action="pause"):
    """使用多种方式尝试控制媒体播放"""
    print(f"\n尝试{action}媒体播放...")
    
    commands = [
        # 方法1: 使用 Play/Pause 媒体键
        f"""osascript -e 'tell application "System Events" to key code 100'""",
        
        # 方法2: 使用 Command + Option + P 快捷键
        f"""osascript -e 'tell application "System Events" to keystroke "p" using {{command down, option down}}'""",
        
        # 方法3: 使用 NowPlaying 命令
        f"""osascript -e '
            tell application "System Events"
                set activeApp to first application process whose frontmost is true
                tell process "ControlCenter"
                    try
                        click button "{action}" of group 1 of group 1 of window 1
                    end try
                end tell
            end tell'""",
        
        # 方法4: 使用空格键模拟播放/暂停
        f"""osascript -e 'tell application "System Events" to keystroke space'""",
        
        # 方法5: 直接发送媒体控制命令
        f"""osascript -e '
            tell application "System Events"
                tell application process "Music"
                    if exists then
                        {action}
                    end if
                end tell
                tell application process "Spotify"
                    if exists then
                        {action}
                    end if
                end tell
            end tell'"""
    ]
    
    for i, cmd in enumerate(commands, 1):
        try:
            print(f"尝试方法 {i}...")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.stderr:
                print(f"方法 {i} 错误: {result.stderr}")
            else:
                print(f"方法 {i} 已执行")
        except Exception as e:
            print(f"方法 {i} 执行失败: {e}")

def on_press(key):
    try:
        if key == keyboard.Key.alt:
            print("\n按下 Option 键")
            control_media("pause")
    except AttributeError:
        pass

def on_release(key):
    try:
        if key == keyboard.Key.alt:
            print("\n释放 Option 键")
            control_media("play")
    except AttributeError:
        pass

print("=== 媒体控制脚本启动 ===")
print("按住 Option 键暂停系统媒体播放")
print("释放 Option 键恢复播放")
print("按 Ctrl+C 退出程序")

with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join() 