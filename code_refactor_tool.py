#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码重构工具 - 分析和清理项目中的冗余代码
"""

import os
import re
import ast
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict, Counter
from datetime import datetime
import argparse

class CodeRefactorTool:
    """代码重构分析工具"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.src_dir = self.project_root / "src"
        self.analysis_report = ""
        
    def analyze_project(self) -> Dict[str, Any]:
        """分析项目中的冗余代码"""
        print("🔍 开始分析项目冗余代码...")
        
        analysis_data = {
            'duplicate_functions': self._find_duplicate_functions(),
            'cleanup_methods': self._analyze_cleanup_methods(),
            'permission_checks': self._find_permission_checks(),
            'import_redundancy': self._analyze_import_redundancy(),
            'exception_patterns': self._find_exception_patterns(),
            'hardcoded_values': self._find_hardcoded_values()
        }
        
        self._generate_analysis_report(analysis_data)
        return analysis_data
    
    def _find_duplicate_functions(self) -> Dict[str, List[str]]:
        """查找重复的函数定义"""
        print("\n🔄 查找重复函数定义...")
        
        function_definitions = defaultdict(list)
        
        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 使用AST解析函数定义
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        function_definitions[node.name].append(str(py_file))
                        
            except Exception as e:
                print(f"⚠️ 解析文件失败 {py_file}: {e}")
        
        # 找出重复的函数
        duplicates = {func: files for func, files in function_definitions.items() if len(files) > 1}
        
        if duplicates:
            print(f"  🎯 发现 {len(duplicates)} 个重复函数:")
            for func, files in duplicates.items():
                print(f"    - {func}: {len(files)} 个文件")
        else:
            print("  ✅ 未发现重复函数")
            
        return duplicates
    
    def _analyze_cleanup_methods(self) -> Dict[str, Dict[str, Any]]:
        """分析cleanup方法的实现"""
        print("\n🧹 分析cleanup方法...")
        
        cleanup_methods = {}
        
        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 查找cleanup方法
                cleanup_pattern = r'def\s+(cleanup|_cleanup|cleanup_resources|_quick_cleanup)\s*\([^)]*\):'
                matches = re.finditer(cleanup_pattern, content)
                
                for match in matches:
                    method_name = match.group(1)
                    # 计算方法行数
                    lines_before = content[:match.start()].count('\n') + 1
                    method_content = self._extract_method_content(content, match.start())
                    lines_count = method_content.count('\n') + 1
                    
                    cleanup_methods[str(py_file)] = {
                        'method_name': method_name,
                        'start_line': lines_before,
                        'lines': lines_count,
                        'content_preview': method_content[:200] + '...' if len(method_content) > 200 else method_content
                    }
                    
            except Exception as e:
                print(f"⚠️ 分析cleanup方法失败 {py_file}: {e}")
        
        print(f"  🎯 发现 {len(cleanup_methods)} 个cleanup方法")
        return cleanup_methods
    
    def _extract_method_content(self, content: str, start_pos: int) -> str:
        """提取方法内容"""
        lines = content[start_pos:].split('\n')
        method_lines = [lines[0]]  # 方法定义行
        
        if len(lines) > 1:
            # 找到方法的缩进级别
            base_indent = len(lines[1]) - len(lines[1].lstrip()) if lines[1].strip() else 4
            
            for line in lines[1:]:
                if line.strip() == "":
                    method_lines.append(line)
                    continue
                    
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= base_indent and line.strip():
                    break
                    
                method_lines.append(line)
                
        return '\n'.join(method_lines)
    
    def _find_permission_checks(self) -> Dict[str, List[str]]:
        """查找权限检查相关代码"""
        print("\n🔐 查找权限检查逻辑...")
        
        permission_patterns = {
            'check_permissions': r'def\s+.*check.*permission',
            'accessibility_check': r'accessibility|辅助功能',
            'microphone_check': r'microphone|麦克风|录音权限',
            'system_events': r'system.*event|系统事件'
        }
        
        permission_checks = {pattern: [] for pattern in permission_patterns}
        
        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern_name, pattern in permission_patterns.items():
                    if re.search(pattern, content, re.IGNORECASE):
                        permission_checks[pattern_name].append(str(py_file))
                        
            except Exception as e:
                print(f"⚠️ 查找权限检查失败 {py_file}: {e}")
        
        for pattern, files in permission_checks.items():
            if files:
                print(f"  🎯 {pattern}: {len(files)} 个文件")
        
        return permission_checks
    
    def _analyze_import_redundancy(self) -> Dict[str, List[str]]:
        """分析导入语句冗余"""
        print("\n📦 分析导入语句冗余...")
        
        import_statements = defaultdict(list)
        
        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 查找import语句
                import_patterns = [
                    r'^import\s+([\w\.]+)',
                    r'^from\s+([\w\.]+)\s+import'
                ]
                
                for pattern in import_patterns:
                    matches = re.finditer(pattern, content, re.MULTILINE)
                    for match in matches:
                        module = match.group(1)
                        import_statements[module].append(str(py_file))
                        
            except Exception as e:
                print(f"⚠️ 分析导入语句失败 {py_file}: {e}")
        
        # 找出高频导入
        common_imports = {imp: files for imp, files in import_statements.items() if len(files) >= 3}
        
        print(f"  🎯 发现 {len(common_imports)} 个高频导入模块")
        return common_imports
    
    def _find_exception_patterns(self) -> Dict[str, List[str]]:
        """查找异常处理模式"""
        print("\n⚠️ 查找异常处理模式...")
        
        exception_patterns = {
            'generic_except': r'except\s*:',
            'broad_exception': r'except\s+Exception\s*:',
            'try_except_pass': r'except[^:]*:\s*pass',
            'exception_logging': r'except[^:]*:.*(?:print|log|logger)'
        }
        
        exception_usage = {pattern: [] for pattern in exception_patterns}
        
        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern_name, pattern in exception_patterns.items():
                    if re.search(pattern, content, re.MULTILINE | re.DOTALL):
                        exception_usage[pattern_name].append(str(py_file))
                        
            except Exception as e:
                print(f"⚠️ 查找异常处理失败 {py_file}: {e}")
        
        for pattern, files in exception_usage.items():
            if files:
                print(f"  🎯 {pattern}: {len(files)} 个文件")
        
        return exception_usage
    
    def _find_hardcoded_values(self) -> Dict[str, List[Tuple[str, str]]]:
        """查找硬编码值"""
        print("\n🔢 查找硬编码值...")
        
        hardcoded_patterns = {
            'magic_numbers': r'\\b(?:0\\.3|3000|5000|8000|16000|30|50|100|200|300|500|1000)\\b',
            'file_paths': r'["\'][^"\'\n]*\\.(wav|log|json|txt|py)["\']',
            'app_names': r'["\'](?:Dou-flow|ASR-FunASR|Music|Spotify|Chrome|Safari)["\']',
            'error_messages': r'["\'][^"\'\n]*(?:失败|错误|Error|Failed)[^"\'\n]*["\']'
        }
        
        hardcoded_values = {pattern: [] for pattern in hardcoded_patterns}
        
        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern_name, pattern in hardcoded_patterns.items():
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        hardcoded_values[pattern_name].append((str(py_file), match.group()))
                        
            except Exception as e:
                print(f"⚠️ 查找硬编码值失败 {py_file}: {e}")
        
        for pattern, values in hardcoded_values.items():
            if values:
                print(f"  🎯 {pattern}: {len(values)} 个")
        
        return hardcoded_values
    
    def _generate_analysis_report(self, analysis_data: Dict):
        """生成分析报告"""
        print("\n📊 生成分析报告...")
        
        report_content = f"""
# 代码冗余分析报告
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
项目路径: {self.project_root}

## 🎯 主要发现

### 1. 重复函数定义
"""
        
        # 重复函数
        if analysis_data['duplicate_functions']:
            report_content += "\n**发现的重复函数:**\n"
            for func, files in analysis_data['duplicate_functions'].items():
                report_content += f"- `{func}` 在 {len(files)} 个文件中重复:\n"
                for file in files:
                    report_content += f"  - {file}\n"
        else:
            report_content += "\n✅ 未发现重复的函数定义\n"
        
        # Cleanup方法分析
        report_content += "\n### 2. Cleanup方法分析\n"
        if analysis_data['cleanup_methods']:
            report_content += f"\n**找到 {len(analysis_data['cleanup_methods'])} 个cleanup方法:**\n"
            for file, info in analysis_data['cleanup_methods'].items():
                report_content += f"- {file}: {info['lines']}行\n"
        
        # 权限检查
        report_content += "\n### 3. 权限检查逻辑\n"
        for pattern, files in analysis_data['permission_checks'].items():
            if files:
                report_content += f"\n**{pattern}:** {len(files)} 个文件\n"
        
        # 导入冗余
        report_content += "\n### 4. 导入语句冗余\n"
        common_imports = analysis_data['import_redundancy']
        if common_imports:
            report_content += "\n**高频导入语句:**\n"
            for imp, files in sorted(common_imports.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
                report_content += f"- `{imp}`: {len(files)} 次\n"
        
        # 异常处理
        report_content += "\n### 5. 异常处理模式\n"
        for pattern, files in analysis_data['exception_patterns'].items():
            if files:
                report_content += f"- **{pattern}:** {len(files)} 个文件\n"
        
        # 硬编码值
        report_content += "\n### 6. 硬编码值统计\n"
        for pattern, values in analysis_data['hardcoded_values'].items():
            if values:
                report_content += f"- **{pattern}:** {len(values)} 个\n"
        
        # 优化建议
        report_content += self._generate_optimization_suggestions(analysis_data)
        
        # 保存报告
        report_file = self.project_root / "code_redundancy_analysis.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"✅ 分析报告已保存到: {report_file}")
        self.analysis_report = report_content
    
    def _generate_optimization_suggestions(self, analysis_data: Dict) -> str:
        """生成优化建议"""
        suggestions = "\n\n## 🚀 优化建议\n\n"
        
        # 1. 重复函数优化
        if analysis_data['duplicate_functions']:
            suggestions += "### 1. 重复函数优化\n\n"
            
            # 特别处理clean_html_tags函数
            for func, files in analysis_data['duplicate_functions'].items():
                if 'clean_html_tags' in func:
                    suggestions += "**优先级：高**\n"
                    suggestions += "- 创建 `src/utils/text_utils.py` 统一管理文本处理函数\n"
                    suggestions += "- 将 `clean_html_tags` 函数移动到工具模块\n"
                    suggestions += "- 更新所有引用该函数的文件\n\n"
        
        # 2. Cleanup方法优化
        if len(analysis_data['cleanup_methods']) > 3:
            suggestions += "### 2. 资源清理优化\n\n"
            suggestions += "**优先级：中**\n"
            suggestions += "- 创建基础清理接口 `CleanupMixin`\n"
            suggestions += "- 统一清理方法的实现模式\n"
            suggestions += "- 添加清理状态跟踪\n\n"
        
        # 3. 权限检查优化
        permission_files = sum(len(files) for files in analysis_data['permission_checks'].values())
        if permission_files > 2:
            suggestions += "### 3. 权限检查优化\n\n"
            suggestions += "**优先级：中**\n"
            suggestions += "- 创建 `src/utils/permission_utils.py` 统一权限检查\n"
            suggestions += "- 实现权限状态缓存机制\n"
            suggestions += "- 统一权限错误处理\n\n"
        
        return suggestions
    
    def execute_high_priority_refactoring(self):
        """执行高优先级重构"""
        print("\n🚀 开始执行高优先级重构...")
        
        # 1. 创建工具目录
        utils_dir = self.src_dir / "utils"
        utils_dir.mkdir(exist_ok=True)
        
        # 创建__init__.py
        init_file = utils_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text('"""工具模块"""\n', encoding='utf-8')
        
        # 2. 创建text_utils.py
        self._create_text_utils()
        
        # 3. 创建error_handler.py
        self._create_error_handler()
        
        print("✅ 高优先级重构完成")
    
    def _create_text_utils(self):
        """创建文本处理工具模块"""
        text_utils_content = '''
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本处理工具模块
统一管理所有文本处理相关的函数
"""

import re
import html

def clean_html_tags(text: str) -> str:
    """
    清理HTML标签和解码HTML实体
    
    Args:
        text: 包含HTML标签的文本
        
    Returns:
        清理后的纯文本
    """
    if not text:
        return ""
    
    # 移除HTML标签
    clean_text = re.sub(r'<[^>]+>', '', text)
    
    # 解码HTML实体
    clean_text = html.unescape(clean_text)
    
    # 清理多余的空白字符
    clean_text = re.sub(r'\\s+', ' ', clean_text).strip()
    
    return clean_text

def normalize_text(text: str) -> str:
    """
    标准化文本格式
    
    Args:
        text: 原始文本
        
    Returns:
        标准化后的文本
    """
    if not text:
        return ""
    
    # 统一换行符
    text = text.replace('\\r\\n', '\\n').replace('\\r', '\\n')
    
    # 移除多余空行
    text = re.sub(r'\\n\\s*\\n', '\\n\\n', text)
    
    # 清理首尾空白
    text = text.strip()
    
    return text

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本到指定长度
    
    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 截断后缀
        
    Returns:
        截断后的文本
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix
'''
        
        text_utils_file = self.src_dir / "utils" / "text_utils.py"
        with open(text_utils_file, 'w', encoding='utf-8') as f:
            f.write(text_utils_content)
        
        print(f"✅ 创建文本工具模块: {text_utils_file}")
    
    def _create_error_handler(self):
        """创建错误处理工具模块"""
        error_handler_content = '''
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误处理工具模块
统一管理异常处理逻辑
"""

import functools
import logging
import traceback
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)

def handle_exceptions(default_return: Any = None, 
                     log_error: bool = True,
                     reraise: bool = False):
    """
    统一异常处理装饰器
    
    Args:
        default_return: 异常时的默认返回值
        log_error: 是否记录错误日志
        reraise: 是否重新抛出异常
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.error(
                        f"函数 {func.__name__} 执行失败: {str(e)}\\n"
                        f"参数: args={args}, kwargs={kwargs}\\n"
                        f"堆栈: {traceback.format_exc()}"
                    )
                
                if reraise:
                    raise
                    
                return default_return
        return wrapper
    return decorator

def safe_execute(func: Callable, 
                *args, 
                default_return: Any = None,
                log_error: bool = True,
                **kwargs) -> Any:
    """
    安全执行函数
    
    Args:
        func: 要执行的函数
        *args: 函数参数
        default_return: 异常时的默认返回值
        log_error: 是否记录错误日志
        **kwargs: 函数关键字参数
        
    Returns:
        函数执行结果或默认返回值
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_error:
            logger.error(
                f"安全执行函数 {func.__name__} 失败: {str(e)}\\n"
                f"参数: args={args}, kwargs={kwargs}\\n"
                f"堆栈: {traceback.format_exc()}"
            )
        return default_return

class ErrorContext:
    """
    错误上下文管理器
    """
    
    def __init__(self, 
                 operation_name: str,
                 default_return: Any = None,
                 log_error: bool = True,
                 reraise: bool = False):
        self.operation_name = operation_name
        self.default_return = default_return
        self.log_error = log_error
        self.reraise = reraise
        self.result = None
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            if self.log_error:
                logger.error(
                    f"操作 '{self.operation_name}' 失败: {str(exc_val)}\\n"
                    f"异常类型: {exc_type.__name__}\\n"
                    f"堆栈: {traceback.format_exc()}"
                )
            
            if not self.reraise:
                self.result = self.default_return
                return True  # 抑制异常
                
        return False  # 不抑制异常
'''
        
        error_handler_file = self.src_dir / "utils" / "error_handler.py"
        with open(error_handler_file, 'w', encoding='utf-8') as f:
            f.write(error_handler_content)
        
        print(f"✅ 创建错误处理模块: {error_handler_file}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='代码重构工具')
    parser.add_argument('project_path', help='项目根目录路径')
    parser.add_argument('--execute', action='store_true', help='执行高优先级重构')
    
    args = parser.parse_args()
    
    tool = CodeRefactorTool(args.project_path)
    
    # 分析项目
    analysis_data = tool.analyze_project()
    
    # 执行重构（如果指定）
    if args.execute:
        tool.execute_high_priority_refactoring()
    
    print("\n🎉 分析完成！")
    print(f"📄 查看详细报告: {tool.project_root}/code_redundancy_analysis.md")

if __name__ == "__main__":
    main()