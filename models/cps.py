from multiprocessing import Process, Manager
import threading
import time
import sys

from . import _cps_gui

# Try to import a lightweight mouse listener. Prefer pynput if available.
try:
    from pynput import mouse
    _HAS_PYNPUT = True
except Exception:
    mouse = None
    _HAS_PYNPUT = False


class cps:
    """Model class `cps` — measures mouse clicks per second (CPS).

    Behavior:
    - Uses a multiprocessing.Manager.Value('i', 0) to store the latest CPS value.
    - Runs a background thread to periodically compute CPS from click events.
    - Uses a pynput mouse.Listener (if available) in a separate thread to capture clicks so
      the main thread is never blocked. If pynput is unavailable, the module still
      provides a value but won't update automatically.

    Methods:
    - start(): non-blocking, starts listener thread and worker thread.
    - stop(): stops listener and worker, joins threads, shuts down manager.
    """

    def __init__(self):
        self._stop_event = threading.Event()
        self._manager = Manager()
        self._cps_value = self._manager.Value('i', 0)

        # shared clicks buffer (manager.list) so GUI process can append timestamps
        # fallback: if pynput is unavailable, GUI clicks will still update CPS
        self._clicks = self._manager.list()
        self._lock = threading.Lock()

        self._listener_thread = None
        self._worker_thread = None
        self._listener = None
        self._proc = None

    def _on_click(self, x, y, button, pressed):
        # only count press events
        if not pressed:
            return
        ts = time.time()
        # append to shared list; manager.list is process-safe
        try:
            with self._lock:
                self._clicks.append(ts)
        except Exception:
            # best-effort
            pass

    def _listener_run(self):
        # runs in a thread and starts pynput listener (blocking until stopped)
        if not _HAS_PYNPUT:
            return
        try:
            with mouse.Listener(on_click=self._on_click) as l:
                self._listener = l
                # wait until stop event set
                while not self._stop_event.is_set():
                    time.sleep(0.1)
                # stopping listener context will exit
        except Exception:
            # fallback: exit silently
            pass

    def _worker(self):
        # compute CPS from timestamps in _clicks
        # keep last 2 seconds of clicks and compute instantaneous CPS
        window = 1.0
        while not self._stop_event.is_set():
            now = time.time()
            cutoff = now - window
            # remove old timestamps from the left
            try:
                with self._lock:
                    # manager.list doesn't support deque semantics; prune in-place
                    i = 0
                    L = self._clicks
                    ln = len(L)
                    while i < ln and L[i] < cutoff:
                        i += 1
                    if i > 0:
                        # remove first i items
                        for _ in range(i):
                            try:
                                L.pop(0)
                            except Exception:
                                break
                    count = len(L)
            except Exception:
                count = 0
            try:
                self._cps_value.value = int(count / window)
            except Exception:
                pass
            # sleep a bit before next sample
            time.sleep(0.1)

    def start(self):
        """Start the CPS measurement (non-blocking)."""
        if self._worker_thread and self._worker_thread.is_alive():
            return
        self._stop_event.clear()
        # start worker thread
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()

        # start listener thread if available
        if _HAS_PYNPUT and (self._listener_thread is None or not self._listener_thread.is_alive()):
            self._listener_thread = threading.Thread(target=self._listener_run, daemon=True)
            self._listener_thread.start()

        # start GUI process that reads self._cps_value (keep UI in separate process)
        try:
            if self._proc is None or not self._proc.is_alive():
                # pass both the shared cps value and the shared click list to GUI
                self._proc = Process(target=_cps_gui.run_gui, args=(self._cps_value, self._clicks), daemon=True)
                self._proc.start()
        except Exception:
            # If GUI process cannot be started, continue without blocking
            self._proc = None

    def stop(self):
        """Stop listener and worker, clean up manager."""
        self._stop_event.set()
        # try to stop pynput listener
        try:
            if self._listener:
                self._listener.stop()
        except Exception:
            pass

        if self._listener_thread:
            self._listener_thread.join(timeout=2)
        if self._worker_thread:
            self._worker_thread.join(timeout=2)

        # stop GUI process if started
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

