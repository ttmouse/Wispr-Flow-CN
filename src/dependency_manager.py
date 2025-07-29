#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖管理器模块
负责检测、安装和管理应用运行所需的各种依赖
"""

import os
import sys
import subprocess
import platform
import shutil
import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

class DependencyStatus(Enum):
    """依赖状态枚举"""
    INSTALLED = "已安装"
    NOT_INSTALLED = "未安装"
    VERSION_MISMATCH = "版本不匹配"
    CORRUPTED = "文件损坏"
    UNKNOWN = "未知状态"

@dataclass
class DependencyInfo:
    """依赖信息数据类"""
    name: str
    description: str
    status: DependencyStatus
    version: Optional[str] = None
    required_version: Optional[str] = None
    install_command: Optional[str] = None
    check_command: Optional[str] = None
    error_message: Optional[str] = None

class DependencyManager:
    """依赖管理器主类"""
    
    def __init__(self):
        self.logger = logging.getLogger('DependencyManager')
        self.dependencies = {}
        self._init_dependencies()
    
    def _init_dependencies(self):
        """初始化依赖项定义"""
        self.dependencies = {
            'python': DependencyInfo(
                name='Python环境',
                description='Python 3.8+ 运行环境',
                status=DependencyStatus.UNKNOWN,
                required_version='3.8+',
                check_command='python3 --version'
            ),
            'conda': DependencyInfo(
                name='Conda环境',
                description='Miniconda/Anaconda包管理器',
                status=DependencyStatus.UNKNOWN,
                check_command='conda --version'
            ),
            'funasr_env': DependencyInfo(
                name='FunASR环境',
                description='专用的Python虚拟环境',
                status=DependencyStatus.UNKNOWN,
                check_command='conda env list | grep funasr_env'
            ),
            'asr_model': DependencyInfo(
                name='ASR模型',
                description='语音识别模型文件',
                status=DependencyStatus.UNKNOWN
            ),
            'punc_model': DependencyInfo(
                name='标点模型',
                description='标点符号预测模型文件',
                status=DependencyStatus.UNKNOWN
            ),
            'microphone_permission': DependencyInfo(
                name='麦克风权限',
                description='录音所需的系统权限',
                status=DependencyStatus.UNKNOWN
            ),
            'accessibility_permission': DependencyInfo(
                name='辅助功能权限',
                description='自动粘贴所需的系统权限',
                status=DependencyStatus.UNKNOWN
            )
        }
    
    def check_all_dependencies(self) -> Dict[str, DependencyInfo]:
        """检查所有依赖项状态"""
        self.logger.debug("开始检查所有依赖项")
        
        # 检查Python环境
        self._check_python()
        
        # 检查Conda环境
        self._check_conda()
        
        # 检查FunASR环境
        self._check_funasr_env()
        
        # 检查模型文件
        self._check_models()
        
        # 检查系统权限
        self._check_permissions()
        
        return self.dependencies
    
    def _check_python(self):
        """检查Python环境"""
        try:
            version = sys.version_info
            version_str = f"{version.major}.{version.minor}.{version.micro}"
            
            if version.major >= 3 and version.minor >= 8:
                self.dependencies['python'].status = DependencyStatus.INSTALLED
                self.dependencies['python'].version = version_str
            else:
                self.dependencies['python'].status = DependencyStatus.VERSION_MISMATCH
                self.dependencies['python'].version = version_str
                self.dependencies['python'].error_message = f"需要Python 3.8+，当前版本：{version_str}"
        except Exception as e:
            self.dependencies['python'].status = DependencyStatus.NOT_INSTALLED
            self.dependencies['python'].error_message = str(e)
    
    def _check_conda(self):
        """检查Conda环境"""
        try:
            # 首先检查conda命令是否可用
            result = subprocess.run(['conda', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version = result.stdout.strip().split()[-1]
                self.dependencies['conda'].status = DependencyStatus.INSTALLED
                self.dependencies['conda'].version = version
            else:
                self.dependencies['conda'].status = DependencyStatus.NOT_INSTALLED
                self.dependencies['conda'].error_message = "Conda命令执行失败"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # conda命令不存在，检查是否有其他Python环境
            try:
                # 检查是否有pip
                pip_result = subprocess.run(['pip', '--version'], 
                                          capture_output=True, text=True, timeout=10)
                if pip_result.returncode == 0:
                    self.dependencies['conda'].status = DependencyStatus.INSTALLED
                    self.dependencies['conda'].version = "pip环境"
                else:
                    self.dependencies['conda'].status = DependencyStatus.NOT_INSTALLED
                    self.dependencies['conda'].error_message = "未找到conda或pip命令"
            except:
                self.dependencies['conda'].status = DependencyStatus.NOT_INSTALLED
                self.dependencies['conda'].error_message = "未找到Python包管理器"
        except Exception as e:
            self.dependencies['conda'].status = DependencyStatus.UNKNOWN
            self.dependencies['conda'].error_message = str(e)
    
    def _check_funasr_env(self):
        """检查FunASR虚拟环境"""
        try:
            # 首先检查是否在conda环境中
            conda_env = os.environ.get('CONDA_DEFAULT_ENV')
            if conda_env:
                if 'funasr' in conda_env.lower() or conda_env == 'base':
                    self.dependencies['funasr_env'].status = DependencyStatus.INSTALLED
                    self.dependencies['funasr_env'].version = conda_env
                    return
            
            # 检查conda环境列表
            try:
                result = subprocess.run(['conda', 'env', 'list'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and 'funasr_env' in result.stdout:
                    self.dependencies['funasr_env'].status = DependencyStatus.INSTALLED
                    self.dependencies['funasr_env'].version = "funasr_env"
                    return
            except:
                pass
            
            # 检查当前Python环境是否可用
            try:
                # 检查是否能导入关键模块
                import sys
                python_path = sys.executable
                if python_path:
                    self.dependencies['funasr_env'].status = DependencyStatus.INSTALLED
                    self.dependencies['funasr_env'].version = f"当前Python环境 ({python_path})"
                else:
                    self.dependencies['funasr_env'].status = DependencyStatus.NOT_INSTALLED
                    self.dependencies['funasr_env'].error_message = "Python环境不可用"
            except Exception as e:
                self.dependencies['funasr_env'].status = DependencyStatus.NOT_INSTALLED
                self.dependencies['funasr_env'].error_message = f"环境检查失败: {str(e)}"
                
        except Exception as e:
            self.dependencies['funasr_env'].status = DependencyStatus.UNKNOWN
            self.dependencies['funasr_env'].error_message = str(e)
    
    def _check_models(self):
        """检查模型文件"""
        # 检查ASR模型
        try:
            asr_model_path = self._get_model_path('asr')
            if asr_model_path and asr_model_path.exists():
                self.dependencies['asr_model'].status = DependencyStatus.INSTALLED
                self.dependencies['asr_model'].version = "已下载"
            elif asr_model_path:
                self.dependencies['asr_model'].status = DependencyStatus.NOT_INSTALLED
                self.dependencies['asr_model'].error_message = f"ASR模型文件不存在: {asr_model_path}"
            else:
                # 模型路径未配置，这是正常的初始状态
                self.dependencies['asr_model'].status = DependencyStatus.NOT_INSTALLED
                self.dependencies['asr_model'].error_message = "ASR模型路径未配置，可在设置中配置"
        except Exception as e:
            self.dependencies['asr_model'].status = DependencyStatus.UNKNOWN
            self.dependencies['asr_model'].error_message = f"检查ASR模型失败: {str(e)}"
        
        # 检查标点模型
        try:
            punc_model_path = self._get_model_path('punc')
            if punc_model_path and punc_model_path.exists():
                self.dependencies['punc_model'].status = DependencyStatus.INSTALLED
                self.dependencies['punc_model'].version = "已下载"
            elif punc_model_path:
                self.dependencies['punc_model'].status = DependencyStatus.NOT_INSTALLED
                self.dependencies['punc_model'].error_message = f"标点模型文件不存在: {punc_model_path}"
            else:
                # 模型路径未配置，这是正常的初始状态
                self.dependencies['punc_model'].status = DependencyStatus.NOT_INSTALLED
                self.dependencies['punc_model'].error_message = "标点模型路径未配置，可在设置中配置"
        except Exception as e:
            self.dependencies['punc_model'].status = DependencyStatus.UNKNOWN
            self.dependencies['punc_model'].error_message = f"检查标点模型失败: {str(e)}"
    
    def _check_permissions(self):
        """检查系统权限"""
        if platform.system() == 'Darwin':
            # 检查麦克风权限
            self._check_microphone_permission()
            
            # 检查辅助功能权限
            self._check_accessibility_permission()
        else:
            # 非macOS系统，假设权限已授予
            self.dependencies['microphone_permission'].status = DependencyStatus.INSTALLED
            self.dependencies['accessibility_permission'].status = DependencyStatus.INSTALLED
    
    def _check_microphone_permission(self):
        """检查麦克风权限"""
        try:
            # 尝试使用pyaudio检查麦克风权限
            import pyaudio
            p = pyaudio.PyAudio()
            # 尝试获取默认输入设备
            default_input = p.get_default_input_device_info()
            p.terminate()
            
            if default_input:
                self.dependencies['microphone_permission'].status = DependencyStatus.INSTALLED
                self.dependencies['microphone_permission'].version = "已授权"
            else:
                self.dependencies['microphone_permission'].status = DependencyStatus.NOT_INSTALLED
                self.dependencies['microphone_permission'].error_message = "未找到麦克风设备"
        except ImportError:
            # pyaudio未安装，使用系统命令检查
            try:
                result = subprocess.run(
                    ['system_profiler', 'SPAudioDataType'], 
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0 and 'Input' in result.stdout:
                    self.dependencies['microphone_permission'].status = DependencyStatus.INSTALLED
                    self.dependencies['microphone_permission'].version = "已授权"
                else:
                    self.dependencies['microphone_permission'].status = DependencyStatus.NOT_INSTALLED
                    self.dependencies['microphone_permission'].error_message = "未检测到音频输入设备"
            except Exception as e:
                self.dependencies['microphone_permission'].status = DependencyStatus.UNKNOWN
                self.dependencies['microphone_permission'].error_message = f"检查失败: {str(e)}"
        except Exception as e:
            self.dependencies['microphone_permission'].status = DependencyStatus.NOT_INSTALLED
            self.dependencies['microphone_permission'].error_message = f"麦克风权限被拒绝: {str(e)}"
    
    def _check_accessibility_permission(self):
        """检查辅助功能权限"""
        try:
            # 使用AppleScript检查辅助功能权限
            script = '''
            tell application "System Events"
                try
                    set frontApp to name of first application process whose frontmost is true
                    return "success"
                on error
                    return "error"
                end try
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0 and 'success' in result.stdout:
                self.dependencies['accessibility_permission'].status = DependencyStatus.INSTALLED
                self.dependencies['accessibility_permission'].version = "已授权"
            else:
                self.dependencies['accessibility_permission'].status = DependencyStatus.NOT_INSTALLED
                self.dependencies['accessibility_permission'].error_message = "需要在系统设置中授予辅助功能权限"
        except Exception as e:
            self.dependencies['accessibility_permission'].status = DependencyStatus.UNKNOWN
            self.dependencies['accessibility_permission'].error_message = f"检查失败: {str(e)}"
    
    def _get_model_path(self, model_type: str) -> Optional[Path]:
        """获取模型文件路径"""
        try:
            # 从设置管理器获取模型路径
            from settings_manager import SettingsManager
            settings = SettingsManager()
            
            if model_type == 'asr':
                path_str = settings.get_setting('asr.model_path')
            elif model_type == 'punc':
                path_str = settings.get_setting('asr.punc_model_path')
            else:
                return None
            
            if path_str:
                return Path(path_str)
        except Exception as e:
            self.logger.error(f"获取{model_type}模型路径失败: {e}")
        
        return None
    
    def install_dependency(self, dep_name: str) -> Tuple[bool, str]:
        """安装指定依赖"""
        if dep_name not in self.dependencies:
            return False, f"未知的依赖项: {dep_name}"
        
        try:
            if dep_name == 'conda':
                return self._install_conda()
            elif dep_name == 'funasr_env':
                return self._install_funasr_env()
            elif dep_name == 'asr_model':
                return self._install_asr_model()
            elif dep_name == 'punc_model':
                return self._install_punc_model()
            else:
                return False, f"不支持自动安装: {dep_name}"
        except Exception as e:
            self.logger.error(f"安装{dep_name}失败: {e}")
            return False, str(e)
    
    def _install_conda(self) -> Tuple[bool, str]:
        """安装Conda"""
        # 这里应该实现Conda的自动安装逻辑
        # 由于复杂性，暂时返回提示信息
        return False, "请手动安装Miniconda或Anaconda"
    
    def _install_funasr_env(self) -> Tuple[bool, str]:
        """创建FunASR环境"""
        try:
            # 创建conda环境
            cmd = ['conda', 'create', '-n', 'funasr_env', 'python=3.10', '-y']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                return True, "FunASR环境创建成功"
            else:
                return False, f"创建环境失败: {result.stderr}"
        except Exception as e:
            return False, str(e)
    
    def _install_asr_model(self) -> Tuple[bool, str]:
        """下载ASR模型"""
        # 这里应该实现模型下载逻辑
        return False, "模型下载功能待实现"
    
    def _install_punc_model(self) -> Tuple[bool, str]:
        """下载标点模型"""
        # 这里应该实现模型下载逻辑
        return False, "模型下载功能待实现"
    
    def get_dependency_summary(self) -> Dict[str, int]:
        """获取依赖状态摘要"""
        summary = {
            'total': len(self.dependencies),
            'installed': 0,
            'not_installed': 0,
            'issues': 0
        }
        
        for dep in self.dependencies.values():
            if dep.status == DependencyStatus.INSTALLED:
                summary['installed'] += 1
            elif dep.status == DependencyStatus.NOT_INSTALLED:
                summary['not_installed'] += 1
            elif dep.status in [DependencyStatus.VERSION_MISMATCH, DependencyStatus.CORRUPTED]:
                summary['issues'] += 1
            # UNKNOWN状态的依赖不计入任何类别，直到检查完成
        
        return summary
    
    def export_dependency_report(self) -> str:
        """导出依赖检查报告"""
        report = ["# 依赖检查报告\n"]
        report.append(f"检查时间: {self._get_current_time()}\n")
        report.append(f"系统信息: {platform.system()} {platform.release()}\n")
        
        summary = self.get_dependency_summary()
        report.append(f"\n## 摘要")
        report.append(f"- 总计: {summary['total']}")
        report.append(f"- 已安装: {summary['installed']}")
        report.append(f"- 未安装: {summary['not_installed']}")
        report.append(f"- 有问题: {summary['issues']}")
        
        report.append(f"\n## 详细信息")
        for name, dep in self.dependencies.items():
            report.append(f"\n### {dep.name}")
            report.append(f"- 状态: {dep.status.value}")
            if dep.version:
                report.append(f"- 版本: {dep.version}")
            if dep.error_message:
                report.append(f"- 错误: {dep.error_message}")
        
        return "\n".join(report)
    
    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")