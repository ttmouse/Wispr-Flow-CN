# 兼容性文件 - 保持向后兼容
# 重定向到新的模块化组件

# 导入新的模块化组件
from .modern_list_widget import ModernListWidget
from .history_item import HistoryItem, HistoryItemWidget
from .text_label import TextLabel
from .list_styles import ListStyleManager

# 为了向后兼容，保留原有的导入方式
__all__ = ['ModernListWidget', 'HistoryItem', 'HistoryItemWidget', 'TextLabel']