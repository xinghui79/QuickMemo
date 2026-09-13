import ctypes
import ctypes.wintypes
from PyQt6.QtCore import QAbstractNativeEventFilter

MOD_ALT = 0x0001
MOD_NOREPEAT = 0x4000  # 禁用按住不放时的系统级热键连发
VK_M = 0x4D
WM_HOTKEY = 0x0312
HOTKEY_ID = 1

class HotkeyFilter(QAbstractNativeEventFilter):
    def __init__(self, tray_manager):
        super().__init__()
        self.tray_manager = tray_manager

    def nativeEventFilter(self, eventType, message):
        if eventType == b"windows_generic_MSG":
            try:
                msg = ctypes.wintypes.MSG.from_address(int(message))
                if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                    self.tray_manager.toggle_all_windows_visibility()
                    return True, 0
            except Exception:
                pass
        return False, 0
