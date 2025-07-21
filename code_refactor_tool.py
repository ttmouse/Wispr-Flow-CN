#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码重构工具 - 识别和清理项目中的冗余代码
保持系统功能不变的情况下，使代码更简洁和优雅
"""

import os
import re
import ast
import shutil
from pathlib import Path
from typing import List, Dict, Set, Tuple
from datetime import datetime

class CodeRefactorTool:
    """代码重构工具类"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.src_dir = self.project_root / "src"
        self.backup_dir = self.project_root / "backup_before_refactor"
        self.analysis_report = []
        
    def analyze_redundant_code(self):
        """分析项目中的冗余代码"""
        print("🔍 开始分析项目中的冗余代码...")
        print("=" * 60)
        
        # 1. 分析重复的函数定义
        duplicate_functions = self._find_duplicate_functions()
        
        # 2. 分析相似的cleanup方法
        cleanup_methods = self._analyze_cleanup_methods()
        
        # 3. 分析重复的权限检查逻辑
        permission_checks = self._analyze_permission_checks()
        
        # 4. 分析重复的导入语句
        import_redundancy = self._analyze_import_redundancy()
        
        # 5. 分析异常处理模式
        exception_patterns = self._analyze_exception_patterns()
        
        # 6. 分析硬编码值
        hardcoded_values = self._find_hardcoded_values()
        
        # 生成分析报告
        self._generate_analysis_report({
            'duplicate_functions': duplicate_functions,
            'cleanup_methods': cleanup_methods,
            'permission_checks': permission_checks,
            'import_redundancy': import_redundancy,
            'exception_patterns': exception_patterns,
            'hardcoded_values': hardcoded_values
        })
        
        return self.analysis_report
    
    def _find_duplicate_functions(self) -> Dict[str, List[str]]:
        """查找重复的函数定义"""
        print("\n📋 分析重复的函数定义...")
        
        function_signatures = {}
        duplicate_functions = {}
        
        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 使用AST解析函数定义
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        func_name = node.name
                        # 获取函数签名（简化版）
                        args = [arg.arg for arg in node.args.args]
                        signature = f"{func_name}({', '.join(args)})"
                        
                        if signature not in function_signatures:
                            function_signatures[signature] = []
                        function_signatures[signature].append(str(py_file))
                        
            except Exception as e:
                print(f"⚠️ 解析文件失败 {py_file}: {e}")
        
        # 找出重复的函数
        for signature, files in function_signatures.items():
            if len(files) > 1:
                duplicate_functions[signature] = files
                print(f"  🔄 重复函数: {signature}")
                for file in files:
                    print(f"    📁 {file}")
        
        return duplicate_functions
    
    def _analyze_cleanup_methods(self) -> Dict[str, Dict]:
        """分析cleanup方法的实现"""
        print("\n🧹 分析cleanup方法实现...")
        
        cleanup_methods = {}
        
        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 查找cleanup方法
                cleanup_pattern = r'def cleanup\(self\):(.*?)(?=def |class |$)'
                matches = re.finditer(cleanup_pattern, content, re.DOTALL)
                
                for match in matches:
                    method_body = match.group(1).strip()
                    cleanup_methods[str(py_file)] = {
                        'body': method_body,
                        'lines': len(method_body.split('\n')),
                        'has_try_except': 'try:' in method_body,
                        'has_print': 'print(' in method_body,
                        'has_logging': 'logging.' in method_body or 'logger.' in method_body
                    }
                    
            except Exception as e:
                print(f"⚠️ 分析cleanup方法失败 {py_file}: {e}")
        
        # 分析相似性
        print(f"  📊 找到 {len(cleanup_methods)} 个cleanup方法")
        for file, info in cleanup_methods.items():
            print(f"    📁 {file}: {info['lines']}行, try/except: {info['has_try_except']}")
        
        return cleanup_methods
    
    def _analyze_permission_checks(self) -> Dict[str, List[str]]:
        """分析权限检查逻辑"""
        print("\n🔐 分析权限检查逻辑...")
        
        permission_patterns = {
            'check_permissions': [],
            'microphone_permission': [],
            'accessibility_permission': [],
            'osascript_permission': []
        }
        
        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 查找各种权限检查模式
                if 'check_permissions' in content:
                    permission_patterns['check_permissions'].append(str(py_file))
                
                if 'microphone' in content.lower() and 'permission' in content.lower():
                    permission_patterns['microphone_permission'].append(str(py_file))
                
                if 'accessibility' in content.lower() and 'permission' in content.lower():
                    permission_patterns['accessibility_permission'].append(str(py_file))
                
                if 'osascript' in content and 'permission' in content.lower():
                    permission_patterns['osascript_permission'].append(str(py_file))
                    
            except Exception as e:
                print(f"⚠️ 分析权限检查失败 {py_file}: {e}")
        
        for pattern, files in permission_patterns.items():
            if files:
                print(f"  🔑 {pattern}: {len(files)} 个文件")
                for file in files:
                    print(f"    📁 {file}")
        
        return permission_patterns
    
    def _analyze_import_redundancy(self) -> Dict[str, List[str]]:
        """分析重复的导入语句"""
        print("\n📦 分析导入语句冗余...")
        
        import_usage = {}
        
        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                imports = []
                for line in lines[:50]:  # 只检查前50行
                    line = line.strip()
                    if line.startswith('import ') or line.startswith('from '):
                        imports.append(line)
                
                if imports:
                    import_usage[str(py_file)] = imports
                    
            except Exception as e:
                print(f"⚠️ 分析导入语句失败 {py_file}: {e}")
        
        # 统计最常用的导入
        import_count = {}
        for file, imports in import_usage.items():
            for imp in imports:
                if imp not in import_count:
                    import_count[imp] = []
                import_count[imp].append(file)
        
        # 找出使用频率高的导入
        common_imports = {imp: files for imp, files in import_count.items() if len(files) >= 3}
        
        print(f"  📊 常用导入语句 (使用≥3次):")
        for imp, files in sorted(common_imports.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"    📦 {imp}: {len(files)} 次")
        
        return common_imports
    
    def _analyze_exception_patterns(self) -> Dict[str, List[str]]:
        """分析异常处理模式"""
        print("\n⚠️ 分析异常处理模式...")
        
        exception_patterns = {
            'generic_except': [],
            'print_error': [],
            'logging_error': [],
            'traceback_print': []
        }
        
        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 查找各种异常处理模式
                if 'except Exception as e:' in content:
                    exception_patterns['generic_except'].append(str(py_file))
                
                if 'print(f"❌' in content or 'print(f"⚠️' in content:
                    exception_patterns['print_error'].append(str(py_file))
                
                if 'logging.error' in content or 'logger.error' in content:
                    exception_patterns['logging_error'].append(str(py_file))
                
                if 'traceback.print_exc()' in content or 'traceback.format_exc()' in content:
                    exception_patterns['traceback_print'].append(str(py_file))
                    
            except Exception as e:
                print(f"⚠️ 分析异常处理失败 {py_file}: {e}")
        
        for pattern, files in exception_patterns.items():
            if files:
                print(f"  ⚡ {pattern}: {len(files)} 个文件")
        
        return exception_patterns
    
    def _find_hardcoded_values(self) -> Dict[str, List[Tuple[str, str]]]:
        """查找硬编码值"""
        print("\n🔢 查找硬编码值...")
        
        hardcoded_patterns = {
            'magic_numbers': r'\b(?:0\.3|3000|5000|8000|16000|30|50|100|200|300|500|1000)\b',
            'file_paths': r'["\'][^"\'
]*\.(wav|log|json|txt|py)["\']',
            'app_names': r'["\'](?:Dou-flow|ASR-FunASR|Music|Spotify|Chrome|Safari)["\']',
            'error_messages': r'["\'][^"\'
]*(?:失败|错误|Error|Failed)[^"\'
]*["\']'
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
        
        # 4. 导入优化
        if analysis_data['import_redundancy']:
            suggestions += "### 4. 导入语句优化\n\n"
            suggestions += "**优先级：低**\n"
            suggestions += "- 创建 `src/common_imports.py` 管理常用导入\n"
            suggestions += "- 使用相对导入减少路径依赖\n"
            suggestions += "- 移除未使用的导入语句\n\n"
        
        # 5. 异常处理优化
        if analysis_data['exception_patterns']['generic_except']:
            suggestions += "### 5. 异常处理优化\n\n"
            suggestions += "**优先级：高**\n"
            suggestions += "- 创建 `src/utils/error_handler.py` 统一异常处理\n"
            suggestions += "- 使用具体的异常类型替代通用Exception\n"
            suggestions += "- 统一错误日志格式\n\n"
        
        # 6. 配置管理优化
        if analysis_data['hardcoded_values']['magic_numbers']:
            suggestions += "### 6. 配置管理优化\n\n"
            suggestions += "**优先级：中**\n"
            suggestions += "- 将硬编码值提取到 `src/constants.py`\n"
            suggestions += "- 创建配置文件管理系统\n"
            suggestions += "- 实现运行时配置更新\n\n"
        
        return suggestions
    
    def create_refactor_plan(self) -> str:
        """创建重构计划"""
        plan_content = f"""
# 代码重构执行计划
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📋 重构步骤

### 阶段1: 高优先级重构 (立即执行)

#### 1.1 创建工具模块
```bash
# 创建工具目录
mkdir -p src/utils

# 创建文本处理工具
touch src/utils/text_utils.py
touch src/utils/error_handler.py
touch src/utils/permission_utils.py
```

#### 1.2 重构clean_html_tags函数
- [ ] 将函数移动到 `src/utils/text_utils.py`
- [ ] 更新 `src/main.py` 中的导入
- [ ] 更新 `src/ui/components/history_manager.py` 中的导入
- [ ] 测试功能完整性

#### 1.3 统一异常处理
- [ ] 创建 `src/utils/error_handler.py`
- [ ] 实现统一的异常处理装饰器
- [ ] 逐步替换现有的异常处理代码

### 阶段2: 中优先级重构 (1-2周内)

#### 2.1 优化cleanup方法
- [ ] 创建 `CleanupMixin` 基类
- [ ] 重构各个类的cleanup方法
- [ ] 添加清理状态跟踪

#### 2.2 统一权限检查
- [ ] 创建 `src/utils/permission_utils.py`
- [ ] 合并重复的权限检查逻辑
- [ ] 实现权限状态缓存

#### 2.3 配置管理优化
- [ ] 扩展 `src/constants.py`
- [ ] 提取硬编码值
- [ ] 创建配置验证机制

### 阶段3: 低优先级重构 (长期维护)

#### 3.1 导入优化
- [ ] 清理未使用的导入
- [ ] 优化导入顺序
- [ ] 使用相对导入

#### 3.2 代码风格统一
- [ ] 统一命名约定
- [ ] 添加类型注解
- [ ] 完善文档字符串

## ⚠️ 注意事项

1. **备份重要**: 每次重构前创建备份
2. **逐步进行**: 不要一次性修改太多文件
3. **测试验证**: 每个阶段完成后进行功能测试
4. **保持功能**: 确保重构不影响现有功能

## 🧪 测试策略

1. **单元测试**: 为重构的函数编写测试
2. **集成测试**: 验证模块间的交互
3. **功能测试**: 确保用户功能正常
4. **性能测试**: 验证重构不影响性能
"""
        
        plan_file = self.project_root / "code_refactor_plan.md"
        with open(plan_file, 'w', encoding='utf-8') as f:
            f.write(plan_content)
        
        print(f"📋 重构计划已保存到: {plan_file}")
        return plan_content
    
    def execute_high_priority_refactor(self):
        """执行高优先级重构"""
        print("\n🚀 开始执行高优先级重构...")
        
        # 创建备份
        self._create_backup()
        
        # 1. 创建工具目录
        self._create_utils_directory()
        
        # 2. 重构clean_html_tags函数
        self._refactor_clean_html_tags()
        
        # 3. 创建异常处理工具
        self._create_error_handler()
        
        print("✅ 高优先级重构完成！")
    
    def _create_backup(self):
        """创建备份"""
        print("📦 创建备份...")
        
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        
        shutil.copytree(self.src_dir, self.backup_dir)
        print(f"✅ 备份已创建: {self.backup_dir}")
    
    def _create_utils_directory(self):
        """创建工具目录"""
        print("📁 创建工具目录...")
        
        utils_dir = self.src_dir / "utils"
        utils_dir.mkdir(exist_ok=True)
        
        # 创建__init__.py
        init_file = utils_dir / "__init__.py"
        init_file.write_text('"""工具模块"""\n', encoding='utf-8')
        
        print(f"✅ 工具目录已创建: {utils_dir}")
    
    def _refactor_clean_html_tags(self):
        """重构clean_html_tags函数"""
        print("🔧 重构clean_html_tags函数...")
        
        # 创建text_utils.py
        text_utils_content = '''
"""文本处理工具模块"""

import re
from typing import Optional

def clean_html_tags(text: Optional[str]) -> str:
    """清理HTML标签，返回纯文本
    
    Args:
        text: 包含HTML标签的文本
        
    Returns:
        清理后的纯文本
    """
    if not text:
        return text or 