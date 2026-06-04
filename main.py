import sys
import json
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QTextEdit,
    QPushButton,
    QLabel,
    QHBoxLayout,
)
from PyQt5.QtCore import Qt, QStandardPaths, QTimer, QPoint
from PyQt5.QtGui import QFont, QCursor


class SnapMemo(QMainWindow):
    """SnapMemo: A lightweight desktop sticky note application."""

    # === 配置常量 ===
    APP_NAME = "SnapMemo"
    CONFIG_FILE = "settings.json"
    DEFAULT_CONTENT = ""
    WINDOW_WIDTH = 250
    WINDOW_HEIGHT = 180

    # === 样式表 (Stylesheets) ===
    STYLE_TITLE_BAR = """
        background-color: #333333;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
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
        background-color: #FFFFE0;
        border: 1px solid #FFD700;
        border-radius: 0 0 8px 8px;
        border-top: none;
    """
    STYLE_TEXT_EDIT = """
        QTextEdit {
            background-color: transparent;
            border: none;
            padding: 0; margin: 0;
            selection-background-color: #3399FF;
        }
    """

    def __init__(self):
        super().__init__()
        self._drag_pos = None

        # 初始化数据路径
        self.config_path = self._get_config_path()

        # 加载数据并初始化界面
        self.current_content = self._load_data()
        self._setup_ui()

        # 自动保存定时器 (30分钟 = 30 * 60 * 1000 毫秒)
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self._save_data)
        self.auto_save_timer.start(30 * 60 * 1000)

    def _get_config_path(self) -> Path:
        """获取跨平台的配置文件路径"""
        doc_dir = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        config_dir = Path(doc_dir) / self.APP_NAME
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / self.CONFIG_FILE

    def _setup_ui(self):
        """构建用户界面"""
        # 窗口基础属性
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.resize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)

        # --- 标题栏 ---
        title_bar = self._create_title_bar()

        # --- 内容区域 ---
        content_widget = self._create_content_area()

        # --- 布局组装 ---
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(title_bar)
        main_layout.addWidget(content_widget)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def _create_title_bar(self) -> QWidget:
        """创建自定义标题栏"""
        bar = QWidget()
        bar.setFixedHeight(28)
        bar.setStyleSheet(self.STYLE_TITLE_BAR)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 0, 5, 0)

        title_label = QLabel("SnapMemo")
        title_label.setStyleSheet("color: white; font-weight: bold;")
        title_label.setFont(QFont("Microsoft YaHei", 9))
        title_label.setAlignment(Qt.AlignVCenter)

        close_btn = QPushButton("×")
        close_btn.setFixedSize(28, 28)
        close_btn.setFont(QFont("Arial", 12, QFont.Bold))
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setStyleSheet(self.STYLE_CLOSE_BTN)
        close_btn.clicked.connect(self.close)

        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(close_btn)
        return bar

    def _create_content_area(self) -> QWidget:
        """创建文本编辑区域"""
        widget = QWidget()
        widget.setStyleSheet(self.STYLE_CONTENT_AREA)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 8, 10, 10)

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("请输入文字...")
        self.text_edit.setPlainText(self.current_content)
        self.text_edit.setStyleSheet(self.STYLE_TEXT_EDIT)
        self.text_edit.setFont(QFont("Microsoft YaHei", 10))

        layout.addWidget(self.text_edit)
        return widget

    def _on_screen(self):
        """将窗口定位到屏幕右侧居中"""
        screen = QApplication.primaryScreen().geometry()
        x = screen.width() - self.width() - 20
        y = max(50, (screen.height() - self.height()) // 2)
        self.move(x, y)

    # === 数据持久化逻辑 ===

    def _load_data(self) -> str:
        """从 JSON 文件加载便签内容"""
        try:
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    content = data.get("content", self.DEFAULT_CONTENT)
                    x = data.get("x")
                    y = data.get("y")
                    if x is not None and y is not None:
                        self.move(x, y)
                    else:
                        self._on_screen()
                return content
        except Exception as e:
            print(f"[SnapMemo] Load Error: {e}")
        return self.DEFAULT_CONTENT

    def _save_data(self):
        """将当前内容保存到 JSON 文件"""
        content = self.text_edit.toPlainText()
        pos = self.pos()
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(
                    {"content": content, "x": pos.x(), "y": pos.y()},
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception as e:
            print(f"[SnapMemo] Save Error: {e}")

    # === 事件处理 ===

    def mousePressEvent(self, event):
        """处理鼠标按下事件（用于拖拽）"""
        if event.button() == Qt.LeftButton and event.pos().y() <= 28:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """处理鼠标移动事件（实现窗口拖拽）"""
        if event.buttons() == Qt.LeftButton and self._drag_pos is not None:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def closeEvent(self, event):
        """窗口关闭前自动保存"""
        self._save_data()
        super().closeEvent(event)


if __name__ == "__main__":
    # 启用高 DPI 支持（可选，视系统而定）
    # QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # 统一控件风格

    window = SnapMemo()
    window.show()
    sys.exit(app.exec_())
