from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QPainter, QColor, QGuiApplication
import sys
import ctypes
from ctypes import wintypes, byref
import time
import platform
import os
import json

_IS_WINDOWS = platform.system().lower() == 'windows'


class MouseUnderWindowOverlay(QWidget):
    def __init__(self, cfg=None):
        super().__init__()

        # 无边框、置顶、透明背景、工具窗口（不在任务栏）
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # 默认值，可由配置覆盖
        self._border_thickness = 6
        self._hue = 0
        self._corner_radius = 12
        self._current_rect = None  # (x, y, w, h) 逻辑像素
        self._last_time = time.perf_counter()
        self._follow_speed = 0.18
        self._hue_step = 3
        self._tick_interval = 30

        # 应用配置（如果提供）
        if isinstance(cfg, dict):
            self._border_thickness = int(cfg.get('border_thickness', self._border_thickness))
            self._corner_radius = int(cfg.get('corner_radius', self._corner_radius))
            try:
                self._follow_speed = float(cfg.get('follow_speed', self._follow_speed))
            except Exception:
                pass
            try:
                self._hue_step = float(cfg.get('hue_step', self._hue_step))
            except Exception:
                pass
            try:
                self._tick_interval = int(cfg.get('tick_interval_ms', self._tick_interval))
            except Exception:
                pass

        # 更新定时器 - 更新位置与颜色
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(self._tick_interval)

        # 缓存上次目标矩形，避免频繁重设 geometry
        self._last_rect = (0, 0, 0, 0)

        # 平台相关初始化
        if _IS_WINDOWS:
            self.user32 = ctypes.windll.user32
        else:
            # try import Xlib for Linux
            try:
                from Xlib import display as xdisplay
                self._xdisplay = xdisplay.Display()
            except Exception:
                self._xdisplay = None

        # 使窗口不接收鼠标事件（Qt 层面）
        try:
            self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        except Exception:
            pass

    def _make_click_through(self):
        try:
            hwnd = int(self.winId())
            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x00080000
            WS_EX_TRANSPARENT = 0x00000020
            WS_EX_TOOLWINDOW = 0x00000080
            try:
                cur = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, cur | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW)
            except Exception:
                # 64-bit fallback
                try:
                    cur = ctypes.windll.user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
                    ctypes.windll.user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, cur | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW)
                except Exception:
                    pass
        except Exception:
            pass

    def _tick(self):
        # 获取鼠标位置并尝试找到窗口矩形（跨平台）
        left = top = w = h = None

        if _IS_WINDOWS:
            pt = wintypes.POINT()
            if not self.user32.GetCursorPos(byref(pt)):
                return

            hwnd = self.user32.WindowFromPoint(pt)
            if not hwnd:
                return

            # 获取顶层窗口（避免子控件导致尺寸不正确）
            try:
                GA_ROOTOWNER = 3
                hwnd = self.user32.GetAncestor(hwnd, GA_ROOTOWNER) or hwnd
            except Exception:
                pass

            rect = wintypes.RECT()
            if not self.user32.GetWindowRect(hwnd, byref(rect)):
                return

            left, top, right, bottom = rect.left, rect.top, rect.right, rect.bottom
            w = max(1, right - left)
            h = max(1, bottom - top)
        else:
            # Linux: 使用 Xlib（若可用）尝试获取鼠标下的最顶层窗口
            if self._xdisplay is None:
                # 无法获取 Xlib，使用光标位置并以小矩形代替
                qp = QGuiApplication.cursor().pos()
                left = qp.x() - 40
                top = qp.y() - 12
                w = 80
                h = 24
            else:
                try:
                    root = self._xdisplay.screen().root
                    pointer = root.query_pointer()
                    child = pointer.child
                    if child == 0:
                        # 如果没有 child，使用根窗口附近位置
                        qp = QGuiApplication.cursor().pos()
                        left = qp.x() - 40
                        top = qp.y() - 12
                        w = 80
                        h = 24
                    else:
                        win = self._xdisplay.create_resource_object('window', child)
                        geom = win.get_geometry()
                        # translate coords to root
                        try:
                            tx = win.translate_coords(root, 0, 0)
                            left = tx.x
                            top = tx.y
                        except Exception:
                            left = geom.x
                            top = geom.y
                        w = max(1, geom.width)
                        h = max(1, geom.height)
                except Exception:
                    qp = QGuiApplication.cursor().pos()
                    left = qp.x() - 40
                    top = qp.y() - 12
                    w = 80
                    h = 24

        # 将 overlay 设置为目标窗口大小并在周围留出边框
        # 注意：Win32 / X11 返回的是物理像素，需要转换为 Qt 逻辑像素（考虑 DPI 缩放）
        try:
            screen = QGuiApplication.screenAt(QPoint(left, top)) or QGuiApplication.primaryScreen()
            scale = getattr(screen, 'devicePixelRatio', None)
            if callable(scale):
                scale = scale()
            if not scale or scale <= 0:
                # Qt6 常用 devicePixelRatio 返回 1.0 或更大
                try:
                    scale = screen.devicePixelRatio()
                except Exception:
                    scale = 1.0
        except Exception:
            scale = 1.0

        phys_left = left
        phys_top = top
        phys_w = w
        phys_h = h

        # 转换为逻辑像素
        left = int(phys_left / scale)
        top = int(phys_top / scale)
        w = int(phys_w / scale)
        h = int(phys_h / scale)

        new_rect = (left - self._border_thickness, top - self._border_thickness,
                    w + self._border_thickness * 2, h + self._border_thickness * 2)

        if new_rect != self._last_rect:
            try:
                self.setGeometry(new_rect[0], new_rect[1], new_rect[2], new_rect[3])
                self._last_rect = new_rect
            except Exception:
                pass

        # 只有第一次显示后尝试设置点击穿透样式
        if not self.isVisible():
            # 先以目标位置直接显示，后面由插值平滑
            try:
                self.setGeometry(new_rect[0], new_rect[1], new_rect[2], new_rect[3])
            except Exception:
                pass
            self.show()
            # 稍微延迟以确保 winId 可用，然后设置系统级穿透（Windows）
            QTimer.singleShot(50, self._make_click_through)

        # 计算平滑插值（根据时间步）
        now = time.perf_counter()
        dt = max(1e-6, now - self._last_time)
        self._last_time = now

        tx, ty, tw, th = new_rect
        if self._current_rect is None:
            self._current_rect = (float(tx), float(ty), float(tw), float(th))
        else:
            cx, cy, cw, ch = self._current_rect
            # 使用指数衰减近似，和帧率无关的插值系数
            # factor 越接近 1 则跟随越快
            factor = 1 - pow(1 - self._follow_speed, dt * 60)
            nx = cx + (tx - cx) * factor
            ny = cy + (ty - cy) * factor
            nw = cw + (tw - cw) * factor
            nh = ch + (th - ch) * factor
            self._current_rect = (nx, ny, nw, nh)

        # 将插值后的矩形应用到窗口（四舍五入为像素）
        crx, cry, crw, crh = self._current_rect
        try:
            self.setGeometry(int(round(crx)), int(round(cry)), max(1, int(round(crw))), max(1, int(round(crh))))
        except Exception:
            pass

        # 更新颜色（循环 hue）
        self._hue = (self._hue + self._hue_step) % 360
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)

        # 不绘制背景（保持透明），只绘制边框
        color = QColor.fromHsv(int(self._hue), 255, 255)
        color.setAlpha(220)
        pen = p.pen()
        pen.setWidth(self._border_thickness)
        pen.setColor(color)
        p.setPen(pen)
        # 绘制圆角矩形边框
        try:
            # drawRoundedRect(x, y, w, h, xRadius, yRadius)
            x = self._border_thickness // 2
            y = self._border_thickness // 2
            w = max(1, self.width() - self._border_thickness)
            h = max(1, self.height() - self._border_thickness)
            p.drawRoundedRect(x, y, w, h, self._corner_radius, self._corner_radius)
        except Exception:
            p.drawRect(0, 0, self.width()-1, self.height()-1)


def run_gui():
    # 尝试从同目录的 mousewin.json 加载配置
    cfg = None
    try:
        base = os.path.dirname(__file__)
        cfg_path = os.path.join(base, 'mousewin.json')
        if os.path.exists(cfg_path):
            with open(cfg_path, 'r', encoding='utf-8') as f:
                j = json.load(f)
                cfg = j.get('config', None) if isinstance(j, dict) else None
    except Exception:
        cfg = None

    app = QApplication(sys.argv)
    w = MouseUnderWindowOverlay(cfg=cfg)
    w.show()  # will be adjusted by first tick
    try:
        app.exec()
    except Exception:
        pass
