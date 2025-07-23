#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试历史记录点击性能优化效果
"""

import time
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from clipboard_manager import ClipboardManager

def test_clipboard_performance():
    """测试剪贴板操作性能"""
    print("开始测试剪贴板操作性能...")
    print("="*50)
    
    # 创建剪贴板管理器
    clipboard_manager = ClipboardManager(debug_mode=True)
    
    # 测试数据
    test_texts = [
        "快速响应测试 - 第1条记录",
        "零延迟测试 - 第2条记录", 
        "优化后测试 - 第3条记录",
        "性能提升测试 - 第4条记录",
        "即时反馈测试 - 第5条记录"
    ]
    
    response_times = []
    
    for i, text in enumerate(test_texts):
        print(f"\n测试 {i+1}/5: '{text}'")
        
        # 记录开始时间
        start_time = time.time()
        
        # 执行剪贴板操作
        success = clipboard_manager.safe_copy_and_paste(text)
        
        # 计算响应时间
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # 转换为毫秒
        
        if success:
            response_times.append(response_time)
            print(f"✅ 操作成功: 响应时间={response_time:.1f}ms")
        else:
            print(f"❌ 操作失败: 响应时间={response_time:.1f}ms")
        
        # 短暂延迟避免操作冲突
        time.sleep(0.1)
    
    # 显示统计结果
    if response_times:
        avg_time = sum(response_times) / len(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        
        print("\n" + "="*50)
        print("性能测试结果:")
        print(f"平均响应时间: {avg_time:.1f}ms")
        print(f"最快响应时间: {min_time:.1f}ms")
        print(f"最慢响应时间: {max_time:.1f}ms")
        print(f"成功测试次数: {len(response_times)}/5")
        print("="*50)
        
        # 性能评估
        if avg_time < 50:
            print("🎉 性能优秀！响应时间非常快")
        elif avg_time < 100:
            print("✅ 性能良好！响应时间可接受")
        elif avg_time < 200:
            print("⚠️ 性能一般，还有优化空间")
        else:
            print("❌ 性能较差，需要进一步优化")
    else:
        print("\n❌ 所有测试都失败了")

def test_individual_operations():
    """测试单独的剪贴板操作"""
    print("\n开始测试单独操作性能...")
    print("="*50)
    
    clipboard_manager = ClipboardManager(debug_mode=False)
    test_text = "性能测试文本"
    
    # 测试复制操作
    print("\n1. 测试复制操作:")
    start_time = time.time()
    copy_success = clipboard_manager.copy_to_clipboard(test_text)
    copy_time = (time.time() - start_time) * 1000
    print(f"复制操作: {'成功' if copy_success else '失败'}, 耗时: {copy_time:.1f}ms")
    
    # 测试粘贴操作
    print("\n2. 测试粘贴操作:")
    start_time = time.time()
    clipboard_manager.paste_to_current_app()
    paste_time = (time.time() - start_time) * 1000
    print(f"粘贴操作: 完成, 耗时: {paste_time:.1f}ms")
    
    # 测试获取剪贴板内容
    print("\n3. 测试获取剪贴板内容:")
    start_time = time.time()
    content = clipboard_manager.get_clipboard_content()
    get_time = (time.time() - start_time) * 1000
    print(f"获取内容: 成功, 耗时: {get_time:.1f}ms")
    print(f"内容: '{content[:30]}{'...' if len(content) > 30 else ''}'")
    
    total_time = copy_time + paste_time + get_time
    print(f"\n总操作时间: {total_time:.1f}ms")

def main():
    print("历史记录点击性能测试")
    print("测试优化后的剪贴板操作延迟")
    print("注意: 此测试会执行实际的剪贴板操作")
    
    try:
        # 测试完整的剪贴板操作
        test_clipboard_performance()
        
        # 测试单独操作
        test_individual_operations()
        
        print("\n🎯 测试完成！")
        print("如果平均响应时间显著降低，说明优化生效")
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()