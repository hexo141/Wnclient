from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QFont, QFontDatabase, QFontMetrics
import sys
import os
import time


class KeyItem:
    def __init__(self, key, count, ts):
        self.key = key
        self.count = count
        self.ts = ts
        self.x = None
        self.target_x = None
        self.width = 0


class KeybWindow(QWidget):
    def __init__(self, keys_list):
        super().__init__()
        self.keys_list = keys_list  # Manager.list of tuples

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        # make window background transparent so keys are not boxed
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # size small and place at bottom-right of primary screen
        self._width = 360
        self._height = 64
        self.setFixedSize(self._width, self._height)

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
            self._font = QFont(self._font_family, 14)
        else:
            self._font = QFont("Segoe UI", 14)

        self._items = []  # list of KeyItem
        self._last_snapshot = []

        self._speed = 600.0  # pixels per second for slide animation
        self._gap = 8
        self._item_h = 40
        self._item_padding = 12
        self._max_items = 6

        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._tick)
        self._update_timer.start(16)

        # timing for smooth animation
        import time as _time
        self._last_tick = _time.perf_counter()

        # position window at bottom-right
        try:
            screen = QApplication.primaryScreen()
            geo = screen.availableGeometry()
            x = geo.right() - self._width - 10
            y = geo.bottom() - self._height - 10
            self.move(x, y)
        except Exception:
            pass

    def _tick(self):
        now = time.time()
        # read shared list snapshot
        try:
            snap = list(self.keys_list)
        except Exception:
            snap = []

        # convert to (key,count,ts)
        new_snapshot = [(t[0], t[1], t[2]) for t in snap]

        # sync internal items with snapshot: newest at end of list
        # We will keep up to _max_items most recent
        new_snapshot = new_snapshot[-self._max_items:]

        # if changed, rebuild items preserving animation x where possible
        if new_snapshot != self._last_snapshot:
            # 使用键名和时间戳的组合作为唯一标识符，避免同名键的冲突
            existing = {}
            for it in self._items:
                # 使用键名和时间戳的组合作为标识符
                identifier = f"{it.key}_{it.ts}"
                existing[identifier] = it
            
            items = []
            for key, count, ts in new_snapshot:
                identifier = f"{key}_{ts}"
                itm = existing.get(identifier)
                if itm is None:
                    itm = KeyItem(key, count, ts)
                    # start beyond right edge to animate in
                    itm.x = self._width + 40
                else:
                    # update count and timestamp but keep current x (no re-entry)
                    itm.count = count
                    itm.ts = ts
                items.append(itm)
            self._items = items
            self._last_snapshot = list(new_snapshot)

        # compute target positions: newest at rightmost inside window
        # item widths vary based on text
        total_width = 0
        fm_main = QFontMetrics(self._font)
        # small font for count
        try:
            main_ps = self._font.pointSize()
            if main_ps <= 0:
                main_ps = int(self._font.pointSizeF()) if self._font.pointSizeF() > 0 else 14
        except Exception:
            main_ps = 14
        small_ps = max(8, main_ps - 4)
        small_font = QFont(self._font.family(), small_ps)
        fm_small = QFontMetrics(small_font)

        # compute width per item and assign to item.width so paintEvent can reuse
        for it in self._items:
            main_text = str(it.key)
            main_w = fm_main.horizontalAdvance(main_text)
            small_w = fm_small.horizontalAdvance(f"x{it.count}") if it.count and it.count > 1 else 0
            # add a tiny spacing between main text and small count
            spacing = 6 if small_w else 0
            w = main_w + small_w + spacing + self._item_padding * 2
            it.width = w
            total_width += w

        # ensure items fit into the window width; if not, drop oldest until they fit
        available = self._width - 20  # margin
        # drop oldest items until remaining total (including gaps) fits available width
        n = len(self._items)
        total_with_gaps = total_width + max(0, n - 1) * self._gap
        while n > 0 and total_with_gaps > available:
            # drop oldest (leftmost)
            try:
                drop_it = self._items.pop(0)
                if self._last_snapshot:
                    try:
                        self._last_snapshot.pop(0)
                    except Exception:
                        pass
                total_width -= getattr(drop_it, 'width', 0)
            except Exception:
                break
            n = len(self._items)
            total_with_gaps = total_width + max(0, n - 1) * self._gap

        # compute target x for each item so that rightmost item's right edge is window width - margin
        margin = 10
        pos = self._width - margin
        targets = []
        # use item.width attributes in reversed order to compute targets
        for it in reversed(self._items):
            w = getattr(it, 'width', 0)
            pos -= w
            targets.append(pos)
            pos -= self._gap
        targets = list(reversed(targets))  # align with self._items order

        # update positions moving towards targets using spring-damper for smooth motion
        import time as _time
        now_tick = _time.perf_counter()
        dt = now_tick - getattr(self, '_last_tick', now_tick)
        # clamp dt to reasonable range
        if dt <= 0 or dt > 0.1:
            dt = 0.016
        self._last_tick = now_tick

        # spring parameters
        k = 400.0   # stiffness
        d = 40.0    # damping

        for i, it in enumerate(self._items):
            targ = targets[i] if i < len(targets) else self._width + 40
            if it.x is None:
                it.x = self._width + 40
                it.v = 0.0
            # ensure velocity field
            if not hasattr(it, 'v'):
                it.v = 0.0
            # spring force = k * (targ - x), damping = -d * v
            force = k * (targ - it.x) - d * it.v
            # integrate velocity and position
            it.v += force * dt
            it.x += it.v * dt
            # if very close to target, snap to avoid tiny oscillations
            if abs(targ - it.x) < 0.5 and abs(it.v) < 0.5:
                it.x = targ
                it.v = 0.0

        # remove items whose timestamp is old (handled by model worker too) — do nothing here

        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        # transparent background: do not fillRect so only text is visible

        # compute small font size here as paintEvent cannot rely on values from _tick
        try:
            main_ps = self._font.pointSize()
            if main_ps <= 0:
                main_ps = int(self._font.pointSizeF()) if self._font.pointSizeF() > 0 else 14
        except Exception:
            main_ps = 14
        small_ps = max(8, main_ps - 4)

        from PySide6.QtGui import QPen

        # helper: dynamic rainbow color
        def rainbow_color(offset=0, alpha=255):
            try:
                h = int((time.time() * 80 + offset) % 360)
                return QColor.fromHsv(h, 255, 255, alpha)
            except Exception:
                return QColor(255, 255, 255, alpha)

        # compute a single global hue that cycles with time so all keys share same color
        try:
            base_hue = int((time.time() * 80) % 360)
        except Exception:
            base_hue = 0

        for it in self._items:
            if it.x is None:
                continue
            x = int(it.x)
            h = self._item_h
            y = (self._height - h) // 2

            # draw main text
            p.setFont(self._font)
            # unified color for all keys (global rainbow cycle)
            hue_off = base_hue
            main_col = rainbow_color(offset=hue_off, alpha=230)
            p.setPen(main_col)
            fm = p.fontMetrics()
            main_text = str(it.key)
            tx = x + self._item_padding
            # vertical center baseline
            ty = y + (h + fm.ascent() - fm.descent()) // 2
            p.drawText(tx, ty, main_text)

            # draw small count at right-bottom of main text
            if it.count and it.count > 1:
                # compute small font and position
                small_font = QFont(self._font.family(), small_ps)
                p.setFont(small_font)
                # smaller count uses same hue but slightly dimmer
                count_col = rainbow_color(offset=hue_off, alpha=180)
                p.setPen(count_col)
                fm_s = QFontMetrics(small_font)
                small_text = f"x{it.count}"
                main_w = fm.horizontalAdvance(main_text)
                sx = tx + main_w + 4
                # place at bottom-right of main text (slightly lower)
                sy = y + h - 6
                p.drawText(sx, sy, small_text)

            # draw border (rounded) around the item using stored width
            try:
                item_w = int(getattr(it, 'width', 0))
                # draw soft neon/glow behind
                glow_col = rainbow_color(offset=hue_off, alpha=60)
                p.setPen(Qt.NoPen)
                p.setBrush(glow_col)
                p.drawRoundedRect(x - 2, y - 2, item_w + 4, int(h) + 4, 8, 8)

                # outline with brighter neon
                pen = QPen(rainbow_color(offset=hue_off, alpha=200))
                pen.setWidth(1)
                p.setPen(pen)
                p.setBrush(Qt.NoBrush)
                p.drawRoundedRect(x, y, item_w, int(h), 6, 6)
            except Exception:
                pass

    # dragging intentionally disabled — window is not draggable


def run_gui(keys_list):
    app = QApplication(sys.argv)
    w = KeybWindow(keys_list)
    w.show()
    try:
        app.exec()
    except Exception:
        pass