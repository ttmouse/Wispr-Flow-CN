#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双热键方案测试脚本
用于测试Hammerspoon和Python两种热键方案的切换功能
"""

import sys
import os
import time
import logging
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from settings_manager import SettingsManager
from hotkey_manager_factory import HotkeyManagerFactory

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class DualHotkeyTester:
    """双热键方案测试器"""
    
    def __init__(self):
        self.settings_manager = SettingsManager()
        self.current_manager = None
        self.test_results = []
        
    def log(self, message):
        """记录日志"""
        print(f"[{time.strftime('%H:%M:%S')}] {message}")
        logging.info(message)
        
    def test_scheme_availability(self):
        """测试方案可用性"""
        self.log("=== 测试方案可用性 ===")
        
        available_schemes = HotkeyManagerFactory.get_available_schemes()
        self.log(f"可用方案: {available_schemes}")
        
        for scheme in ['hammerspoon', 'python']:
            is_available = HotkeyManagerFactory.is_scheme_available(scheme)
            self.log(f"{scheme}方案可用性: {is_available}")
            
            scheme_info = HotkeyManagerFactory.get_scheme_info(scheme)
            self.log(f"{scheme}方案信息: {scheme_info['name']} - {scheme_info['description']}")
            
        return available_schemes
    
    def test_scheme_creation(self, scheme):
        """测试方案创建"""
        self.log(f"=== 测试{scheme}方案创建 ===")
        
        try:
            manager = HotkeyManagerFactory.create_hotkey_manager(scheme, self.settings_manager)
            if manager:
                self.log(f"✓ {scheme}方案创建成功")
                
                # 设置回调函数
                manager.set_press_callback(self.on_hotkey_press)
                manager.set_release_callback(self.on_hotkey_release)
                
                # 测试状态获取
                status = manager.get_status()
                self.log(f"状态信息: {status}")
                
                return manager
            else:
                self.log(f"❌ {scheme}方案创建失败")
                return None
                
        except Exception as e:
            self.log(f"❌ {scheme}方案创建异常: {e}")
            return None
    
    def test_scheme_switching(self):
        """测试方案切换"""
        self.log("=== 测试方案切换 ===")
        
        schemes = ['hammerspoon', 'python']
        
        for scheme in schemes:
            self.log(f"切换到{scheme}方案...")
            
            # 更新设置
            self.settings_manager.set_hotkey_scheme(scheme)
            current_scheme = self.settings_manager.get_hotkey_scheme()
            self.log(f"当前设置的方案: {current_scheme}")
            
            # 清理旧管理器
            if self.current_manager:
                try:
                    self.current_manager.stop_listening()
                    self.current_manager.cleanup()
                except Exception as e:
                    self.log(f"清理旧管理器失败: {e}")
            
            # 创建新管理器
            self.current_manager = self.test_scheme_creation(scheme)
            
            if self.current_manager:
                # 测试启动监听
                try:
                    success = self.current_manager.start_listening()
                    if success:
                        self.log(f"✓ {scheme}方案启动监听成功")
                        
                        # 等待一段时间测试稳定性
                        self.log("等待5秒测试稳定性...")
                        time.sleep(5)
                        
                        # 检查状态
                        status = self.current_manager.get_status()
                        self.log(f"运行状态: {status}")
                        
                        if status.get('active', False):
                            self.log(f"✓ {scheme}方案运行稳定")
                            self.test_results.append((scheme, True, "运行正常"))
                        else:
                            self.log(f"❌ {scheme}方案运行不稳定")
                            self.test_results.append((scheme, False, "运行不稳定"))
                    else:
                        self.log(f"❌ {scheme}方案启动监听失败")
                        self.test_results.append((scheme, False, "启动失败"))
                        
                except Exception as e:
                    self.log(f"❌ {scheme}方案测试异常: {e}")
                    self.test_results.append((scheme, False, f"异常: {e}"))
            else:
                self.test_results.append((scheme, False, "创建失败"))
            
            self.log(f"{scheme}方案测试完成\n")
    
    def on_hotkey_press(self):
        """热键按下回调"""
        self.log("🔴 热键按下事件")
    
    def on_hotkey_release(self):
        """热键释放回调"""
        self.log("⚪ 热键释放事件")
    
    def print_test_results(self):
        """打印测试结果"""
        self.log("=== 测试结果汇总 ===")
        
        for scheme, success, message in self.test_results:
            status = "✓ 成功" if success else "❌ 失败"
            self.log(f"{scheme}方案: {status} - {message}")
        
        # 统计
        success_count = sum(1 for _, success, _ in self.test_results if success)
        total_count = len(self.test_results)
        self.log(f"\n成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    def cleanup(self):
        """清理资源"""
        if self.current_manager:
            try:
                self.current_manager.stop_listening()
                self.current_manager.cleanup()
                self.log("✓ 资源清理完成")
            except Exception as e:
                self.log(f"❌ 资源清理失败: {e}")
    
    def run_tests(self):
        """运行所有测试"""
        try:
            self.log("开始双热键方案测试...")
            
            # 测试方案可用性
            available_schemes = self.test_scheme_availability()
            
            if not available_schemes:
                self.log("❌ 没有可用的热键方案")
                return
            
            # 测试方案切换
            self.test_scheme_switching()
            
            # 打印结果
            self.print_test_results()
            
        except KeyboardInterrupt:
            self.log("\n用户中断测试")
        except Exception as e:
            self.log(f"❌ 测试过程中发生异常: {e}")
        finally:
            self.cleanup()

def main():
    """主函数"""
    print("双热键方案测试工具")
    print("=" * 50)
    
    tester = DualHotkeyTester()
    tester.run_tests()
    
    print("\n测试完成，按任意键退出...")
    try:
        input()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()