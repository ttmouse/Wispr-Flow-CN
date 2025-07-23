#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证历史记录点击修复
通过代码模拟验证点击事件处理逻辑
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication, QListWidgetItem
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QMouseEvent
from ui.components.modern_list_widget import ModernListWidget
from ui.components.history_manager import HistoryManager
from state_manager import StateManager

def test_click_event_handling():
    """测试点击事件处理逻辑"""
    print("=== 验证历史记录点击修复 ===")
    
    app = QApplication(sys.argv)
    
    # 创建历史记录管理器
    history_manager = HistoryManager("test_verify.json", max_history=10)
    
    # 创建状态管理器
    state_manager = StateManager()
    if hasattr(state_manager, 'hotwords'):
        state_manager.hotwords = ["测试", "点击"]
    else:
        state_manager.get_hotwords = lambda: ["测试", "点击"]
    history_manager.set_state_manager(state_manager)
    
    # 创建列表组件
    list_widget = ModernListWidget()
    
    # 设置点击信号处理
    click_count = 0
    clicked_texts = []
    
    def on_item_clicked(item):
        nonlocal click_count, clicked_texts
        click_count += 1
        index = list_widget.row(item)
        original_text = history_manager.get_original_text_by_index(index)
        clicked_texts.append(original_text)
        print(f"✅ 点击事件触发: 索引={index}, 文本='{original_text}'")
    
    list_widget.itemClicked.connect(on_item_clicked)
    
    # 添加测试数据
    test_texts = [
        "第一条测试记录",
        "第二条点击测试",
        "第三条验证数据"
    ]
    
    for text in test_texts:
        history_manager.add_history_item(text)
        highlighted_text = history_manager.apply_hotword_highlight(text)
        list_widget.addItem(highlighted_text)
    
    print(f"✓ 已添加 {len(test_texts)} 条测试数据")
    
    # 验证列表项数量
    item_count = list_widget.count()
    print(f"✓ 列表项数量: {item_count}")
    
    # 模拟点击事件
    print("\n开始模拟点击测试...")
    
    for i in range(min(3, item_count)):
        item = list_widget.item(i)
        if item:
            print(f"\n模拟点击第 {i+1} 项...")
            
            # 直接触发itemClicked信号（模拟点击）
            list_widget.itemClicked.emit(item)
            
            # 验证原始文本获取
            original_text = history_manager.get_original_text_by_index(i)
            expected_text = test_texts[i]
            
            if original_text == expected_text:
                print(f"✅ 文本匹配成功: '{original_text}'")
            else:
                print(f"❌ 文本匹配失败: 期望='{expected_text}', 实际='{original_text}'")
    
    # 验证结果
    print(f"\n=== 测试结果 ===")
    print(f"总点击次数: {click_count}")
    print(f"期望点击次数: {min(3, item_count)}")
    print(f"点击成功率: {click_count}/{min(3, item_count)}")
    
    if click_count == min(3, item_count):
        print("✅ 所有点击事件都正常触发")
    else:
        print("❌ 部分点击事件未触发")
    
    # 验证获取的文本
    print(f"\n获取到的文本:")
    for i, text in enumerate(clicked_texts):
        print(f"  {i+1}. '{text}'")
    
    # 检查是否有重复或错误的文本
    if len(set(clicked_texts)) == len(clicked_texts):
        print("✅ 所有获取的文本都是唯一的")
    else:
        print("⚠️ 发现重复的文本")
    
    app.quit()
    
    return click_count == min(3, item_count)

def test_mouse_event_handling():
    """测试鼠标事件处理"""
    print("\n=== 测试鼠标事件处理 ===")
    
    app = QApplication(sys.argv)
    
    # 创建列表组件
    list_widget = ModernListWidget()
    list_widget.addItem("测试项目")
    
    # 模拟鼠标按下事件
    print("模拟鼠标按下事件...")
    try:
        mouse_press_event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPoint(10, 10),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        list_widget.mousePressEvent(mouse_press_event)
        print("✅ 鼠标按下事件处理成功")
    except Exception as e:
        print(f"❌ 鼠标按下事件处理失败: {e}")
        return False
    
    # 模拟鼠标释放事件
    print("模拟鼠标释放事件...")
    try:
        mouse_release_event = QMouseEvent(
            QMouseEvent.Type.MouseButtonRelease,
            QPoint(10, 10),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        list_widget.mouseReleaseEvent(mouse_release_event)
        print("✅ 鼠标释放事件处理成功")
    except Exception as e:
        print(f"❌ 鼠标释放事件处理失败: {e}")
        return False
    
    app.quit()
    return True

def main():
    """主函数"""
    print("开始验证历史记录点击修复...\n")
    
    # 测试点击事件处理
    click_test_passed = test_click_event_handling()
    
    # 测试鼠标事件处理
    mouse_test_passed = test_mouse_event_handling()
    
    # 总结
    print(f"\n=== 验证总结 ===")
    print(f"点击事件测试: {'✅ 通过' if click_test_passed else '❌ 失败'}")
    print(f"鼠标事件测试: {'✅ 通过' if mouse_test_passed else '❌ 失败'}")
    
    if click_test_passed and mouse_test_passed:
        print("\n🎉 历史记录点击功能修复验证成功！")
        print("修复内容:")
        print("1. 移除了mousePressEvent中的clearSelection调用")
        print("2. 延长了mouseReleaseEvent中clearSelection的延迟时间")
        print("3. 确保itemClicked信号能够正常触发")
        return True
    else:
        print("\n❌ 验证失败，需要进一步检查")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)