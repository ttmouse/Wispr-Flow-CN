import subprocess
import sys

def check_microphone_permission():
    result = subprocess.run(["osascript", "-e", 'tell application "System Events" to tell process "SystemUIServer" to get value of attribute "AXEnabled" of UI element "Microphone"'], capture_output=True, text=True)
    return "true" in result.stdout.lower()

def check_accessibility_permission():
    result = subprocess.run(["osascript", "-e", 'tell application "System Events" to UI elements of process "Python" exists'], capture_output=True, text=True)
    return "true" in result.stdout.lower()

def main():
    mic_permission = check_microphone_permission()
    accessibility_permission = check_accessibility_permission()

    if not mic_permission or not accessibility_permission:
        print("请授予必要的权限以运行此应用程序：")
        print("1. 打开'系统偏好设置' > '安全性与隐私' > '隐私'")
        print("2. 在左侧列表中选择'麦克风'，然后在右侧勾选 Python 或您的终端应用")
        print("3. 在左侧列表中选择'辅助功能'，然后在右侧勾选 Python 或您的终端应用")
        print("4. 完成后，请重新运行此程序")
        sys.exit(1)
    else:
        print("所有必要的权限都已授予，正在启动主程序...")

if __name__ == "__main__":
    main()