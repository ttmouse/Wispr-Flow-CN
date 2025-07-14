import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

class SettingsManager:
    # 默认设置
    DEFAULT_SETTINGS = {
        'hotkey': 'fn',              # 快捷键设置：fn, ctrl, alt
        'high_frequency_words': [],   # 高频词列表
        'audio': {
            'input_device': None,     # 输入设备名称，None表示系统默认
            'volume_threshold': 150,   # 音量阈值：0-1000，对应实际阈值0-0.02，默认值150对应0.003
            'max_recording_duration': 10,  # 最大录音时长（秒），默认10秒
        },
        'asr': {
            'model_path': '',          # ASR模型路径
            'punc_model_path': '',     # 标点符号模型路径
            'auto_punctuation': True,  # 自动添加标点
            'real_time_display': True, # 实时显示识别结果
            'hotword_weight': 80,      # 热词权重 (0-100)
            'enable_pronunciation_correction': True,  # 启用发音相似词纠错
        },
        'cache': {
            'permissions': {
                'last_check': '',      # 上次权限检查时间
                'accessibility': False, # 辅助功能权限状态
                'microphone': False,   # 麦克风权限状态
                'check_interval_hours': 24,  # 检查间隔（小时）
            },
            'models': {
                'last_check': '',      # 上次模型检查时间
                'asr_available': False, # ASR模型可用状态
                'punc_available': False, # 标点模型可用状态
                'check_interval_hours': 168,  # 检查间隔（小时，7天）
            }
        }
    }

    def __init__(self):
        self.settings = {}
        self.settings_file = 'settings.json'
        self.settings_history_dir = 'settings_history'
        self.max_history_files = 10  # 最多保留10个历史版本
        self.logger = logging.getLogger('SettingsManager')
        self._ensure_history_dir()
        self.load_settings()

    def load_settings(self) -> None:
        """加载设置"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    # 合并加载的设置和默认设置
                    self.settings = self._merge_settings(self.DEFAULT_SETTINGS, loaded_settings)
            else:
                self.settings = self.DEFAULT_SETTINGS.copy()
                self.save_settings()  # 保存默认设置
        except Exception as e:
            self.logger.error(f"加载设置失败: {e}")
            self.settings = self.DEFAULT_SETTINGS.copy()

    def _ensure_history_dir(self) -> None:
        """确保历史记录目录存在"""
        if not os.path.exists(self.settings_history_dir):
            try:
                os.makedirs(self.settings_history_dir)
            except Exception as e:
                self.logger.error(f"创建历史记录目录失败: {e}")
    
    def _save_to_history(self) -> bool:
        """保存当前设置到历史记录"""
        try:
            if not os.path.exists(self.settings_file):
                return True  # 没有现有文件，无需保存历史
            
            # 生成带时间戳的历史文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            history_file = os.path.join(self.settings_history_dir, f"settings_{timestamp}.json")
            
            # 复制当前设置文件到历史目录
            import shutil
            shutil.copy2(self.settings_file, history_file)
            
            # 清理旧的历史文件
            self._cleanup_old_history()
            
            self.logger.info(f"设置历史已保存: {history_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存设置历史失败: {e}")
            return False
    
    def _cleanup_old_history(self) -> None:
        """清理过多的历史文件"""
        try:
            if not os.path.exists(self.settings_history_dir):
                return
            
            # 获取所有历史文件并按时间排序
            history_files = []
            for filename in os.listdir(self.settings_history_dir):
                if filename.startswith('settings_') and filename.endswith('.json'):
                    filepath = os.path.join(self.settings_history_dir, filename)
                    if os.path.isfile(filepath):
                        history_files.append((filepath, os.path.getmtime(filepath)))
            
            # 按修改时间排序（最新的在前）
            history_files.sort(key=lambda x: x[1], reverse=True)
            
            # 删除超出限制的文件
            for filepath, _ in history_files[self.max_history_files:]:
                try:
                    os.remove(filepath)
                    self.logger.info(f"已删除旧的历史文件: {filepath}")
                except Exception as e:
                    self.logger.error(f"删除历史文件失败 {filepath}: {e}")
                    
        except Exception as e:
            self.logger.error(f"清理历史文件失败: {e}")
    
    def save_settings(self) -> bool:
        """保存设置到文件，包含备份、历史记录和恢复机制"""
        backup_file = f"{self.settings_file}.backup"
        temp_file = f"{self.settings_file}.tmp"
        
        try:
            # 保存到历史记录
            self._save_to_history()
            
            # 如果原文件存在，先创建备份
            if os.path.exists(self.settings_file):
                import shutil
                shutil.copy2(self.settings_file, backup_file)
            
            # 先写入临时文件
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            
            # 验证临时文件是否有效
            with open(temp_file, 'r', encoding='utf-8') as f:
                json.load(f)  # 验证JSON格式
            
            # 原子性替换
            if os.path.exists(self.settings_file):
                os.remove(self.settings_file)
            os.rename(temp_file, self.settings_file)
            
            self.logger.info("设置保存成功")
            return True
            
        except Exception as e:
            self.logger.error(f"保存设置失败: {e}")
            
            # 清理临时文件
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            
            # 尝试从备份恢复
            if os.path.exists(backup_file):
                try:
                    import shutil
                    shutil.copy2(backup_file, self.settings_file)
                    self.logger.info("已从备份恢复设置文件")
                except Exception as restore_error:
                    self.logger.error(f"从备份恢复失败: {restore_error}")
            
            return False

    def get_setting(self, key: str, default: Any = None) -> Any:
        """获取设置值"""
        try:
            # 支持使用点号访问嵌套设置，如 'audio.volume_threshold'
            keys = key.split('.')
            value = self.settings
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set_setting(self, key: str, value: Any, auto_save: bool = True) -> bool:
        """设置值
        
        Args:
            key: 设置键名，支持点号分隔的嵌套键
            value: 设置值
            auto_save: 是否自动保存到文件，默认True
        """
        try:
            # 支持使用点号设置嵌套设置
            keys = key.split('.')
            target = self.settings
            
            # 确保所有中间键都存在
            for k in keys[:-1]:
                if k not in target:
                    target[k] = {}
                elif not isinstance(target[k], dict):
                    # 如果中间键不是字典，创建新的字典
                    target[k] = {}
                target = target[k]
            
            # 设置最终值
            target[keys[-1]] = value
            
            if auto_save:
                return self.save_settings()
            return True
        except Exception as e:
            self.logger.error(f"设置值失败 {key}: {e}")
            import traceback
            self.logger.error(f"设置值错误详情: {traceback.format_exc()}")
            return False

    def get_hotkey(self) -> str:
        """获取当前快捷键设置"""
        return self.get_setting('hotkey', 'fn')

    def set_hotkey(self, hotkey: str) -> bool:
        """设置快捷键"""
        return self.set_setting('hotkey', hotkey)
    
    def set_multiple_settings(self, settings_dict: Dict[str, Any]) -> bool:
        """批量设置多个配置项
        
        Args:
            settings_dict: 设置字典，键为设置名，值为设置值
            
        Returns:
            bool: 所有设置是否成功保存
        """
        try:
            # 先设置所有值但不保存
            for key, value in settings_dict.items():
                if not self.set_setting(key, value, auto_save=False):
                    self.logger.error(f"设置 {key} 失败")
                    return False
            
            # 最后一次性保存所有设置
            return self.save_settings()
            
        except Exception as e:
            self.logger.error(f"批量设置失败: {e}")
            return False

    def get_high_frequency_words(self) -> List[str]:
        """获取高频词列表"""
        return self.get_setting('high_frequency_words', [])

    def set_high_frequency_words(self, words: List[str]) -> bool:
        """设置高频词列表"""
        return self.set_setting('high_frequency_words', words)

    def _merge_settings(self, default: Dict, loaded: Dict) -> Dict:
        """递归合并设置，确保所有默认键都存在"""
        result = default.copy()
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_settings(result[key], value)
            else:
                result[key] = value
        return result

    def reset_to_defaults(self) -> bool:
        """重置所有设置为默认值"""
        self.settings = self.DEFAULT_SETTINGS.copy()
        return self.save_settings()

    def get_all_settings(self) -> Dict:
        """获取所有设置"""
        return self.settings.copy()

    def get_model_paths(self):
        """获取模型路径设置"""
        return {
            'asr_model_path': self.get_setting('asr.model_path', ''),
            'punc_model_path': self.get_setting('asr.punc_model_path', '')
        }

    def update_model_paths(self, paths):
        """更新模型路径设置"""
        success = True
        if 'asr_model_path' in paths:
            success &= self.set_setting('asr.model_path', paths['asr_model_path'])
        if 'punc_model_path' in paths:
            success &= self.set_setting('asr.punc_model_path', paths['punc_model_path'])
        return success

    def is_cache_expired(self, cache_type: str) -> bool:
        """检查缓存是否过期
        
        Args:
            cache_type: 缓存类型，'permissions' 或 'models'
        
        Returns:
            bool: True表示缓存已过期或不存在，需要重新检查
        """
        try:
            last_check = self.get_setting(f'cache.{cache_type}.last_check', '')
            if not last_check:
                return True
            
            interval_hours = self.get_setting(f'cache.{cache_type}.check_interval_hours', 24)
            last_check_time = datetime.fromisoformat(last_check)
            expiry_time = last_check_time + timedelta(hours=interval_hours)
            
            return datetime.now() > expiry_time
        except Exception as e:
            self.logger.error(f"检查缓存过期状态失败 {cache_type}: {e}")
            return True

    def update_permissions_cache(self, accessibility: bool, microphone: bool) -> bool:
        """更新权限缓存状态"""
        try:
            now = datetime.now().isoformat()
            success = True
            success &= self.set_setting('cache.permissions.last_check', now)
            success &= self.set_setting('cache.permissions.accessibility', accessibility)
            success &= self.set_setting('cache.permissions.microphone', microphone)
            return success
        except Exception as e:
            self.logger.error(f"更新权限缓存失败: {e}")
            return False

    def update_models_cache(self, asr_available: bool, punc_available: bool) -> bool:
        """更新模型缓存状态"""
        try:
            now = datetime.now().isoformat()
            success = True
            success &= self.set_setting('cache.models.last_check', now)
            success &= self.set_setting('cache.models.asr_available', asr_available)
            success &= self.set_setting('cache.models.punc_available', punc_available)
            return success
        except Exception as e:
            self.logger.error(f"更新模型缓存失败: {e}")
            return False

    def get_permissions_cache(self) -> Dict[str, bool]:
        """获取权限缓存状态"""
        return {
            'accessibility': self.get_setting('cache.permissions.accessibility', False),
            'microphone': self.get_setting('cache.permissions.microphone', False)
        }
    
    def get_hotword_weight(self) -> int:
        """获取热词权重"""
        return self.get_setting('asr.hotword_weight', 80)
    
    def set_hotword_weight(self, weight: int) -> bool:
        """设置热词权重"""
        return self.set_setting('asr.hotword_weight', weight)
    
    def get_pronunciation_correction_enabled(self) -> bool:
        """获取发音纠错启用状态"""
        return self.get_setting('asr.enable_pronunciation_correction', True)
    
    def set_pronunciation_correction_enabled(self, enabled: bool) -> bool:
        """设置发音纠错启用状态"""
        return self.set_setting('asr.enable_pronunciation_correction', enabled)

    def get_models_cache(self) -> Dict[str, bool]:
        """获取模型缓存状态"""
        return {
            'asr_available': self.get_setting('cache.models.asr_available', False),
            'punc_available': self.get_setting('cache.models.punc_available', False)
        }
    
    def get_settings_history(self) -> List[Dict[str, Any]]:
        """获取设置历史记录列表
        
        Returns:
            List[Dict]: 历史记录列表，每个元素包含 {'filename', 'timestamp', 'readable_time'}
        """
        history_list = []
        
        try:
            if not os.path.exists(self.settings_history_dir):
                return history_list
            
            for filename in os.listdir(self.settings_history_dir):
                if filename.startswith('settings_') and filename.endswith('.json'):
                    filepath = os.path.join(self.settings_history_dir, filename)
                    if os.path.isfile(filepath):
                        # 从文件名提取时间戳
                        timestamp_str = filename.replace('settings_', '').replace('.json', '')
                        try:
                            timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                            readable_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                            
                            history_list.append({
                                'filename': filename,
                                'filepath': filepath,
                                'timestamp': timestamp,
                                'readable_time': readable_time
                            })
                        except ValueError:
                            # 跳过无法解析时间戳的文件
                            continue
            
            # 按时间排序（最新的在前）
            history_list.sort(key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"获取设置历史失败: {e}")
        
        return history_list
    
    def restore_from_history(self, history_filename: str) -> bool:
        """从历史记录恢复设置
        
        Args:
            history_filename: 历史文件名
            
        Returns:
            bool: 恢复是否成功
        """
        try:
            history_filepath = os.path.join(self.settings_history_dir, history_filename)
            
            if not os.path.exists(history_filepath):
                self.logger.error(f"历史文件不存在: {history_filepath}")
                return False
            
            # 读取历史设置
            with open(history_filepath, 'r', encoding='utf-8') as f:
                historical_settings = json.load(f)
            
            # 验证设置格式
            if not isinstance(historical_settings, dict):
                self.logger.error("历史设置格式无效")
                return False
            
            # 保存当前设置到历史（作为恢复前的备份）
            self._save_to_history()
            
            # 合并历史设置和默认设置
            self.settings = self._merge_settings(self.DEFAULT_SETTINGS, historical_settings)
            
            # 保存恢复的设置
            if self.save_settings():
                self.logger.info(f"已从历史记录恢复设置: {history_filename}")
                return True
            else:
                self.logger.error("保存恢复的设置失败")
                return False
                
        except Exception as e:
            self.logger.error(f"从历史记录恢复设置失败: {e}")
            return False
    
    def export_settings(self, export_path: str) -> bool:
        """导出当前设置到指定文件
        
        Args:
            export_path: 导出文件路径
            
        Returns:
            bool: 导出是否成功
        """
        try:
            # 添加导出信息
            export_data = {
                'export_info': {
                    'timestamp': datetime.now().isoformat(),
                    'version': '1.0',
                    'description': 'Dou-flow 设置导出文件'
                },
                'settings': self.settings
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"设置已导出到: {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出设置失败: {e}")
            return False
    
    def import_settings(self, import_path: str) -> bool:
        """从文件导入设置
        
        Args:
            import_path: 导入文件路径
            
        Returns:
            bool: 导入是否成功
        """
        try:
            if not os.path.exists(import_path):
                self.logger.error(f"导入文件不存在: {import_path}")
                return False
            
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # 检查是否是导出格式
            if isinstance(import_data, dict) and 'settings' in import_data:
                imported_settings = import_data['settings']
            else:
                # 假设是直接的设置文件
                imported_settings = import_data
            
            if not isinstance(imported_settings, dict):
                self.logger.error("导入文件格式无效")
                return False
            
            # 保存当前设置到历史
            self._save_to_history()
            
            # 合并导入的设置和默认设置
            self.settings = self._merge_settings(self.DEFAULT_SETTINGS, imported_settings)
            
            # 保存导入的设置
            if self.save_settings():
                self.logger.info(f"已导入设置: {import_path}")
                return True
            else:
                self.logger.error("保存导入的设置失败")
                return False
                
        except Exception as e:
            self.logger.error(f"导入设置失败: {e}")
            return False