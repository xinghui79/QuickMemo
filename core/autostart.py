import sys
import os
import winreg

class AutoStartManager:
    """管理程序的开机自动启动"""
    REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    APP_NAME = "QuickMemo"

    @classmethod
    def get_exe_path(cls):
        if getattr(sys, "frozen", False):
            return f'"{sys.executable}" --silent'
        else:
            python_exe = sys.executable
            script_path = os.path.abspath(sys.argv[0])
            return f'"{python_exe}" "{script_path}"'

    @classmethod
    def is_enabled(cls):
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, cls.REG_PATH, 0, winreg.KEY_READ) as key:
                winreg.QueryValueEx(key, cls.APP_NAME)
                return True
        except FileNotFoundError:
            return False
        except Exception:
            return False

    @classmethod
    def set_enabled(cls, enable: bool):
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, cls.REG_PATH, 0, winreg.KEY_SET_VALUE) as key:
                if enable:
                    winreg.SetValueEx(key, cls.APP_NAME, 0, winreg.REG_SZ, cls.get_exe_path())
                else:
                    try:
                        winreg.DeleteValue(key, cls.APP_NAME)
                    except FileNotFoundError:
                        pass
            return True
        except Exception:
            return False