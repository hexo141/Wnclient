from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QFont, QFontDatabase, QGuiApplication
import sys
import os
import json
import time


class MarqueeFPSWindow(QWidget):
    def __init__(self, fps_value):
        super().__init__()
        self.fps_value = fps_value

        # frameless, always-on-top and allow transparent outside (for rounded corners)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(120, 36)

        self._offset = 0.0
        self._segment_len = 24  # moving segment length
        self._thickness = 2     # border / segment thickness

        # time-based movement for smooth marquee
        self._last_time = time.perf_counter()
        self._speed = 120.0  # pixels per second

        # 使用更快的更新定时器
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._tick)
        self._update_timer.start(8)  # ~125Hz

        # 屏幕FPS测量
        self._last_vblank_time = 0
        self._vblank_times = []  # 存储垂直同步时间戳
        self._max_samples = 60   # 存储最近60个样本
        
        # 获取屏幕刷新率作为参考
        self._screen = QGuiApplication.primaryScreen()
        self._nominal_refresh_rate = self._screen.refreshRate()
        
        # FPS更新定时器
        self._fps_timer = QTimer(self)
        self._fps_timer.timeout.connect(self._update_fps)
        self._fps_timer.start(100)  # 每100ms更新一次FPS显示

        # try load a bundled font if present
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

        # for drag support
        self._drag_pos = None

        # try restore last saved position
        try:
            pos_file = os.path.join(os.path.dirname(__file__), 'fps.pos.json')
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

    def _update_fps(self):
        """Calculate screen refresh rate based on vertical sync timing."""
        now = time.perf_counter()
        
        # 移除超过1秒的旧时间戳
        self._vblank_times = [t for t in self._vblank_times if now - t <= 1.0]
        
        # 计算基于垂直同步的FPS
        if len(self._vblank_times) >= 2:
            time_span = self._vblank_times[-1] - self._vblank_times[0]
            if time_span > 0:
                fps = (len(self._vblank_times) - 1) / time_span
            else:
                fps = 0
        else:
            # 如果没有足够样本，使用标称刷新率
            fps = self._nominal_refresh_rate
            
        # 限制样本数量
        if len(self._vblank_times) > self._max_samples:
            self._vblank_times = self._vblank_times[-self._max_samples:]
        
        # 输出FPS值
        out = int(round(fps)) if fps > 0.5 else 0
        try:
            self.fps_value.value = int(out)
        except Exception:
            pass

    def _perimeter_length(self):
        w = self.width()
        h = self.height()
        return max(1, 2 * (w + h) - 8)

    def _tick(self):
        now = time.perf_counter()
        dt = now - self._last_time
        self._last_time = now
        move = self._speed * dt
        self._offset = (self._offset + move) % self._perimeter_length()
        
        # 模拟垂直同步事件 - 在每次tick时记录时间戳
        current_time = time.perf_counter()
        if self._last_vblank_time == 0:
            self._last_vblank_time = current_time
            self._vblank_times.append(current_time)
        else:
            # 只有当时间间隔接近屏幕刷新周期时才记录为垂直同步
            expected_interval = 1.0 / self._nominal_refresh_rate
            actual_interval = current_time - self._last_vblank_time
            
            # 如果时间间隔接近预期的刷新间隔，记录为垂直同步
            if abs(actual_interval - expected_interval) < expected_interval * 0.3:
                self._vblank_times.append(current_time)
                self._last_vblank_time = current_time
            # 如果间隔太长（可能由于系统负载），也记录但重置计时
            elif actual_interval > expected_interval * 1.5:
                self._vblank_times.append(current_time)
                self._last_vblank_time = current_time
        
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        
        # rounded background
        p.setRenderHint(QPainter.Antialiasing, True)
        rect = self.rect().adjusted(0, 0, 0, 0)
        bg = QColor(0, 0, 0, 230)
        p.setPen(Qt.NoPen)
        p.setBrush(bg)
        try:
            p.drawRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), 8, 8)
        except Exception:
            p.fillRect(self.rect(), QColor(0, 0, 0))

        # draw FPS text - this shows SCREEN refresh rate
        try:
            val = int(self.fps_value.value)
        except Exception:
            val = 0
        text = f"{val} FPS"
        p.setFont(self._font)
        
        # 根据帧率改变文字颜色
        if val >= 120:
            text_color = QColor(0, 255, 0)  # 绿色表示高刷新率
        elif val >= 60:
            text_color = QColor(255, 255, 0)  # 黄色表示中等刷新率
        else:
            text_color = QColor(255, 100, 100)  # 红色表示低刷新率
            
        p.setPen(text_color)
        rect_text = self.rect().adjusted(0, 0, 0, -2)
        p.drawText(rect_text, Qt.AlignCenter, text)

        # rounded thin border
        base_color = QColor(255, 255, 255, 30)
        p.setPen(base_color)
        p.setBrush(Qt.NoBrush)
        rect_border = self.rect().adjusted(1, 1, -1, -1)
        try:
            p.drawRoundedRect(rect_border.x(), rect_border.y(), rect_border.width(), rect_border.height(), 6, 6)
        except Exception:
            p.drawRect(rect_border)

        # draw marquee moving segment along perimeter
        seg_color = QColor(255, 255, 255)
        p.setPen(Qt.NoPen)
        p.setBrush(seg_color)

        seg = int(self._segment_len)
        t = int(self._thickness)
        pos = int(self._offset)
        perim = self._perimeter_length()

        w = self.width()
        h = self.height()

        def draw_segment_at(pix, length):
            if pix < (w - 4):
                x = 2 + pix
                y = 2
                p.drawRect(int(x), int(y), int(length), int(t))
                return
            pix2 = pix - (w - 4)
            if pix2 < (h - 4):
                x = w - 2 - t
                y = 2 + pix2
                p.drawRect(int(x), int(y), int(t), int(length))
                return
            pix3 = pix2 - (h - 4)
            if pix3 < (w - 4):
                x = (w - 2) - pix3 - length
                y = h - 2 - t
                p.drawRect(int(x), int(y), int(length), int(t))
                return
            pix4 = pix3 - (w - 4)
            x = 2
            y = (h - 2) - pix4 - length
            p.drawRect(int(x), int(y), int(t), int(length))

        step = 4
        for i in range(0, seg, step):
            pix = (pos + i) % perim
            draw_segment_at(pix, step)

    # dragging
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.LeftButton:
            newpos = event.globalPosition().toPoint() - self._drag_pos
            self.move(newpos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def closeEvent(self, event):
        # save current top-left position to file
        try:
            geo = self.frameGeometry().topLeft()
            x = int(geo.x())
            y = int(geo.y())
            pos_file = os.path.join(os.path.dirname(__file__), 'fps.pos.json')
            with open(pos_file, 'w', encoding='utf-8') as f:
                json.dump({'x': x, 'y': y}, f)
        except Exception:
            pass
        event.accept()


def run_gui(fps_value):
    app = QApplication(sys.argv)
    w = MarqueeFPSWindow(fps_value)
    w.show()
    try:
        app.exec()
    except Exception:
        pass