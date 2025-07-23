from PyQt6.QtCore import QObject, pyqtSignal
from pynput import keyboard
import traceback

class GlobalHotkeyManager(QObject):
    """全局热键管理器"""
    hotkey_triggered = pyqtSignal()  # 热键触发信号

    def __init__(self):
        super().__init__()
        self.pressed_keys = set()
        self.keyboard_listener = None

    def setup(self):
        """设置全局快捷键"""
        try:
            def on_press(key):
                try:
                    # 记录按下的键
                    if key == keyboard.Key.cmd:
                        self.pressed_keys.add('cmd')
                    elif hasattr(key, 'char') and key.char == '.':
                        self.pressed_keys.add('.')
                    
                    # 检查组合键
                    if 'cmd' in self.pressed_keys and '.' in self.pressed_keys:
                        # 发出热键触发信号
                        self.hotkey_triggered.emit()
                except Exception as e:
                    import logging
                    logging.error(f"处理按键事件失败: {e}")
                    logging.debug(traceback.format_exc())
            
            def on_release(key):
                try:
                    # 移除释放的键
                    if key == keyboard.Key.cmd:
                        self.pressed_keys.discard('cmd')
                    elif hasattr(key, 'char') and key.char == '.':
                        self.pressed_keys.discard('.')
                except Exception as e:
                    import logging
                    logging.error(f"处理按键释放事件失败: {e}")
                    logging.debug(traceback.format_exc())

            # 启动监听器
            self.keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
            self.keyboard_listener.daemon = True  # 设置为守护线程
            self.keyboard_listener.start()
            pass  # 全局快捷键已注册
        except Exception as e:
            import logging
            logging.error(f"设置全局快捷键失败: {e}")
            logging.debug(traceback.format_exc())

    def cleanup(self):
        """清理资源"""
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None