import ctypes
import ctypes.wintypes
from PyQt5.QtCore import QAbstractNativeEventFilter

MOD_ALT = 0x0001
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
                msg = ctypes.wintypes.MSG.from_address(message.__int__())
                if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                    self.tray_manager.toggle_all_windows_visibility()
                    return True, 0
            except Exception:
                pass
        return False, 0
