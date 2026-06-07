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
from ui.memo_window import QuickMemo

def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("com.yourcompany.QuickMemo")

    # 单例检测
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(1.0)
    try:
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        client_socket.sendall("CREATE_NEW_WINDOW".encode("utf-8"))
        time.sleep(0.1)
        sys.exit(0)
    except (ConnectionRefusedError, socket.timeout, OSError):
        pass
    finally:
        try: client_socket.close()
        except Exception: pass

    is_silent_start = "--silent" in sys.argv
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    global_tray = GlobalTrayManager(app, icon_path=None)
    hotkey_filter = HotkeyFilter(global_tray)
    app.installNativeEventFilter(hotkey_filter)

    server_thread = threading.Thread(target=start_server, args=(global_tray,), daemon=True)
    server_thread.start()

    if not is_silent_start:
        window = QuickMemo(tray_manager=global_tray)
        window.show()

    QTimer.singleShot(100, global_tray.update_sensor_visibility)
    ret = app.exec_()
    global_tray.quit_app()
    sys.exit(ret)

if __name__ == "__main__":
    main()