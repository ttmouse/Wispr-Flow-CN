#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
冗余文件清理脚本
用于清理AI生成代码中的重复和无用文件
"""

import os
import shutil
from pathlib import Path
import json
from datetime import datetime

class RedundantFileCleaner:
    """冗余文件清理器"""
    
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.backup_dir = self.project_root / "backup_before_cleanup"
        self.cleanup_log = []
    
    def create_backup(self):
        """创建备份目录"""
        if not self.backup_dir.exists():
            self.backup_dir.mkdir()
            print(f"✓ 创建备份目录: {self.backup_dir}")
    
    def backup_file(self, file_path):
        """备份单个文件"""
        if file_path.exists():
            backup_path = self.backup_dir / file_path.name
            shutil.copy2(file_path, backup_path)
            return True
        return False
    
    def log_action(self, action, file_path, reason):
        """记录清理动作"""
        self.cleanup_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "file": str(file_path),
            "reason": reason
        })
    
    def clean_duplicate_test_files(self):
        """清理重复的测试文件"""
        print("\n🧹 清理重复的测试文件...")
        
        # 要删除的重复测试文件
        duplicate_files = [
            "audio_control_test.py",  # 保留 v3 版本
            "audio_control_test_v2.py",
            "test_drag_fix.py",
            "test_drag_simple.py", 
            "test_exit_fix.py",
            "test_exit_improvement.py",
            "test_simple_exit.py",
            "test_ui_crash.py",
            "test_loading_drag.py",
            "test_line_height.py",  # 功能重复
            "test_list_display.py",  # 功能重复
            "test_html_cleanup.py",  # 功能重复
            "test_html_rendering.py",  # 功能重复
        ]
        
        deleted_count = 0
        for filename in duplicate_files:
            file_path = self.project_root / filename
            if file_path.exists():
                # 备份文件
                self.backup_file(file_path)
                # 删除文件
                file_path.unlink()
                self.log_action("DELETE", file_path, "重复的测试文件")
                print(f"  ❌ 删除: {filename}")
                deleted_count += 1
            else:
                print(f"  ⚠️  文件不存在: {filename}")
        
        print(f"✓ 删除了 {deleted_count} 个重复测试文件")
    
    def clean_redundant_docs(self):
        """清理冗余的文档文件"""
        print("\n📚 清理冗余的文档文件...")
        
        # 要删除的冗余文档（内容已合并到主文档）
        redundant_docs = [
            "HOTKEY_STATUS_GUIDE.md",
            "HOTKEY_TROUBLESHOOTING.md", 
            "CLIPBOARD_FIX_GUIDE.md",
            "CLIPBOARD_CONTENT_VERIFICATION_FIX.md",
            "STYLE_CONFIG_README.md",
            "PASTE_FUNCTION_FIX_REPORT.md",
            "CRASH_FIX_REPORT.md",
            "CACHE_CRASH_FIX_REPORT.md",
            "APP_EXIT_PROCESS_ANALYSIS.md",
            "RECORDING_IMPROVEMENT_SUMMARY.md",
            "RECORDING_STABILITY_ANALYSIS.md",
        ]
        
        deleted_count = 0
        for filename in redundant_docs:
            file_path = self.project_root / filename
            if file_path.exists():
                # 备份文件
                self.backup_file(file_path)
                # 删除文件
                file_path.unlink()
                self.log_action("DELETE", file_path, "冗余的文档文件")
                print(f"  ❌ 删除: {filename}")
                deleted_count += 1
        
        print(f"✓ 删除了 {deleted_count} 个冗余文档文件")
    
    def clean_duplicate_engine_files(self):
        """清理重复的引擎文件"""
        print("\n⚙️  清理重复的引擎文件...")
        
        # 项目根目录的重复文件（保留 src/ 目录中的版本）
        root_engine = self.project_root / "funasr_engine.py"
        if root_engine.exists():
            self.backup_file(root_engine)
            root_engine.unlink()
            self.log_action("DELETE", root_engine, "重复的引擎文件，保留src/版本")
            print(f"  ❌ 删除: funasr_engine.py (根目录)")
            print(f"  ✓ 保留: src/funasr_engine.py")
        else:
            print(f"  ⚠️  根目录引擎文件不存在")
    
    def clean_old_settings_backups(self):
        """清理过多的设置备份文件"""
        print("\n⚙️  清理过多的设置备份文件...")
        
        settings_history_dir = self.project_root / "settings_history"
        if not settings_history_dir.exists():
            print("  ⚠️  设置历史目录不存在")
            return
        
        # 获取所有备份文件并按时间排序
        backup_files = list(settings_history_dir.glob("settings_*.json"))
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # 保留最新的5个备份，删除其余的
        keep_count = 5
        if len(backup_files) > keep_count:
            files_to_delete = backup_files[keep_count:]
            for file_path in files_to_delete:
                self.backup_file(file_path)
                file_path.unlink()
                self.log_action("DELETE", file_path, "过多的设置备份文件")
                print(f"  ❌ 删除旧备份: {file_path.name}")
            
            print(f"✓ 保留最新 {keep_count} 个备份，删除了 {len(files_to_delete)} 个旧备份")
        else:
            print(f"  ✓ 备份文件数量合理 ({len(backup_files)} 个)")
    
    def clean_temp_files(self):
        """清理临时文件"""
        print("\n🗑️  清理临时文件...")
        
        temp_patterns = [
            "*.pyc",
            "*.pyo", 
            "*.pyd",
            "__pycache__",
            ".DS_Store",
            "*.tmp",
            "*.log",  # 旧的日志文件
        ]
        
        deleted_count = 0
        for pattern in temp_patterns:
            if pattern == "__pycache__":
                # 删除 __pycache__ 目录
                for cache_dir in self.project_root.rglob("__pycache__"):
                    if cache_dir.is_dir():
                        shutil.rmtree(cache_dir)
                        self.log_action("DELETE", cache_dir, "Python缓存目录")
                        print(f"  ❌ 删除缓存目录: {cache_dir.relative_to(self.project_root)}")
                        deleted_count += 1
            else:
                # 删除匹配的文件
                for file_path in self.project_root.rglob(pattern):
                    if file_path.is_file():
                        file_path.unlink()
                        self.log_action("DELETE", file_path, f"临时文件 ({pattern})")
                        print(f"  ❌ 删除临时文件: {file_path.relative_to(self.project_root)}")
                        deleted_count += 1
        
        print(f"✓ 删除了 {deleted_count} 个临时文件")
    
    def save_cleanup_log(self):
        """保存清理日志"""
        log_file = self.project_root / "cleanup_log.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(self.cleanup_log, f, indent=2, ensure_ascii=False)
        print(f"\n📝 清理日志已保存到: {log_file}")
    
    def generate_summary(self):
        """生成清理总结"""
        total_deleted = len(self.cleanup_log)
        file_types = {}
        
        for entry in self.cleanup_log:
            reason = entry['reason']
            file_types[reason] = file_types.get(reason, 0) + 1
        
        print("\n" + "=" * 50)
        print("🎯 清理总结")
        print("=" * 50)
        print(f"总共删除文件: {total_deleted} 个")
        print("\n按类型统计:")
        for file_type, count in file_types.items():
            print(f"  - {file_type}: {count} 个")
        
        print(f"\n📁 备份位置: {self.backup_dir}")
        print("\n💡 建议下一步:")
        print("  1. 检查应用功能是否正常")
        print("  2. 如果有问题，可从备份目录恢复文件")
        print("  3. 确认无问题后，可删除备份目录")
        print("  4. 继续执行代码结构优化")
    
    def run_cleanup(self):
        """执行完整的清理流程"""
        print("🚀 开始清理AI生成代码的冗余文件")
        print("=" * 50)
        
        # 创建备份
        self.create_backup()
        
        # 执行各种清理
        self.clean_duplicate_test_files()
        self.clean_redundant_docs()
        self.clean_duplicate_engine_files()
        self.clean_old_settings_backups()
        self.clean_temp_files()
        
        # 保存日志和生成总结
        self.save_cleanup_log()
        self.generate_summary()

def main():
    """主函数"""
    # 获取项目根目录
    project_root = Path(__file__).parent
    
    print(f"项目目录: {project_root}")
    
    # 确认清理
    response = input("\n⚠️  即将清理冗余文件，是否继续？(y/N): ").strip().lower()
    if response != 'y':
        print("❌ 清理已取消")
        return
    
    # 执行清理
    cleaner = RedundantFileCleaner(project_root)
    cleaner.run_cleanup()
    
    print("\n✅ 清理完成！")

if __name__ == "__main__":
    main()