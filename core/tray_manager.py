import ctypes
import os
import logging
from pathlib import Path
from typing import List, Optional

from PyQt5.QtWidgets import (QSystemTrayIcon, QMenu, QAction, 
                             QMessageBox, QApplication)
from PyQt5.QtCore import (QObject, pyqtSignal, pyqtSlot, QTimer, 
                          QPoint, QPropertyAnimation, QEasingCurve, 
                          QStandardPaths)
from PyQt5.QtGui import QIcon

from core.autostart import AutoStartManager
from core.hotkey import MOD_ALT, VK_M, HOTKEY_ID
from utils.paths import get_resource_path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class GlobalTrayManager(QObject):
    """QuickMemo 全局托盘与窗口管理器 (单例模式)"""
    
    # ================= 常量配置 =================
    ANIMATION_BASE_DURATION = 300  # 基础动画时长(ms)
    ANIMATION_DURATION_STEP = 50   # 每个后续窗口增加的时长
    SLIDE_OFFSET_STEP = 20         # 窗口滑出时的Y轴偏移
    NEW_WINDOW_OFFSET_STEP = 40    # 新建窗口时的XY轴偏移
    SCREEN_EDGE_MARGIN = 50        # 距离屏幕边缘的安全边距
    
    # ================= 信号与单例模式 =================
    _instance: Optional['GlobalTrayManager'] = None
    request_new_window = pyqtSignal()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, app: QApplication, icon_path: str = None):
        if self._initialized:
            return
            
        super().__init__()
        self.app = app
        self.windows: List[QObject] = []  # 使用类型提示明确列表内容
        self._initialized = True
        self._running = True
        self.server_socket = None
        
        # 延迟导入避免循环引用
        from ui.edge_sensor import EdgeSensor
        from ui.memo_window import QuickMemo
        self._QuickMemo = QuickMemo  # 缓存类引用
        
        # 初始化各子模块
        self._setup_tray_icon(icon_path)
        self._setup_menu()
        self._register_global_hotkey()
        
        self.edge_sensor = EdgeSensor(self)
        self.edge_sensor.show()
        self.edge_sensor.raise_()
        
        self._sensor_timer = QTimer(self)
        self._sensor_timer.setSingleShot(True)
        self._sensor_timer.timeout.connect(self.update_sensor_visibility)
        
        self.request_new_window.connect(self.create_new_window_slot)

    # ================= 初始化子模块 =================
    
    def _setup_tray_icon(self, icon_path: str):
        """初始化系统托盘图标"""
        self.tray_icon = QSystemTrayIcon(self)
        final_path = self._resolve_icon_path(icon_path)
        
        if final_path:
            icon = QIcon(final_path)
            if not icon.isNull():
                # 强制缩放到 32x32 保证清晰度
                self.tray_icon.setIcon(QIcon(icon.pixmap(32, 32)))
            else:
                logging.warning(f"图标文件存在但无法解析: {final_path}")
        else:
            logging.error("未找到有效的托盘图标文件")

        self.tray_icon.setToolTip("QuickMemo")
        self.tray_icon.activated.connect(self.on_activated)
        self.tray_icon.show()

    def _resolve_icon_path(self, custom_path: str) -> Optional[str]:
        """解析图标路径，支持自定义路径和默认 assets 路径"""
        if custom_path and os.path.exists(custom_path):
            return custom_path
            
        project_root = Path(__file__).resolve().parent.parent
        default_path = project_root / "assets" / "icon.ico"
        return str(default_path) if default_path.exists() else None

    def _setup_menu(self):
        """构建托盘右键菜单"""
        self.menu = QMenu()
        self.menu.addAction("显示所有便签", self.show_all_windows)
        self.menu.addAction("新建便签", self.create_new_window_slot)
        
        self.action_auto_start = QAction("开机自动启动", self, checkable=True)
        self.action_auto_start.setChecked(AutoStartManager.is_enabled())
        self.action_auto_start.triggered.connect(self.toggle_auto_start)
        self.menu.addAction(self.action_auto_start)
        
        self.menu.addSeparator()
        self.menu.addAction("退出程序", self.quit_app)
        self.tray_icon.setContextMenu(self.menu)

    def _register_global_hotkey(self):
        """注册全局热键"""
        try:
            # 0 表示 None (NULL)
            ctypes.windll.user32.RegisterHotKey(None, HOTKEY_ID, MOD_ALT, VK_M)
        except Exception as e:
            logging.error(f"全局热键注册失败 (可能被其他程序占用): {e}")

    # ================= 窗口管理核心逻辑 =================
    
    def get_next_window_id(self) -> int:
        existing_ids = {getattr(win, 'window_id', 0) for win in self.windows}
        next_id = 1
        while next_id in existing_ids:
            next_id += 1
        return next_id

    def add_window(self, window):
        if window not in self.windows:
            self.windows.append(window)

    def remove_window(self, window):
        if window in self.windows:
            self.windows.remove(window)
            self.update_sensor_visibility()

    def show_all_windows(self):
        for win in self.windows:
            if hasattr(win, 'bring_to_front'):
                win.bring_to_front()
        self.update_sensor_visibility()

    # ================= 动画与可见性控制 =================
    
    def slide_out_all_windows(self):
        """滑出所有隐藏的窗口"""
        if not self.windows:
            self.create_new_window_slot()
            return
            
        screen = QApplication.primaryScreen().availableGeometry()
        offset, duration = 0, self.ANIMATION_BASE_DURATION

        for win in self.windows:
            if win.isHidden() and not getattr(win, "_is_sliding_in", False):
                self._animate_window_slide(win, screen, offset, duration)
                offset += self.SLIDE_OFFSET_STEP
                duration += self.ANIMATION_DURATION_STEP
                
        self.update_sensor_visibility()

    def _animate_window_slide(self, win, screen, offset, duration):
        """执行单个窗口的滑入动画"""
        target_pos = win.pos()
        start_pos = QPoint(screen.right() + 50, target_pos.y() + offset)
        
        win.move(start_pos)
        win.show()
        win.raise_()
        win._is_sliding_in = True

        # 使用属性动画
        animation = QPropertyAnimation(win, b"pos")
        animation.setDuration(duration)
        animation.setStartValue(start_pos)
        animation.setEndValue(target_pos)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # 动画结束后清理状态
        def on_slide_finished():
            win._is_sliding_in = False
            self.update_sensor_visibility()
        animation.finished.connect(on_slide_finished)
        animation.start()
        
        # 保持引用防止被垃圾回收
        win._slide_animation = animation

    def update_sensor_visibility(self):
        """更新边缘传感器的显示状态"""
        if self.edge_sensor:
            self.edge_sensor.show()
            self.edge_sensor.raise_()
            self.edge_sensor.update() 

    # ================= 事件槽函数 =================
    
    @pyqtSlot()
    def create_new_window_slot(self):
        """创建或恢复窗口"""
        hidden_windows = [win for win in self.windows if win.isHidden()]
        if hidden_windows:
            for win in hidden_windows:
                if hasattr(win, 'bring_to_front'):
                    win.bring_to_front()
            return

        offset_step = self.NEW_WINDOW_OFFSET_STEP
        if self.windows:
            last_window = self.windows[-1]
            base_x, base_y = last_window.x() + offset_step, last_window.y() + offset_step
        else:
            screen = QApplication.primaryScreen().availableGeometry()
            base_x = screen.right() - self._QuickMemo.WINDOW_WIDTH - self.SCREEN_EDGE_MARGIN
            base_y = screen.top() + self.SCREEN_EDGE_MARGIN
            
        new_window = self._QuickMemo(tray_manager=self, is_new=True)
        new_window.move(base_x, base_y)
        if hasattr(new_window, '_keep_on_screen'):
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
            for win in self.windows:
                if hasattr(win, 'hide_memo'):
                    win.hide_memo()
        self.update_sensor_visibility()

    # ================= 系统级操作与清理 =================
    
    def toggle_auto_start(self, checked):
        if not AutoStartManager.set_enabled(checked):
            self.action_auto_start.setChecked(not checked)
            QMessageBox.warning(None, "QuickMemo 提示", 
                                "设置开机自启失败！\n可能被杀毒软件或系统权限拦截。")

    def _unregister_global_hotkey(self):
        """注销全局热键"""
        try:
            ctypes.windll.user32.UnregisterHotKey(None, HOTKEY_ID)
        except Exception as e:
            logging.error(f"全局热键注销失败: {e}")

    def _cleanup_temp_files(self):
        """清理临时配置文件"""
        doc_dir = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        config_dir = Path(doc_dir) / self._QuickMemo.APP_NAME
        
        if config_dir.exists():
            for file in config_dir.glob("settings_*.*"):
                try:
                    file.unlink()
                except Exception as e:
                    logging.warning(f"无法删除临时文件 {file}: {e}")
                    
            try:
                if not any(config_dir.iterdir()):
                    config_dir.rmdir()
            except Exception:
                pass

    def quit_app(self):
        """安全退出应用程序"""
        self._running = False
        
        if self.server_socket:
            try: self.server_socket.close()
            except Exception: pass
    
        for win in self.windows:
            if hasattr(win, "save_timer") and win.save_timer.isActive():
                win.save_timer.stop()
                win._save_data()

        self._unregister_global_hotkey()
        self._cleanup_temp_files()
        
        self.app.quit()

