import socket

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 65479

def start_server(tray_manager):
    """后台线程：监听其他进程的请求"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.settimeout(1.0)
    tray_manager.server_socket = server_socket
    
    try:
        server_socket.bind((SERVER_HOST, SERVER_PORT))
        server_socket.listen(10)
        while tray_manager._running:
            try:
                conn, addr = server_socket.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            try:
                data_bytes = conn.recv(1024)
                if not data_bytes: continue
                data = data_bytes.decode("utf-8").strip()
                if data == "CREATE_NEW_WINDOW":
                    tray_manager.request_new_window.emit()
            except Exception:
                pass
            finally:
                conn.close()
    except OSError:
        pass
    finally:
        server_socket.close()