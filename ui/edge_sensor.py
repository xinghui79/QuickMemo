from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor

class EdgeSensor(QWidget):
    def __init__(self, tray_manager):
        super().__init__()
        self.tray_manager = tray_manager
        self.is_hovered = False
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.sensor_width = 6
        self.sensor_height = 160
        self.setGeometry(0, 0, self.sensor_width, self.sensor_height)
        self.setMouseTracking(True)

    def showEvent(self, event):
        super().showEvent(event)
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.right() - self.sensor_width + 1
        y = (screen.height() - self.sensor_height) // 2
        self.setGeometry(x, y, self.sensor_width, self.sensor_height)

    def enterEvent(self, event):
        self.is_hovered = True
        self.update()
        if self.tray_manager: self.tray_manager.slide_out_all_windows()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if self.is_hovered:
            color, width = QColor(255, 240, 120, 220), self.sensor_width
        else:
            color, width = QColor(255, 245, 150, 80), self.sensor_width - 2
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        painter.drawRoundedRect(self.width() - width, 0, width, self.height(), 3, 3)