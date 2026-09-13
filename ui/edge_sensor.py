from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor


class EdgeSensor(QWidget):
    """状态绝对同步、支持四向边缘吸附的边缘感应条"""

    # === 配置参数 ===
    THICKNESS = 6  # 贴边方向的厚度（细边）
    LENGTH = 80  # 平行于边缘方向的长度
    DEFAULT_Y_RATIO = 0.3  # 默认位置：距可用区域顶部的比例（0=顶 1=底）

    def __init__(self, tray_manager):
        super().__init__(
            None, Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.tray_manager = tray_manager
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 状态变量
        self.is_hovered = False  # 鼠标是否悬停
        self.is_horizontal = False  # 当前是横向(上下边缘)还是竖向(左右边缘)

        self._drag_pos = None
        self._press_pos = None

        # 初始化尺寸和位置（默认右侧居中，竖向）
        self.resize(self.THICKNESS, self.LENGTH)
        self._init_position()

    def _init_position(self):
        """初始化感应条位置（默认右侧偏上）"""
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.right() - self.THICKNESS
        y = int(screen.height() * self.DEFAULT_Y_RATIO) - self.LENGTH // 2
        self.move(x, y)

    # ================= 动态获取真实状态 =================

    def _get_sensor_state(self):
        """
        检测便签的整体显示状态，返回三种状态之一：
        - 'all_visible': 都没有隐藏（全在屏幕上）
        - 'all_hidden': 所有都隐藏了
        - 'mixed': 部分显示，部分隐藏
        """
        if not self.tray_manager or not self.tray_manager.windows:
            return 'all_hidden'  # 如果没有便签，视为全隐藏状态

        total = len(self.tray_manager.windows)
        visible_count = 0
        
        for win in self.tray_manager.windows:
            # 排除正在播放滑入动画（尚未完全显示）的窗口
            is_sliding_in = getattr(win, "_is_sliding_in", False)
            if not win.isHidden() and not is_sliding_in:
                visible_count += 1

        if visible_count == 0:
            return 'all_hidden'
        elif visible_count == total:
            return 'all_visible'
        else:
            return 'mixed'

    # ================= 交互事件 =================

    def enterEvent(self, event):
        self.is_hovered = True
        self.update()  # 触发重绘，重新检测窗口状态
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.globalPosition().toPoint()
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton and self._drag_pos:
            if (event.globalPosition().toPoint() - self._press_pos).manhattanLength() > 5:
                self.move(event.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._press_pos is not None:
            # 判断是点击还是拖动
            if (event.globalPosition().toPoint() - self._press_pos).manhattanLength() <= 5:
                self._toggle_windows()
            else:
                self._snap_to_edge()

            self._drag_pos = None
            self._press_pos = None
        super().mouseReleaseEvent(event)

    # ================= 核心逻辑 =================

    def _toggle_windows(self):
        """点击切换显示/隐藏（严格基于三态逻辑）"""
        if not self.tray_manager:
            return

        # 获取当前的三态状态
        state = self._get_sensor_state()

        # 根据状态执行对应的操作
        if state == 'all_visible':
            # 【灰色状态】所有便签都在屏幕上 -> 点击后：隐藏所有便签
            for win in self.tray_manager.windows:
                if hasattr(win, "hide_memo"):
                    win.hide_memo()
        else:
            # 【黄色状态】所有都隐藏了 -> 点击后：显示所有便签
            # 【橙色状态】有隐藏也有显示的 -> 点击后：把隐藏的召唤出来（显示所有）
            self.tray_manager.slide_out_all_windows()

        # 状态改变后，立即触发重绘刷新颜色
        self.update()

    def _snap_to_edge(self):
        """自动吸附到最近的边缘，并自动切换横/竖方向"""
        screen = QApplication.primaryScreen().availableGeometry()
        geo = self.geometry()
        center = geo.center()

        dist_left = center.x() - screen.left()
        dist_right = screen.right() - center.x()
        dist_top = center.y() - screen.top()
        dist_bottom = screen.bottom() - center.y()

        min_dist = min(dist_left, dist_right, dist_top, dist_bottom)
        new_x, new_y = geo.x(), geo.y()

        if min_dist in (dist_left, dist_right):
            self.is_horizontal = False
            self.resize(self.THICKNESS, self.LENGTH)
            new_x = (
                screen.left()
                if min_dist == dist_left
                else screen.right() - self.THICKNESS
            )
            new_y = max(screen.top(), min(geo.y(), screen.bottom() - self.LENGTH))
        else:
            self.is_horizontal = True
            self.resize(self.LENGTH, self.THICKNESS)
            new_y = (
                screen.top()
                if min_dist == dist_top
                else screen.bottom() - self.THICKNESS
            )
            new_x = max(screen.left(), min(geo.x(), screen.right() - self.LENGTH))

        self.move(new_x, new_y)

    # ================= UI 绘制 =================

    def paintEvent(self, event):
        """严格根据【三态逻辑】绘制感应条颜色"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 获取当前的三态状态
        state = self._get_sensor_state()

        # === 严格遵循您的颜色逻辑 ===
        if state == 'mixed':
            # 橙色：部分显示，部分隐藏（有便签在屏幕上，也有便签被隐藏）
            color = QColor(255, 140, 0, 220)  
        elif state == 'all_hidden':
            # 黄色：所有便签都隐藏了
            color = QColor(255, 215, 0, 240)  
        else: 
            # 灰色：都没有隐藏（所有便签都在屏幕上）
            color = QColor(200, 200, 200, 120)  

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)

        # 平时贴外边缘只画 4px，悬停时向屏幕内侧扩展到全厚 6px，形成可见的"变粗"反馈
        screen = QApplication.primaryScreen().availableGeometry()
        t = self.THICKNESS if self.is_hovered else self.THICKNESS - 2

        if self.is_horizontal:
            rect_h = t
            rect_w = self.width() - 2
            rect_x = 1
            rect_y = 0 if self.y() == screen.top() else self.height() - t
        else:
            rect_w = t
            rect_h = self.height() - 2
            rect_y = 1
            rect_x = 0 if self.x() == screen.left() else self.width() - t

        painter.drawRoundedRect(rect_x, rect_y, rect_w, rect_h, 3, 3)
