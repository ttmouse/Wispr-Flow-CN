"""导入管理工具模块"""

# 常用的PyQt6导入
from PyQt6.QtCore import (
    QThread, QTimer, QObject, pyqtSignal, QMutex, QMutexLocker,
    QSettings, QStandardPaths, QDir, QUrl, QSize, Qt
)

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QLineEdit, QComboBox,
    QCheckBox, QSpinBox, QSlider, QProgressBar, QStatusBar,
    QMenuBar, QMenu, QAction, QSystemTrayIcon, QMessageBox,
    QDialog, QDialogButtonBox, QGroupBox, QFrame, QSplitter,
    QScrollArea, QTabWidget, QListWidget, QTreeWidget,
    QTableWidget, QHeaderView, QAbstractItemView
)

from PyQt6.QtGui import (
    QIcon, QPixmap, QFont, QFontMetrics, QPalette, QColor,
    QBrush, QPen, QPainter, QAction, QKeySequence, QCursor,
    QMovie, QTextCursor, QTextDocument, QSyntaxHighlighter
)

# 常用的系统导入
import os
import sys
import json
import time
import threading
import logging
import traceback
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from collections import defaultdict, deque, OrderedDict
from functools import wraps, partial, lru_cache
from contextlib import contextmanager

# 常用的第三方库导入
try:
    import numpy as np
except ImportError:
    np = None

try:
    import pyaudio
except ImportError:
    pyaudio = None

try:
    import requests
except ImportError:
    requests = None

# 导入检查器
class ImportChecker:
    """导入检查器，用于检查模块是否可用"""
    
    _available_modules = {}
    
    @classmethod
    def is_available(cls, module_name: str) -> bool:
        """检查模块是否可用"""
        if module_name in cls._available_modules:
            return cls._available_modules[module_name]
        
        try:
            __import__(module_name)
            cls._available_modules[module_name] = True
            return True
        except ImportError:
            cls._available_modules[module_name] = False
            return False
    
    @classmethod
    def require_module(cls, module_name: str, error_message: str = None):
        """要求模块必须可用，否则抛出异常"""
        if not cls.is_available(module_name):
            if error_message is None:
                error_message = f"Required module '{module_name}' is not available"
            raise ImportError(error_message)
    
    @classmethod
    def get_available_modules(cls) -> Dict[str, bool]:
        """获取所有已检查模块的可用性"""
        return cls._available_modules.copy()

# 常用的导入组合
class CommonImports:
    """常用导入组合"""
    
    @staticmethod
    def get_pyqt_core():
        """获取PyQt核心导入"""
        return {
            'QThread': QThread,
            'QTimer': QTimer,
            'QObject': QObject,
            'pyqtSignal': pyqtSignal,
            'QMutex': QMutex,
            'QMutexLocker': QMutexLocker,
            'Qt': Qt
        }
    
    @staticmethod
    def get_pyqt_widgets():
        """获取PyQt控件导入"""
        return {
            'QApplication': QApplication,
            'QMainWindow': QMainWindow,
            'QWidget': QWidget,
            'QVBoxLayout': QVBoxLayout,
            'QHBoxLayout': QHBoxLayout,
            'QLabel': QLabel,
            'QPushButton': QPushButton,
            'QTextEdit': QTextEdit,
            'QLineEdit': QLineEdit,
            'QComboBox': QComboBox,
            'QCheckBox': QCheckBox,
            'QSystemTrayIcon': QSystemTrayIcon,
            'QMessageBox': QMessageBox
        }
    
    @staticmethod
    def get_pyqt_gui():
        """获取PyQt GUI导入"""
        return {
            'QIcon': QIcon,
            'QPixmap': QPixmap,
            'QFont': QFont,
            'QPalette': QPalette,
            'QColor': QColor,
            'QAction': QAction,
            'QKeySequence': QKeySequence
        }
    
    @staticmethod
    def get_system_imports():
        """获取系统导入"""
        return {
            'os': os,
            'sys': sys,
            'json': json,
            'time': time,
            'threading': threading,
            'logging': logging,
            'traceback': traceback,
            'Path': Path,
            'datetime': datetime,
            'timedelta': timedelta
        }
    
    @staticmethod
    def get_typing_imports():
        """获取类型注解导入"""
        return {
            'Dict': Dict,
            'List': List,
            'Tuple': Tuple,
            'Optional': Optional,
            'Any': Any,
            'Union': Union,
            'Callable': Callable
        }

# 导入管理器
class ImportManager:
    """导入管理器，统一管理项目中的导入"""
    
    def __init__(self):
        self.checker = ImportChecker()
        self.common = CommonImports()
    
    def get_all_common_imports(self) -> Dict[str, Any]:
        """获取所有常用导入"""
        imports = {}
        imports.update(self.common.get_pyqt_core())
        imports.update(self.common.get_pyqt_widgets())
        imports.update(self.common.get_pyqt_gui())
        imports.update(self.common.get_system_imports())
        imports.update(self.common.get_typing_imports())
        return imports
    
    def check_required_modules(self, modules: List[str]) -> Dict[str, bool]:
        """检查必需模块的可用性"""
        results = {}
        for module in modules:
            results[module] = self.checker.is_available(module)
        return results
    
    def get_import_report(self) -> str:
        """获取导入报告"""
        available = self.checker.get_available_modules()
        
        report = ["=== 模块可用性报告 ==="]
        
        for module, is_available in available.items():
            status = "✓" if is_available else "✗"
            report.append(f"{status} {module}")
        
        return "\n".join(report)

# 全局导入管理器实例
import_manager = ImportManager()

# 便捷函数
def check_module(module_name: str) -> bool:
    """检查模块是否可用"""
    return ImportChecker.is_available(module_name)

def require_module(module_name: str, error_message: str = None):
    """要求模块必须可用"""
    ImportChecker.require_module(module_name, error_message)

def get_common_imports() -> Dict[str, Any]:
    """获取所有常用导入"""
    return import_manager.get_all_common_imports()