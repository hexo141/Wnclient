from multiprocessing import Process, Manager
import threading
import time
import sys

from . import _keyb_gui

# try optional pynput for global keyboard listening
try:
    from pynput import keyboard
    _HAS_PYNPUT = True
except Exception:
    keyboard = None
    _HAS_PYNPUT = False


class keyb:
    """Model class `keyb` — monitor keyboard presses and show animated overlay.

    Behavior:
    - Maintains a multiprocessing.Manager.list of recent key events as tuples
      (key_str, count, timestamp).
    - If `pynput` is available, a listener thread captures key presses and updates the
      shared list (consolidating repeated presses into xN). Otherwise the GUI still
      accepts clicks if other code appends to the shared list.
    - Starts a separate process running a PySide6 GUI (`models/_keyb_gui.py`) which
      reads the shared list and animates the pressed keys from right-to-left.
    """

    def __init__(self):
        self._stop_event = threading.Event()
        self._manager = Manager()
        self._keys = self._manager.list()  # elements: (key_str, count, ts)
        self._lock = threading.Lock()

        self._listener_thread = None
        self._worker_thread = None
        self._listener = None
        self._proc = None

        # track last physical press times to filter OS auto-repeat (long-press)
        self._last_press_time = {}
        # interval (s) below which repeated on_press events are considered auto-repeat and ignored
        self._auto_repeat_interval = 0.35
        # interval (s) within which sequential presses of the same key are combined into xN
        self._combine_interval = 1.2

    def _on_press(self, key):
        try:
            k = None
            if hasattr(key, 'char') and key.char is not None:
                k = str(key.char)
            else:
                k = str(key).replace('Key.', '')
        except Exception:
            k = str(key)
        now = time.time()
        # ignore auto-repeat events produced by holding a key down
        last_physical = self._last_press_time.get(k)
        if last_physical is not None and (now - last_physical) < self._auto_repeat_interval:
            # treat as auto-repeat -> ignore
            return
        # record this physical press time
        try:
            self._last_press_time[k] = now
        except Exception:
            pass

        # consolidate with last logical entry if same key and recent (combine into xN)
        try:
            with self._lock:
                if len(self._keys) > 0:
                    last_key, last_count, last_ts = self._keys[-1]
                    if last_key == k and (now - last_ts) < self._combine_interval:
                        # replace last tuple with incremented count
                        try:
                            self._keys[-1] = (last_key, last_count + 1, now)
                        except Exception:
                            pass
                        return
                # append new logical entry
                try:
                    self._keys.append((k, 1, now))
                except Exception:
                    pass
        except Exception:
            pass

    def _listener_run(self):
        if not _HAS_PYNPUT:
            return
        try:
            with keyboard.Listener(on_press=self._on_press) as l:
                self._listener = l
                while not self._stop_event.is_set():
                    time.sleep(0.1)
        except Exception:
            pass

    def _worker(self):
        # prune old entries older than display_time (seconds)
        display_time = 2.5
        while not self._stop_event.is_set():
            now = time.time()
            try:
                with self._lock:
                    # remove old from left
                    i = 0
                    L = self._keys
                    ln = len(L)
                    while i < ln and (now - L[i][2]) > display_time:
                        i += 1
                    if i > 0:
                        for _ in range(i):
                            try:
                                L.pop(0)
                            except Exception:
                                break
            except Exception:
                pass
            time.sleep(0.12)

    def start(self):
        if self._worker_thread and self._worker_thread.is_alive():
            return
        self._stop_event.clear()
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()

        if _HAS_PYNPUT and (self._listener_thread is None or not self._listener_thread.is_alive()):
            self._listener_thread = threading.Thread(target=self._listener_run, daemon=True)
            self._listener_thread.start()

        # start GUI process
        try:
            if self._proc is None or not self._proc.is_alive():
                self._proc = Process(target=_keyb_gui.run_gui, args=(self._keys,), daemon=True)
                self._proc.start()
        except Exception:
            self._proc = None

    def stop(self):
        self._stop_event.set()
        try:
            if self._listener:
                self._listener.stop()
        except Exception:
            pass

        if self._listener_thread:
            self._listener_thread.join(timeout=2)
        if self._worker_thread:
            self._worker_thread.join(timeout=2)

        if self._proc:
            try:
                if self._proc.is_alive():
                    self._proc.terminate()
                    self._proc.join(timeout=2)
            except Exception:
                pass

        try:
            self._manager.shutdown()
        except Exception:
            pass
