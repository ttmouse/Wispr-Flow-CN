"""
转写管理器包装器 - 第8步减法重构
将Application类中的转写和剪贴板相关方法迁移到此处
"""
import logging
import time
from PyQt6.QtCore import QTimer


class TranscriptionManagerWrapper:
    """转写管理器包装器 - 纯粹的方法迁移，不改变任何逻辑"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("转写管理器包装器创建成功")
    
    def paste_and_reactivate(self, app_instance, text):
        """执行粘贴操作 - 从Application类移过来"""
        try:
            # 检查剪贴板管理器是否已初始化
            if not app_instance.clipboard_manager:
                return

            # 使用安全的复制粘贴方法，确保完全替换剪贴板内容
            success = app_instance.clipboard_manager.safe_copy_and_paste(text)
            if not success:
                logging.warning("安全粘贴操作失败")

        except Exception as e:
            logging.error(f"粘贴操作失败: {e}")
            import traceback
            logging.error(traceback.format_exc())
    
    def paste_and_reactivate_with_feedback(self, app_instance, text):
        """执行粘贴操作并返回成功状态 - 从Application类移过来"""
        try:
            # 检查剪贴板管理器是否已初始化
            if not app_instance.clipboard_manager:
                return False

            # 检查文本是否有效
            if not text or not text.strip():
                return False

            # 使用安全的复制粘贴方法，确保完全替换剪贴板内容
            success = app_instance.clipboard_manager.safe_copy_and_paste(text)
            return success

        except Exception as e:
            logging.error(f"粘贴操作异常: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return False
    
    def on_transcription_done(self, app_instance, text):
        """转写完成的回调 - 从Application类移过来"""
        if text and text.strip():
            # 调试模式：显示转录完成信息

            # 1. 通过update_ui_signal更新UI并添加到历史记录（保持原始逻辑）
            app_instance.update_ui_signal.emit("转录完成", text)

            # 2. 使用可配置的延迟时间，用lambda函数捕获当前文本
            delay = app_instance.settings_manager.get_setting('paste.transcription_delay', 30)
            QTimer.singleShot(delay, lambda: app_instance._paste_and_reactivate(text))

            # 转录完成
    
    def on_history_item_clicked(self, app_instance, text):
        """处理历史记录点击事件 - 从Application类移过来"""
        try:
            # 检查文本是否有效
            if not text or not text.strip():
                # 只更新状态，不传递文本内容避免添加到历史记录
                app_instance.main_window.update_status("点击失败")
                return

            # 1. 立即更新UI反馈（只更新状态，不传递文本）
            app_instance.main_window.update_status("正在处理历史记录点击...")

            # 2. 检查剪贴板管理器是否可用
            if not app_instance.clipboard_manager:
                app_instance.main_window.update_status("点击失败")
                return

            # 3. 检查是否启用自动粘贴
            auto_paste_enabled = app_instance.settings_manager.get_setting('paste.auto_paste_enabled', True)

            if auto_paste_enabled:
                # 使用极短延迟或立即执行粘贴（_paste_and_reactivate内部会处理复制）
                delay = app_instance.settings_manager.get_setting('paste.history_click_delay', 0)  # 默认无延迟
                if delay <= 0:
                    # 立即执行粘贴
                    success = app_instance._paste_and_reactivate_with_feedback(text)
                    if success:
                        app_instance.main_window.update_status("历史记录已粘贴")
                    else:
                        app_instance.main_window.update_status("粘贴失败")
                else:
                    # 使用lambda函数捕获当前文本，避免变量覆盖问题
                    QTimer.singleShot(delay, lambda: app_instance._paste_and_reactivate_with_feedback(text))
            else:
                # 如果不自动粘贴，只复制到剪贴板
                success = app_instance.clipboard_manager.copy_to_clipboard(text)
                if success:
                    app_instance.main_window.update_status("历史记录已复制")
                else:
                    app_instance.main_window.update_status("复制失败")

        except Exception as e:
            logging.error(f"处理历史记录点击事件失败: {e}")
            import traceback
            logging.error(traceback.format_exc())
            app_instance.main_window.update_status("点击处理出错")
    
    def get_status(self):
        """获取管理器状态"""
        return {
            'name': 'TranscriptionManagerWrapper',
            'description': '转写管理器包装器'
        }
