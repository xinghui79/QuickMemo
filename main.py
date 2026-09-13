import sys
import time
import socket
import ctypes
import logging
import threading
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

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
    # Qt6 默认开启高 DPI 缩放与高清像素映射，无需再设置 AA_ 属性
    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("com.yourcompany.QuickMemo")

    if _notify_running_instance():
        sys.exit(0)

    # 主线程预先绑定端口：绑定失败说明端口被占用（已有实例在运行但唤醒失败），
    # 直接退出防止出现没有服务的"僵尸"第二实例
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((SERVER_HOST, SERVER_PORT))
    except OSError as e:
        logging.error(f"端口 {SERVER_PORT} 绑定失败（已有实例占用），退出: {e}")
        sys.exit(1)

    is_silent_start = "--silent" in sys.argv
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    global_tray = GlobalTrayManager(app, icon_path=None)
    hotkey_filter = HotkeyFilter(global_tray)
    app.installNativeEventFilter(hotkey_filter)
    app.commitDataRequest.connect(global_tray.discard_session_data)

    server_thread = threading.Thread(
        target=start_server, args=(server_socket, global_tray), daemon=True
    )
    server_thread.start()

    global_tray.prepare_new_session(show=not is_silent_start)

    QTimer.singleShot(100, global_tray.update_sensor_visibility)
    ret = app.exec()
    global_tray.quit_app()
    sys.exit(ret)

if __name__ == "__main__":
    main()