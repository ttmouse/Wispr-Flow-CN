import os
import sys

def get_resource_path(relative_path):
    """获取资源文件的绝对路径，兼容开发环境和打包环境"""
    try:
        # 如果是打包后的应用
        if getattr(sys, 'frozen', False):
            # PyInstaller 打包后的路径
            if hasattr(sys, '_MEIPASS'):
                # 临时解压目录
                base_path = sys._MEIPASS
            else:
                # 应用程序目录
                base_path = os.path.dirname(sys.executable)
        else:
            # 开发环境，从src目录向上查找
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        resource_path = os.path.join(base_path, relative_path)
        
        # 检查文件是否存在
        if os.path.exists(resource_path):
            return resource_path
        
        # 如果在预期位置找不到，尝试其他可能的位置
        alternative_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', relative_path),
            os.path.join(os.getcwd(), relative_path),
            relative_path  # 最后尝试相对路径
        ]
        
        for alt_path in alternative_paths:
            if os.path.exists(alt_path):
                return alt_path
        
        return relative_path  # 返回原始路径作为后备
        
    except Exception as e:
        import logging
        logging.error(f"获取资源路径失败: {e}")
        return relative_path

def get_icon_path(icon_name):
    """获取图标文件路径"""
    return get_resource_path(f"resources/{icon_name}")

def get_audio_path(audio_name):
    """获取音频文件路径"""
    return get_resource_path(f"resources/{audio_name}")