#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热键状态稳定器
解决状态点频繁变红绿的问题
"""

import time
import logging
from typing import Dict, Any, Optional
from threading import Lock

class HotkeyStatusStabilizer:
    """热键状态稳定器，提供更稳定的状态检测"""
    
    def __init__(self, stability_window: float = 5.0, min_stable_count: int = 3):
        """
        初始化状态稳定器
        
        Args:
            stability_window: 稳定性检测窗口时间（秒）
            min_stable_count: 最小稳定检测次数
        """
        self.stability_window = stability_window
        self.min_stable_count = min_stable_count
        
        # 状态历史记录
        self.status_history = []
        self.last_stable_status = None
        self.last_check_time = 0
        
        # 线程安全锁
        self._lock = Lock()
        
        # 日志记录
        self.logger = logging.getLogger(__name__)
    
    def get_stable_status(self, hotkey_manager) -> Dict[str, Any]:
        """
        获取稳定的热键状态
        
        Args:
            hotkey_manager: 热键管理器实例
            
        Returns:
            Dict[str, Any]: 稳定的状态信息
        """
        with self._lock:
            current_time = time.time()
            
            # 获取原始状态
            try:
                raw_status = hotkey_manager.get_status() if hotkey_manager else {
                    'active': False,
                    'scheme': 'unknown',
                    'hotkey_type': 'unknown',
                    'error_count': 0,
                    'last_error': '热键管理器不存在'
                }
            except Exception as e:
                self.logger.error(f"获取热键状态失败: {e}")
                raw_status = {
                    'active': False,
                    'scheme': 'unknown',
                    'hotkey_type': 'unknown',
                    'error_count': 1,
                    'last_error': str(e)
                }
            
            # 添加时间戳
            raw_status['timestamp'] = current_time
            
            # 记录状态历史
            self.status_history.append({
                'status': raw_status,
                'timestamp': current_time
            })
            
            # 清理过期的历史记录
            cutoff_time = current_time - self.stability_window
            self.status_history = [
                entry for entry in self.status_history 
                if entry['timestamp'] > cutoff_time
            ]
            
            # 分析状态稳定性
            stable_status = self._analyze_stability()
            
            # 更新最后检查时间
            self.last_check_time = current_time
            
            return stable_status
    
    def _analyze_stability(self) -> Dict[str, Any]:
        """
        分析状态稳定性
        
        Returns:
            Dict[str, Any]: 稳定的状态
        """
        if len(self.status_history) < self.min_stable_count:
            # 历史记录不足，返回最后一个状态或默认状态
            if self.status_history:
                return self.status_history[-1]['status']
            elif self.last_stable_status:
                return self.last_stable_status
            else:
                return {
                    'active': False,
                    'scheme': 'unknown',
                    'hotkey_type': 'unknown',
                    'error_count': 0,
                    'last_error': '状态检测中...',
                    'timestamp': time.time()
                }
        
        # 统计活跃状态的频率
        active_count = sum(1 for entry in self.status_history if entry['status'].get('active', False))
        total_count = len(self.status_history)
        active_ratio = active_count / total_count
        
        # 获取最新状态作为基础
        latest_status = self.status_history[-1]['status'].copy()
        
        # 稳定性判断逻辑
        if active_ratio >= 0.7:  # 70%以上的时间是活跃的
            # 认为状态稳定为活跃
            latest_status['active'] = True
            latest_status['stability'] = 'stable_active'
            latest_status['active_ratio'] = active_ratio
        elif active_ratio <= 0.3:  # 30%以下的时间是活跃的
            # 认为状态稳定为非活跃
            latest_status['active'] = False
            latest_status['stability'] = 'stable_inactive'
            latest_status['active_ratio'] = active_ratio
        else:
            # 状态不稳定，使用上次稳定状态
            if self.last_stable_status:
                stable_status = self.last_stable_status.copy()
                stable_status['stability'] = 'unstable_using_last'
                stable_status['active_ratio'] = active_ratio
                stable_status['timestamp'] = latest_status['timestamp']
                return stable_status
            else:
                # 没有上次稳定状态，保持当前状态但标记为不稳定
                latest_status['stability'] = 'unstable_no_history'
                latest_status['active_ratio'] = active_ratio
        
        # 更新最后稳定状态
        if latest_status.get('stability', '').startswith('stable_'):
            self.last_stable_status = latest_status.copy()
        
        return latest_status
    
    def reset(self):
        """重置稳定器状态"""
        with self._lock:
            self.status_history.clear()
            self.last_stable_status = None
            self.last_check_time = 0
    
    def get_debug_info(self) -> Dict[str, Any]:
        """获取调试信息"""
        with self._lock:
            return {
                'history_count': len(self.status_history),
                'stability_window': self.stability_window,
                'min_stable_count': self.min_stable_count,
                'last_check_time': self.last_check_time,
                'has_stable_status': self.last_stable_status is not None,
                'active_threshold': 0.7,
                'inactive_threshold': 0.3,
                'recent_statuses': [
                    {
                        'active': entry['status'].get('active', False),
                        'timestamp': entry['timestamp']
                    }
                    for entry in self.status_history[-5:]  # 最近5个状态
                ]
            }


def create_status_stabilizer() -> HotkeyStatusStabilizer:
    """创建状态稳定器实例"""
    return HotkeyStatusStabilizer(
        stability_window=8.0,  # 8秒稳定窗口
        min_stable_count=4     # 至少4次检测
    )


if __name__ == "__main__":
    # 测试代码
    import sys
    import os
    
    # 添加src目录到路径
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("热键状态稳定器测试")
    print("=" * 50)
    
    # 创建稳定器
    stabilizer = create_status_stabilizer()
    
    # 模拟状态检测
    class MockHotkeyManager:
        def __init__(self):
            self.call_count = 0
        
        def get_status(self):
            self.call_count += 1
            # 模拟不稳定的状态
            if self.call_count % 3 == 0:
                return {'active': False, 'scheme': 'test', 'hotkey_type': 'fn'}
            else:
                return {'active': True, 'scheme': 'test', 'hotkey_type': 'fn'}
    
    mock_manager = MockHotkeyManager()
    
    # 进行多次状态检测
    for i in range(10):
        status = stabilizer.get_stable_status(mock_manager)
        print(f"检测 {i+1}: active={status.get('active')}, stability={status.get('stability', 'N/A')}")
        time.sleep(0.5)
    
    # 显示调试信息
    debug_info = stabilizer.get_debug_info()
    print("\n调试信息:")
    for key, value in debug_info.items():
        print(f"  {key}: {value}")