import os
import sys

def get_resource_path(relative_path):
    """获取资源的绝对路径，兼容 PyInstaller 打包环境"""
    try:
        base_path = sys._MEIPASS
        if not base_path or not os.path.exists(base_path):
            raise ValueError("Invalid _MEIPASS path")
    except (AttributeError, ValueError):
        base_path = os.path.abspath(".")
    return os.path.normpath(os.path.join(base_path, relative_path))