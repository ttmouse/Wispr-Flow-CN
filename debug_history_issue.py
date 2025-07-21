#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
历史记录添加问题诊断脚本
用于调试录音转换成功但文本未添加到历史记录的问题
"""

import sys
import os
import json
import traceback
from datetime import datetime
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, pyqtSignal, QObject

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ui.components.history_manager import HistoryManager
from ui.main_window import MainWindow
from settings_manager import SettingsManager
from state_manager import StateManager
from utils import clean_html_tags

class HistoryDebugger(QObject):
    """历史记录调试器"""
    
    def __init__(self):
        super().__init__()
        self.test_results = []
        self.setup_components()
    
    def setup_components(self):
        """设置测试组件"""
        try:
            # 创建设置管理器
            self.settings_manager = SettingsManager()
            
            # 创建状态管理器
            self.state_manager = StateManager(self.settings_manager)
            
            # 创建历史记录管理器
            self.history_manager = HistoryManager(
                history_file="test_history.json",
                state_manager=self.state_manager
            )
            
            # 创建主窗口（用于测试display_result流程）
            self.main_window = MainWindow()
            self.main_window.history_manager = self.history_manager
            
            print("✓ 测试组件初始化完成")
            
        except Exception as e:
            print(f"❌ 组件初始化失败: {e}")
            traceback.print_exc()
    
    def test_history_manager_directly(self):
        """直接测试历史记录管理器"""
        print("\n=== 测试1: 直接测试历史记录管理器 ===")
        
        test_texts = [
            "这是一个测试文本",
            "另一个测试文本",
            "重复的文本",
            "重复的文本",  # 应该被去重
            "<b>带HTML标签的文本</b>",
            "",  # 空文本
            "   ",  # 空白文本
            "转写失败，请重试",  # 错误消息
        ]
        
        for i, text in enumerate(test_texts):
            try:
                result = self.history_manager.add_history_item(text)
                status = "✓ 成功" if result else "⚠️ 跳过（重复或无效）"
                print(f"测试 {i+1}: {text[:20]}... -> {status}")
                
                self.test_results.append({
                    'test': f'direct_add_{i+1}',
                    'input': text,
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                print(f"❌ 测试 {i+1} 失败: {e}")
                self.test_results.append({
                    'test': f'direct_add_{i+1}',
                    'input': text,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        # 检查历史记录状态
        history_count = len(self.history_manager.history_items)
        print(f"\n当前历史记录数量: {history_count}")
        
        for i, item in enumerate(self.history_manager.history_items):
            print(f"  {i+1}. {item['text'][:30]}...")
    
    def test_display_result_flow(self):
        """测试display_result完整流程"""
        print("\n=== 测试2: 测试display_result完整流程 ===")
        
        test_texts = [
            "通过display_result添加的文本1",
            "通过display_result添加的文本2",
            "<b>带高亮的</b>转录结果",
        ]
        
        initial_count = len(self.history_manager.history_items)
        
        for i, text in enumerate(test_texts):
            try:
                print(f"\n测试display_result: {text}")
                
                # 模拟display_result调用
                self.main_window.display_result(text)
                
                # 检查是否添加成功
                current_count = len(self.history_manager.history_items)
                added = current_count > initial_count + i
                
                print(f"  历史记录数量变化: {initial_count + i} -> {current_count}")
                print(f"  添加状态: {'✓ 成功' if added else '❌ 失败'}")
                
                self.test_results.append({
                    'test': f'display_result_{i+1}',
                    'input': text,
                    'added': added,
                    'count_before': initial_count + i,
                    'count_after': current_count,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                print(f"❌ display_result测试失败: {e}")
                traceback.print_exc()
                self.test_results.append({
                    'test': f'display_result_{i+1}',
                    'input': text,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
    
    def test_transcription_simulation(self):
        """模拟转录完成流程"""
        print("\n=== 测试3: 模拟转录完成流程 ===")
        
        # 模拟不同的转录结果
        transcription_results = [
            "正常的转录结果",
            "另一个正常结果",
            "转写失败，请重试",  # 错误消息
            "",  # 空结果
            "<b>带格式的</b>转录结果",
        ]
        
        for i, text in enumerate(transcription_results):
            try:
                print(f"\n模拟转录结果: {text}")
                
                # 模拟on_transcription_done的逻辑
                if text and text.strip():
                    # 清理HTML标签用于剪贴板复制
                    clean_text = clean_html_tags(text)
                    print(f"  清理后的文本: {clean_text}")
                    
                    # 模拟display_result调用
                    initial_count = len(self.history_manager.history_items)
                    self.main_window.display_result(text)
                    final_count = len(self.history_manager.history_items)
                    
                    added = final_count > initial_count
                    print(f"  历史记录变化: {initial_count} -> {final_count}")
                    print(f"  添加状态: {'✓ 成功' if added else '❌ 失败'}")
                    
                    self.test_results.append({
                        'test': f'transcription_sim_{i+1}',
                        'input': text,
                        'clean_text': clean_text,
                        'added': added,
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    print("  跳过：空文本")
                    self.test_results.append({
                        'test': f'transcription_sim_{i+1}',
                        'input': text,
                        'skipped': 'empty_text',
                        'timestamp': datetime.now().isoformat()
                    })
                    
            except Exception as e:
                print(f"❌ 转录模拟测试失败: {e}")
                traceback.print_exc()
                self.test_results.append({
                    'test': f'transcription_sim_{i+1}',
                    'input': text,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
    
    def test_duplicate_detection(self):
        """测试重复检测逻辑"""
        print("\n=== 测试4: 测试重复检测逻辑 ===")
        
        # 清空历史记录
        self.history_manager.clear_history()
        
        # 添加一些基础记录
        base_texts = ["基础文本1", "基础文本2", "<b>带标签的文本</b>"]
        for text in base_texts:
            self.history_manager.add_history_item(text)
        
        print(f"基础历史记录数量: {len(self.history_manager.history_items)}")
        
        # 测试重复检测
        duplicate_tests = [
            ("基础文本1", True),  # 完全重复
            ("<b>基础文本1</b>", True),  # HTML包装的重复
            ("基础文本1 ", True),  # 带空格的重复
            ("带标签的文本", True),  # 去除HTML后重复
            ("<i>带标签的文本</i>", True),  # 不同HTML标签但内容重复
            ("全新的文本", False),  # 不重复
        ]
        
        for text, should_be_duplicate in duplicate_tests:
            existing_texts = [item['text'] for item in self.history_manager.history_items]
            is_duplicate = self.history_manager.is_duplicate_text(text, existing_texts)
            
            status = "✓" if is_duplicate == should_be_duplicate else "❌"
            print(f"  {status} '{text}' -> 重复: {is_duplicate} (期望: {should_be_duplicate})")
            
            self.test_results.append({
                'test': 'duplicate_detection',
                'input': text,
                'is_duplicate': is_duplicate,
                'expected': should_be_duplicate,
                'correct': is_duplicate == should_be_duplicate,
                'timestamp': datetime.now().isoformat()
            })
    
    def save_test_results(self):
        """保存测试结果"""
        try:
            with open('history_debug_results.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'test_time': datetime.now().isoformat(),
                    'total_tests': len(self.test_results),
                    'results': self.test_results,
                    'final_history_count': len(self.history_manager.history_items),
                    'final_history_items': self.history_manager.get_history_for_save()
                }, f, ensure_ascii=False, indent=2)
            
            print(f"\n✓ 测试结果已保存到 history_debug_results.json")
            
        except Exception as e:
            print(f"❌ 保存测试结果失败: {e}")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("开始历史记录问题诊断...")
        
        try:
            self.test_history_manager_directly()
            self.test_display_result_flow()
            self.test_transcription_simulation()
            self.test_duplicate_detection()
            
            # 统计结果
            total_tests = len(self.test_results)
            failed_tests = len([r for r in self.test_results if 'error' in r])
            
            print(f"\n=== 测试总结 ===")
            print(f"总测试数: {total_tests}")
            print(f"失败测试数: {failed_tests}")
            print(f"成功率: {((total_tests - failed_tests) / total_tests * 100):.1f}%")
            
            self.save_test_results()
            
        except Exception as e:
            print(f"❌ 测试运行失败: {e}")
            traceback.print_exc()

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    debugger = HistoryDebugger()
    
    # 使用QTimer延迟执行测试，确保Qt事件循环正常运行
    QTimer.singleShot(100, debugger.run_all_tests)
    QTimer.singleShot(5000, app.quit)  # 5秒后自动退出
    
    return app.exec()

if __name__ == '__main__':
    sys.exit(main())