import pyperclip
import pyautogui

class ClipboardManager:
    @staticmethod
    def copy_to_clipboard(text):
        pyperclip.copy(text)

    @staticmethod
    def paste_to_current_app():
        pyautogui.hotkey('command', 'v')