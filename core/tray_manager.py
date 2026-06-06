import ctypes,os
from pathlib import Path
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QMessageBox, QApplication
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer, QPoint, QPropertyAnimation, QEasingCurve, QStandardPaths
from PyQt5.QtGui import QIcon

from core.autostart import AutoStartManager
from core.hotkey import MOD_ALT, VK_M, HOTKEY_ID
from utils.paths import get_resource_path

class GlobalTrayManager(QObject):
    _instance = None
    request_new_window = pyqtSignal()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, app, icon_path=None):
        if self._initialized: return
        super().__init__()
        self.app = app
        self.windows = []
        self._initialized = True
        self.server_socket = None
        self._running = True
        
        self.tray_icon = QSystemTrayIcon(self)
        final_icon_path = None
        
        # 1. 优先使用传入的有效路径
        if icon_path and os.path.exists(icon_path):
            final_icon_path = icon_path
        else:
            # 2. 尝试在 assets 文件夹中查找
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            assets_path = os.path.join(project_root, "assets", "icon.ico")
            
            if os.path.exists(assets_path):
                final_icon_path = assets_path  # ✅ 修复：正确赋值
            else:
                # 3. 兜底：尝试找根目录下的 icon.ico (兼容旧习惯)
                root_icon = os.path.join(project_root, "icon.ico")
                if os.path.exists(root_icon):
                    final_icon_path = root_icon

        # ✅ 修复：使用最终确定的 final_icon_path 来加载图标
        if final_icon_path:
            print(f"✅ 成功找到图标路径: {final_icon_path}")
            original_icon = QIcon(final_icon_path)
            if not original_icon.isNull():
                self.tray_icon.setIcon(QIcon(original_icon.pixmap(32, 32)))
            else:
                print("⚠️ 图标文件存在但无法解析，请检查 ico 文件是否损坏")
        else:
            print("❌ 未找到任何图标文件，请检查 assets/icon.ico 是否存在")

        self.tray_icon.setToolTip("QuickMemo")
        self.request_new_window.connect(self.create_new_window_slot)

        # 菜单设置
        self.menu = QMenu()
        self.menu.addAction("显示所有便签", self.show_all_windows)
        self.menu.addAction("新建便签", self.create_new_window_slot)
        
        self.action_auto_start = QAction("开机自动启动", self)
        self.action_auto_start.setCheckable(True)
        self.action_auto_start.setChecked(AutoStartManager.is_enabled())
        self.action_auto_start.triggered.connect(self.toggle_auto_start)
        self.menu.addAction(self.action_auto_start)
        
        self.menu.addSeparator()
        self.menu.addAction("退出程序", self.quit_app)

        self.tray_icon.setContextMenu(self.menu)
        self.tray_icon.activated.connect(self.on_activated)
        self.tray_icon.show()

        try:
            ctypes.windll.user32.RegisterHotKey(None, HOTKEY_ID, MOD_ALT, VK_M)
        except Exception: pass

        # 延迟导入 UI 组件，避免循环依赖
        from ui.edge_sensor import EdgeSensor
        self.edge_sensor = EdgeSensor(self)
        self.edge_sensor.hide()
        
        self._sensor_timer = QTimer(self)
        self._sensor_timer.setSingleShot(True)
        self._sensor_timer.timeout.connect(self.update_sensor_visibility)

    def get_next_window_id(self):
        existing_ids = {win.window_id for win in self.windows}
        next_id = 1
        while next_id in existing_ids: next_id += 1
        return next_id

    def add_window(self, window):
        if window not in self.windows: self.windows.append(window)

    def remove_window(self, window):
        if window in self.windows: self.windows.remove(window)

    def show_all_windows(self):
        for win in self.windows: win.bring_to_front()
        self.update_sensor_visibility()

    def update_sensor_visibility(self):
        if not self.windows or any(win.isHidden() for win in self.windows):
            self.edge_sensor.show()
            self.edge_sensor.raise_()
        else:
            self.edge_sensor.hide()

    def slide_out_all_windows(self):
        if not self.windows:
            self.create_new_window_slot()
            return
            
        screen = QApplication.primaryScreen().availableGeometry()
        offset, duration = 0, 300

        for win in self.windows:
            if win.isHidden() and not getattr(win, "_is_sliding_in", False):
                target_pos = win.pos()
                start_pos = QPoint(screen.right() + 50, target_pos.y() + offset)
                win.move(start_pos)
                win.show()
                win.raise_()
                win._is_sliding_in = True

                animation = QPropertyAnimation(win, b"pos")
                animation.setDuration(duration)
                animation.setStartValue(start_pos)
                animation.setEndValue(target_pos)
                animation.setEasingCurve(QEasingCurve.OutCubic)
                animation.finished.connect(lambda w=win: setattr(w, "_is_sliding_in", False))
                animation.start()
                win._slide_animation = animation

                offset += 20
                duration += 50
        self.update_sensor_visibility()

    @pyqtSlot()
    def create_new_window_slot(self):
        hidden_windows = [win for win in self.windows if win.isHidden()]
        if hidden_windows:
            for win in hidden_windows: win.bring_to_front()
            return

        # 延迟导入 UI 组件
        from ui.memo_window import QuickMemo
        
        offset_step = 40
        if self.windows:
            last_window = self.windows[-1]
            base_x, base_y = last_window.x() + offset_step, last_window.y() + offset_step
        else:
            screen = QApplication.primaryScreen().availableGeometry()
            base_x = screen.right() - QuickMemo.WINDOW_WIDTH - 50
            base_y = screen.top() + 50
            
        new_window = QuickMemo(tray_manager=self, is_new=True)
        new_window.move(base_x, base_y)
        new_window._keep_on_screen()
        new_window.show()
        new_window.raise_()
        new_window.activateWindow()
        self.update_sensor_visibility()

    def on_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.show_all_windows()

    def toggle_all_windows_visibility(self):
        if not self.windows:
            self.create_new_window_slot()
            return
        if any(win.isHidden() for win in self.windows):
            self.slide_out_all_windows()
        else:
            for win in self.windows: win.hide_memo()
        self.update_sensor_visibility()

    def cleanup_hotkey(self):
        try: ctypes.windll.user32.UnregisterHotKey(None, HOTKEY_ID)
        except Exception: pass

    def toggle_auto_start(self, checked):
        if not AutoStartManager.set_enabled(checked):
            self.action_auto_start.setChecked(not checked)
            QMessageBox.warning(None, "QuickMemo 提示", "设置开机自启失败！\n可能被杀毒软件或系统权限拦截。")

    def quit_app(self):
        self._running = False
        if self.server_socket:
            try: self.server_socket.close()
            except Exception: pass
            
        for win in self.windows:
            if hasattr(win, "save_timer") and win.save_timer.isActive():
                win.save_timer.stop()
                win._save_data()
                
        from ui.memo_window import QuickMemo
        doc_dir = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        config_dir = Path(doc_dir) / QuickMemo.APP_NAME
        if config_dir.exists():
            for file in config_dir.glob("settings_*.*"):
                try: file.unlink()
                except Exception: pass
            try:
                if not any(config_dir.iterdir()): config_dir.rmdir()
            except Exception: pass
        self.app.quit()