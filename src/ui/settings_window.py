from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QComboBox, QGroupBox, QWidget, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor
import logging

# 配置日志记录
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SettingsWindow(QDialog):
    save_button_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("SettingsWindow __init__ 开始")
        self.setWindowTitle("设置")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.setup_ui()
        logger.info("SettingsWindow __init__ 完成")

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)

        # 标题
        title_label = QLabel("设置")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # 模型信息
        self.model_path_label = self.create_label("未知")
        model_group = self.create_group("模型信息", [
            ("模型路径", self.model_path_label)
        ])
        layout.addWidget(model_group)

        # 权限设置
        self.mic_permission_label = self.create_permission_label("麦克风权限")
        self.hotkey_permission_label = self.create_permission_label("支持快捷键")
        self.accessibility_permission_label = self.create_permission_label("辅助功能权限")
        permissions_group = self.create_group("权限设置", [
            ("麦克风权限", self.mic_permission_label),
            ("支持快捷键", self.hotkey_permission_label),
            ("辅助功能权限", self.accessibility_permission_label)
        ])
        layout.addWidget(permissions_group)

        # 快捷键设置
        hotkey_group = self.create_group("快捷键设置", [
            ("全局快捷键", self.create_hotkey_widget())
        ])
        layout.addWidget(hotkey_group)

        # 保存按钮
        self.save_button = QPushButton("保存设置")
        self.save_button.clicked.connect(self.on_save_button_clicked)
        layout.addWidget(self.save_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)

    def create_group(self, title, items):
        group = QGroupBox(title)
        layout = QVBoxLayout()
        for item_title, widget in items:
            item_layout = QHBoxLayout()
            item_layout.addWidget(QLabel(item_title), 1)
            item_layout.addWidget(widget, 2)
            layout.addLayout(item_layout)
        group.setLayout(layout)
        return group

    def create_label(self, text):
        label = QLabel(text)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        return label

    def create_permission_label(self, permission_name):
        label = QLabel("未授权")
        label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        label.mousePressEvent = lambda event: self.open_system_settings(permission_name)
        return label

    def create_hotkey_widget(self):
        self.hotkey_combo = QComboBox()
        hotkey_options = [
            "Ctrl+Alt+S",
            "Cmd+Shift+S",
            "Ctrl+Shift+D",
            "Alt+F2",
            "Cmd+Option+R",
            "Ctrl + Alt + S",  # 添加带空格的版本
            "Cmd + Shift + S",
            "Ctrl + Shift + D",
            "Alt + F2",
            "Cmd + Option + R"
        ]
        self.hotkey_combo.addItems(hotkey_options)
        return self.hotkey_combo

    def on_save_button_clicked(self):
        new_hotkey = self.hotkey_combo.currentText()
        logger.info(f"用户选择的快捷键: {new_hotkey}")
        self.save_button_clicked.emit(new_hotkey)

    def update_model_info(self, model_path):
        if self.model_path_label:
            self.model_path_label.setText(model_path)
        else:
            logger.warning("模型路径标签不存在")

    def update_permissions(self):
        try:
            from permissions import check_microphone_permission, check_accessibility_permission, check_hotkey_permission
            mic_enabled = check_microphone_permission()
            hotkey_enabled = check_hotkey_permission()
            accessibility_enabled = check_accessibility_permission()
            
            self.update_permission_label(self.mic_permission_label, mic_enabled)
            self.update_permission_label(self.hotkey_permission_label, hotkey_enabled)
            self.update_permission_label(self.accessibility_permission_label, accessibility_enabled)
        except Exception as e:
            logger.error(f"更新权限状态时出错: {e}", exc_info=True)
            QMessageBox.warning(self, "权限检查错误", f"检查权限状态时发生错误：{str(e)}")

    def update_permission_label(self, label, enabled):
        if label:
            if enabled:
                label.setText("已授权")
            else:
                label.setText("未授权")
        else:
            logger.warning(f"未找到权限标签")

    def open_system_settings(self, permission_name):
        try:
            from permissions import open_system_settings
            open_system_settings(permission_name)
        except Exception as e:
            logger.error(f"打开系统设置时出错: {e}", exc_info=True)
            QMessageBox.warning(self, "打开设置错误", f"无法打开系统设置：{str(e)}")

    def set_hotkey(self, hotkey):
        # 移除多余的空格并标准化格式
        normalized_hotkey = '+'.join(part.strip() for part in hotkey.split('+'))
        index = self.hotkey_combo.findText(normalized_hotkey, Qt.MatchFlag.MatchFixedString)
        if index >= 0:
            self.hotkey_combo.setCurrentIndex(index)
            logger.info(f"设置快捷键下拉框为: {normalized_hotkey}")
        else:
            logger.warning(f"未找到匹配的快捷键选项: {hotkey}")
            # 如果没有找到完全匹配的选项，尝试添加新选项
            self.hotkey_combo.addItem(normalized_hotkey)
            self.hotkey_combo.setCurrentIndex(self.hotkey_combo.count() - 1)
            logger.info(f"添加并设置新的快捷键选项: {normalized_hotkey}")

    def get_hotkey(self):
        return self.hotkey_combo.currentText()