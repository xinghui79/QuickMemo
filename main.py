import sys
import time
import socket
import ctypes
import threading
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QTimer

from core.tray_manager import GlobalTrayManager
from core.hotkey import HotkeyFilter
from core.server import start_server, SERVER_HOST, SERVER_PORT

def _notify_running_instance() -> bool:
    """连接已运行实例让其弹出便签；重试一次，覆盖开机冷启动尚未完成绑定的窗口期"""
    for attempt in range(2):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(1.0)
        try:
            client_socket.connect((SERVER_HOST, SERVER_PORT))
            client_socket.sendall("CREATE_NEW_WINDOW".encode("utf-8"))
            time.sleep(0.1)
            return True
        except (ConnectionRefusedError, socket.timeout, OSError):
            if attempt == 0:
                time.sleep(0.7)
        finally:
            try:
                client_socket.close()
            except Exception:
                pass
    return False

def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("com.yourcompany.QuickMemo")

    if _notify_running_instance():
        sys.exit(0)

    is_silent_start = "--silent" in sys.argv
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    global_tray = GlobalTrayManager(app, icon_path=None)
    hotkey_filter = HotkeyFilter(global_tray)
    app.installNativeEventFilter(hotkey_filter)
    app.commitDataRequest.connect(global_tray.discard_session_data)

    server_thread = threading.Thread(target=start_server, args=(global_tray,), daemon=True)
    server_thread.start()

    global_tray.prepare_new_session(show=not is_silent_start)

    QTimer.singleShot(100, global_tray.update_sensor_visibility)
    ret = app.exec_()
    global_tray.quit_app()
    sys.exit(ret)

if __name__ == "__main__":
    main()