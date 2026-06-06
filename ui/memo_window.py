import json
from pathlib import Path
from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QTextEdit, 
                             QPushButton, QLabel, QHBoxLayout, QMessageBox, 
                             QSizeGrip, QApplication)
from PyQt5.QtCore import Qt, QTimer, QStandardPaths
from PyQt5.QtGui import QFont, QCursor

class QuickMemo(QMainWindow):
    APP_NAME = "QuickMemo"
    DEFAULT_CONTENT = ""
    WINDOW_WIDTH = 250
    WINDOW_HEIGHT = 180

    # === 样式表 (Stylesheets) ===
    STYLE_TITLE_BAR = """
        background-color: #333333;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
    """
    STYLE_ADD_BTN = """
        QPushButton {
            background-color: transparent;
            color: #CCCCCC;
            border: none;
            font-weight: bold;
            border-radius: 4px;
        }
        QPushButton:hover { background-color: #107C10; color: white; }
        QPushButton:pressed { background-color: #0b5a0b; }
    """
    STYLE_PIN_BTN = """
        QPushButton {{
            background-color: transparent;
            color: {color};
            border: none;
            font-weight: bold;
            border-radius: 4px;
        }}
        QPushButton:hover {{ background-color: #FFD700; color: white;}}
        QPushButton:pressed {{ background-color: #222222; }}
    """
    STYLE_HIDE_BTN = """
        QPushButton {
            background-color: transparent; color: #CCCCCC; border: none;
            font-weight: bold; border-radius: 4px;
        }
        QPushButton:hover { background-color: #0078D7; color: white; }
        QPushButton:pressed { background-color: #005A9E; }
    """
    STYLE_CLOSE_BTN = """
        QPushButton {
            background-color: transparent;
            color: #CCCCCC;
            border: none;
            font-weight: bold;
            border-radius: 4px;
        }
        QPushButton:hover { background-color: #e81123; color: white; }
        QPushButton:pressed { background-color: #a80a1a; }
    """
    STYLE_CONTENT_AREA = """
        QWidget#content_container {
            background-color: #FFFFE0;
            border: 1px solid #FFD700;
            border-radius: 0 0 8px 8px;
            border-top: none;
        }
        QSizeGrip:hover {
            background-color: rgba(0, 0, 0, 0.05);
            border: 2px solid #FFD700;
            border-top: none;
            border-left: none;
        }
    """
    STYLE_TEXT_EDIT = """
        QTextEdit {
            background-color: transparent;
            border: none;
            padding: 0; margin: 0;
            selection-background-color: #3399FF;
            selection-color: white;
        }
        QScrollBar:vertical {
            background: transparent; width: 6px; margin: 0;
        }
        QScrollBar::handle:vertical {
            background: rgba(0, 0, 0, 0.2); border-radius: 3px; min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background: rgba(0, 0, 0, 0.4);
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
    """

    def __init__(self, tray_manager=None, is_new=False):
        super().__init__()
        self.title_bar = None
        self.content_widget = None
        self._drag_pos = None
        self.tray_manager = tray_manager
        self.window_id = self.tray_manager.get_next_window_id() if self.tray_manager else 1
        self.is_pinned = False
        self.pin_btn = None

        self.config_path = self._get_config_path()
        self.setMinimumSize(180, 120)
        self.current_content = self._load_data(skip_position=is_new)
        self._setup_ui()

        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self._save_data)
        self.text_edit.textChanged.connect(self._on_text_changed)

        if tray_manager:
            self.tray_manager.add_window(self)

    def _get_config_path(self) -> Path:
        """获取跨平台的配置文件路径"""
        doc_dir = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        config_dir = Path(doc_dir) / self.APP_NAME
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / f"settings_{self.window_id}.json"

    def _setup_ui(self):
        """构建用户界面"""
        # 窗口基础属性
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.CustomizeWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        if not self.config_path.exists():
            self.resize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)

        # --- 标题栏 ---
        self.title_bar = self._create_title_bar()
        self.content_widget = self._create_content_area()
        # --- 布局组装 ---
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.title_bar)
        main_layout.addWidget(self.content_widget)
        container = QWidget()
        container.setLayout(main_layout)
        container.setAttribute(Qt.WA_TranslucentBackground)
        self.setCentralWidget(container)

        self.size_grip = QSizeGrip(self)
        self.size_grip.setFixedSize(20, 20)
        self.size_grip.setStyleSheet("""
            QSizeGrip {
                background-color: transparent;
                border: none;
                image: none; /* 强制清除系统默认的斜线纹理 */
            }
            QSizeGrip:hover {
                background-color: rgba(0, 0, 0, 0.08);
                border-radius: 0 0 8px 0; /* 贴合便签右下角圆角 */
                border-right: 2px solid #FFD700;
                border-bottom: 2px solid #FFD700;
            }
        """)
        # 初始定位到右下角
        self.size_grip.move(
            self.width() - self.size_grip.width(),
            self.height() - self.size_grip.height(),
        )
        self.size_grip.raise_()

    def _create_title_bar(self) -> QWidget:
        """创建自定义标题栏"""
        bar = QWidget()
        bar.setFixedHeight(28)
        bar.setStyleSheet(self.STYLE_TITLE_BAR)
        bar.setObjectName("title_bar")

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 0, 5, 0)

        title_label = QLabel(self.APP_NAME)
        title_label.setStyleSheet("color: white; font-weight: bold;")
        title_label.setFont(QFont("Microsoft YaHei", 9))
        title_label.setAlignment(Qt.AlignVCenter)
        title_label.setAttribute(Qt.WA_TransparentForMouseEvents)

        add_btn = QPushButton("+")
        add_btn.setFixedSize(28, 28)
        add_btn.setFont(QFont("Arial", 14, QFont.Bold))
        add_btn.setCursor(QCursor(Qt.PointingHandCursor))
        add_btn.setStyleSheet(self.STYLE_ADD_BTN)
        add_btn.setToolTip("新建便签")
        add_btn.clicked.connect(self.create_memo)

        self.pin_btn = QPushButton("▲")
        self.pin_btn.setFixedSize(28, 28)
        self.pin_btn.setFont(QFont("Segoe UI Emoji", 11))
        self.pin_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.pin_btn.setToolTip("置顶/取消置顶")
        self.pin_btn.clicked.connect(self.toggle_pin)
        # 根据加载的状态设置初始颜色
        initial_color = "#FFFFFF" if self.is_pinned else "#666666"
        self.pin_btn.setStyleSheet(self.STYLE_PIN_BTN.format(color=initial_color))

        hide_btn = QPushButton("v")
        hide_btn.setFixedSize(28, 28)
        hide_btn.setFont(QFont("Arial", 12, QFont.Bold))
        hide_btn.setCursor(QCursor(Qt.PointingHandCursor))
        hide_btn.setStyleSheet(self.STYLE_HIDE_BTN)
        hide_btn.setToolTip("隐藏便签")
        hide_btn.clicked.connect(self.hide_memo)

        close_btn = QPushButton("×")
        close_btn.setFixedSize(28, 28)
        close_btn.setFont(QFont("Arial", 12, QFont.Bold))
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setStyleSheet(self.STYLE_CLOSE_BTN)
        close_btn.setToolTip("销毁便签")
        close_btn.clicked.connect(self.delete_memo)

        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(add_btn)
        layout.addWidget(self.pin_btn)
        layout.addWidget(hide_btn)
        layout.addWidget(close_btn)
        return bar

    def _create_content_area(self) -> QWidget:
        """创建文本编辑区域"""
        widget = QWidget()
        widget.setObjectName("content_container")
        widget.setStyleSheet(self.STYLE_CONTENT_AREA)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 8, 10, 10)

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("请输入文字...")
        self.text_edit.setPlainText(self.current_content)
        self.text_edit.setStyleSheet(self.STYLE_TEXT_EDIT)
        self.text_edit.setFont(QFont("Microsoft YaHei", 10))
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_edit.setLineWrapMode(QTextEdit.WidgetWidth)

        layout.addWidget(self.text_edit)

        return widget

    def _on_text_changed(self):
        """文本改变时，重启 1.5 秒的防抖定时器"""
        self.save_timer.start(1500)

    def resizeEvent(self, event):
        """重写窗口大小改变事件，确保 QSizeGrip 始终跟随右下角"""
        super().resizeEvent(event)
        if hasattr(self, 'size_grip'):
            grip_x = self.width() - self.size_grip.width()
            grip_y = self.height() - self.size_grip.height()
            self.size_grip.move(grip_x, grip_y)
            self.size_grip.raise_()

    def toggle_pin(self):
        """切换窗口的置顶状态"""
        self.is_pinned = not self.is_pinned

        # 获取当前窗口标志
        flags = self.windowFlags()
        if self.is_pinned:
            # 添加置顶标志
            self.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
            self.pin_btn.setStyleSheet(
                self.STYLE_PIN_BTN.format(color="#FFFFFF")
            )
            self.pin_btn.setToolTip("取消置顶")
        else:
            # 移除置顶标志
            self.setWindowFlags(flags & ~Qt.WindowStaysOnTopHint)
            self.pin_btn.setStyleSheet(
                self.STYLE_PIN_BTN.format(color="#666666")
            )
            self.pin_btn.setToolTip("置顶便签")

        # 在 PyQt 中动态修改 WindowFlags 后，必须重新 show() 才能生效
        self.show()

        # 立即触发保存，记住这个状态
        self._save_data()

    def _load_data(self, skip_position=False) -> str:
        try:
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    content = data.get("content", self.DEFAULT_CONTENT)
                    self.is_pinned = data.get("pinned", False)
                    if not skip_position:
                        x, y = data.get("x"), data.get("y")
                        w, h = data.get("w"), data.get("h")
                        if x is not None and y is not None:
                            self.move(x, y)
                        if w is not None and h is not None:
                            w = max(w, 180)  # 最小宽度 180px
                            h = max(h, 120)  # 最小高度 120px
                            self.resize(w, h)
                        else:
                            self.resize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
                    return content
        except Exception as e:
            print(f"[Load Error] {e}")
        return self.DEFAULT_CONTENT

    def _save_data(self):
        content = self.text_edit.toPlainText()
        geo = self.geometry()
        temp_path = self.config_path.with_suffix(".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "content": content,
                        "x": geo.x(),
                        "y": geo.y(),
                        "w": geo.width(),
                        "h": geo.height(),
                        "pinned": self.is_pinned,
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
            if self.config_path.exists():
                self.config_path.unlink()
            temp_path.rename(self.config_path)
        except Exception as e:
            print(f"[Save Error] {e}")
            if temp_path.exists():
                temp_path.unlink()

    def create_memo(self):
        """新建便签"""
        if self.tray_manager:
            self.tray_manager.create_new_window_slot()

    def hide_memo(self):
        """隐藏便签"""
        if self.save_timer.isActive():
            self.save_timer.stop()
            self._save_data()
        self.hide()
        if self.tray_manager:
            self.tray_manager._sensor_timer.start(100)

    def delete_memo(self):
        """销毁便签"""
        # === 核心逻辑：检查是否是最后一个窗口 ===
        if self.tray_manager and len(self.tray_manager.windows) <= 1:
            QMessageBox.warning(
                self,
                "QuickMemo提示",
                "需保留至少一个便签\n退出程序请右键托盘图标",
                QMessageBox.Ok,
            )
            return
        if self.save_timer.isActive():
            self.save_timer.stop()
            self._save_data()
        try:
            if self.config_path.exists():
                self.config_path.unlink()
        except Exception as e:
            print(f"删除配置文件失败: {e}")
        if self.tray_manager:
            self.tray_manager.remove_window(self)
        self.deleteLater()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            child = self.childAt(event.pos())
            if child == self.title_bar or (
                child and child.parent() == self.title_bar and not isinstance(child, QPushButton)
            ):
                self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()
            else:
                # 明确忽略非标题栏的点击，让事件正常传递给 QTextEdit
                event.ignore()

    def mouseMoveEvent(self, event):
        # 增加 getattr 防护，极端情况下防止 _drag_pos 未定义报错
        if event.buttons() == Qt.LeftButton and getattr(self, '_drag_pos', None) is not None:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = None
            event.accept()

    def closeEvent(self, event):
        """拦截系统级关闭事件 (如 Alt+F4)，将其转为隐藏到托盘"""
        self.hide_memo()
        event.ignore()

    def _keep_on_screen(self):
        """防止窗口飞出屏幕边缘，如果出界则自动换行或拉回"""
        screen = QApplication.primaryScreen().availableGeometry()
        x, y = self.x(), self.y()
        w, h = self.width(), self.height()

        # 如果超出右边界，回到左侧（换行）
        if x + w > screen.right():
            x = screen.left() + 20
            y += h + 20  # 换行后，Y轴向下一个窗口的高度

        # 如果超出下边界，回到顶部
        if y + h > screen.bottom():
            y = screen.top() + 40

        # 确保不会超出左/上边界
        x = max(x, screen.left() + 10)
        y = max(y, screen.top() + 10)

        self.move(x, y)

    def bring_to_front(self):
        """将窗口置顶显示"""
        self.show()
        self.raise_()
        self.activateWindow()
