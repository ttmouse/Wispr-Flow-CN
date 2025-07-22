# 历史记录管理器 - 处理历史记录的业务逻辑
# 包含保存、加载、去重和热词高亮等功能

import json
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from utils.text_utils import clean_html_tags

class HistoryManager:
    """历史记录管理器
    
    负责处理历史记录的业务逻辑，包括：
    - 历史记录的保存和加载
    - 文本去重处理
    - 热词高亮应用
    - 数据格式转换
    """
    
    def __init__(self, history_file_path: str, max_history: int = 30):
        self.history_file = history_file_path
        self.max_history = max_history
        self.state_manager = None
        self.history_items = []  # 内存中的历史记录
    
    def set_state_manager(self, state_manager):
        """设置状态管理器，用于获取热词"""
        self.state_manager = state_manager
    

    
    def apply_hotword_highlight(self, text: str) -> str:
        """应用热词高亮"""
        if not text or not self.state_manager:
            return text
        
        try:
            hotwords = self._get_hotwords()
            if not hotwords:
                return text
            
            highlighted_text = text
            # 按长度降序排列热词，避免短词覆盖长词
            sorted_hotwords = sorted(hotwords, key=len, reverse=True)
            
            for hotword in sorted_hotwords:
                if hotword and hotword.strip():
                    pattern = re.escape(hotword.strip())
                    highlighted_text = re.sub(
                        f'({pattern})',
                        r'<b>\1</b>',
                        highlighted_text,
                        flags=re.IGNORECASE
                    )
            
            return highlighted_text
        except Exception as e:
            print(f"应用热词高亮失败: {e}")
            return text
    
    def _get_hotwords(self) -> List[str]:
        """获取热词列表"""
        if hasattr(self.state_manager, 'get_hotwords'):
            return self.state_manager.get_hotwords()
        return []
    
    def is_duplicate_text(self, new_text: str, existing_texts: List[str]) -> bool:
        """检查文本是否重复"""
        clean_new_text = clean_html_tags(new_text).strip()
        
        for existing_text in existing_texts:
            clean_existing_text = clean_html_tags(existing_text).strip()
            if clean_existing_text == clean_new_text:
                return True
        return False
    
    def prepare_text_for_display(self, text: str) -> str:
        """准备用于显示的文本（应用热词高亮）"""
        # 如果文本中没有HTML标签，则应用热词高亮
        if '<' not in text:
            return self.apply_hotword_highlight(text)
        return text
    
    def save_history(self, history_items: List[Dict[str, Any]]) -> bool:
        """保存历史记录到文件"""
        try:
            # 限制历史记录数量
            limited_items = history_items[:self.max_history]
            
            # 转换为保存格式
            save_data = []
            for item in limited_items:
                if isinstance(item, dict):
                    # 清理HTML标签，保存纯文本
                    clean_text = clean_html_tags(item.get('text', ''))
                    save_data.append({
                        'text': clean_text,
                        'timestamp': item.get('timestamp', datetime.now().isoformat())
                    })
                elif isinstance(item, str):
                    # 兼容字符串格式
                    clean_text = clean_html_tags(item)
                    save_data.append({
                        'text': clean_text,
                        'timestamp': datetime.now().isoformat()
                    })
            
            # 保存到文件
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            pass
            return True
            
        except Exception as e:
            print(f"❌ 保存历史记录失败: {e}")
            return False
    
    def load_history(self) -> List[Dict[str, str]]:
        """从文件加载历史记录"""
        try:
            if not os.path.exists(self.history_file):
                pass
                return []
            
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
            
            # print(f"✓ 历史记录文件存在，包含 {len(history_data)} 条记录")
            
            if not history_data:
                pass
                return []
            
            # 处理和排序历史记录
            processed_data = self._process_loaded_data(history_data)
            return processed_data
            
        except Exception as e:
            print(f"❌ 加载历史记录失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _process_loaded_data(self, history_data: List) -> List[Dict[str, str]]:
        """处理加载的历史记录数据"""
        processed_data = []
        
        # 转换为统一格式
        for entry in history_data:
            if isinstance(entry, dict) and 'text' in entry:
                processed_data.append({
                    'text': entry['text'],
                    'timestamp': entry.get('timestamp', ''),
                    'highlighted_text': self.apply_hotword_highlight(entry['text'])
                })
            elif isinstance(entry, str):
                # 兼容旧格式
                processed_data.append({
                    'text': entry,
                    'timestamp': '',
                    'highlighted_text': self.apply_hotword_highlight(entry)
                })
        
        # 按时间戳排序（最新的在后）
        if processed_data and processed_data[0].get('timestamp'):
            processed_data.sort(key=lambda x: x.get('timestamp', ''), reverse=False)
            # print("✓ 已按时间戳排序历史记录（正序）")
        
        return processed_data
    
    def reapply_hotword_highlight(self, history_items: List[str]) -> List[str]:
        """重新应用热词高亮到历史记录项"""
        try:
            # print(f"开始重新应用热词高亮，历史记录项数量: {len(history_items)}")
            
            highlighted_items = []
            for i, text in enumerate(history_items):
                # 获取原始文本（去除HTML标签）
                original_text = clean_html_tags(text)
                # 重新应用热词高亮
                highlighted_text = self.apply_hotword_highlight(original_text)
                highlighted_items.append(highlighted_text)
                # print(f"✓ 已更新历史记录项 {i+1}: {original_text[:30]}...")
            
            pass
            return highlighted_items
            
        except Exception as e:
            print(f"❌ 重新应用热词高亮失败: {e}")
            import traceback
            print(traceback.format_exc())
            return history_items
    
    def create_history_entry(self, text: str, timestamp: Optional[str] = None) -> Dict[str, str]:
        """创建历史记录条目"""
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        return {
            'text': text,
            'timestamp': timestamp,
            'highlighted_text': self.apply_hotword_highlight(text)
        }
    
    def add_history_item(self, text: str) -> bool:
        """添加历史记录项，总是成功添加（已移除重复检测）"""
        if not text or not text.strip():
            return False
        
        # 直接添加新项目到末尾（已移除重复检测）
        new_item = self.create_history_entry(text)
        self.history_items.append(new_item)
        
        # 限制数量（删除最旧的记录）
        if len(self.history_items) > self.max_history:
            self.history_items = self.history_items[-self.max_history:]
        
        return True
    
    def get_history_texts(self) -> List[str]:
        """获取历史记录文本列表（用于UI显示）"""
        return [item.get('highlighted_text', item['text']) for item in self.history_items]
    
    def get_history_for_save(self) -> List[Dict[str, str]]:
        """获取用于保存的历史记录数据"""
        return [{
            'text': clean_html_tags(item['text']),
            'timestamp': item['timestamp']
        } for item in self.history_items]
    
    def clear_history(self):
        """清空历史记录"""
        self.history_items = []
    
    def load_history_data(self, history_data: List) -> int:
        """加载历史记录数据到内存"""
        self.clear_history()
        
        processed_data = self._process_loaded_data(history_data)
        self.history_items = processed_data
        
        return len(self.history_items)