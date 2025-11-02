from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QFont, QFontDatabase
import sys
import os
import json


class CPSWindow(QWidget):
    def __init__(self, cps_value, click_list=None):
        super().__init__()
        self.cps_value = cps_value
        self._click_list = click_list

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        # make outside transparent so we can draw a rounded background
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(120, 36)

        # try load font from assets folder like fps GUI
        self._font_family = None
        try:
            base = os.path.dirname(os.path.dirname(__file__))
            font_path = os.path.join(base, 'assets', 'AiDianFengYaHei（ShangYongMianFei）-2.ttf')
            if os.path.exists(font_path):
                id_ = QFontDatabase.addApplicationFont(font_path)
                families = QFontDatabase.applicationFontFamilies(id_)
                if families:
                    self._font_family = families[0]
        except Exception:
            self._font_family = None

        if self._font_family:
            self._font = QFont(self._font_family, 11)
        else:
            self._font = QFont("Segoe UI", 11)

        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self.update)
        self._update_timer.start(200)

        # support dragging
        self._drag_pos = None

        # try restore last saved position
        try:
            pos_file = os.path.join(os.path.dirname(__file__), 'cps.pos.json')
            if os.path.exists(pos_file):
                with open(pos_file, 'r', encoding='utf-8') as f:
                    d = json.load(f)
                    x = d.get('x')
                    y = d.get('y')
                    if isinstance(x, int) and isinstance(y, int):
                        try:
                            self.move(x, y)
                        except Exception:
                            pass
        except Exception:
            pass

    def paintEvent(self, event):
        p = QPainter(self)
        # rounded background (allow corners to be transparent)
        p.setRenderHint(QPainter.Antialiasing, True)
        rect = self.rect().adjusted(0, 0, 0, 0)
        bg = QColor(0, 0, 0, 230)
        p.setPen(Qt.NoPen)
        p.setBrush(bg)
        try:
            p.drawRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), 8, 8)
        except Exception:
            p.fillRect(self.rect(), QColor(0, 0, 0))

        # get value
        try:
            val = int(self.cps_value.value)
        except Exception:
            val = 0
        text = f"{val} CPS"

        p.setFont(self._font)
        p.setPen(QColor(255, 255, 255))
        rect = self.rect().adjusted(0, 0, 0, -2)
        p.drawText(rect, Qt.AlignCenter, text)

        # thin border (rounded)
        base_color = QColor(255, 255, 255, 30)
        p.setPen(base_color)
        p.setBrush(Qt.NoBrush)
        rect = self.rect().adjusted(1, 1, -1, -1)
        try:
            p.drawRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), 6, 6)
        except Exception:
            p.drawRect(rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.LeftButton:
            newpos = event.globalPosition().toPoint() - self._drag_pos
            self.move(newpos)

    def mouseReleaseEvent(self, event):
        # record click timestamp into shared manager.list if provided
        try:
            if event.button() == Qt.LeftButton and self._click_list is not None:
                import time as _time
                try:
                    self._click_list.append(_time.time())
                except Exception:
                    pass
        except Exception:
            pass
        self._drag_pos = None

    def closeEvent(self, event):
        # save current top-left position to file
        try:
            geo = self.frameGeometry().topLeft()
            x = int(geo.x())
            y = int(geo.y())
            pos_file = os.path.join(os.path.dirname(__file__), 'cps.pos.json')
            with open(pos_file, 'w', encoding='utf-8') as f:
                json.dump({'x': x, 'y': y}, f)
        except Exception:
            pass
        event.accept()


def run_gui(cps_value, click_list=None):
    app = QApplication(sys.argv)
    w = CPSWindow(cps_value, click_list=click_list)
    w.show()
    try:
        app.exec()
    except Exception:
        pass
