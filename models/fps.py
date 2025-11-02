from multiprocessing import Process, Manager
import threading
import time
import ctypes
import sys

from . import _fps_gui


class fps:
    """Model class `fps` - displays actual screen refresh rate."""

    def __init__(self):
        self._manager = Manager()
        # integer value proxy shared with GUI process
        self._fps_value = self._manager.Value('i', 0)

        self._proc = None

    def start(self):
        """Start the GUI process. Non-blocking."""
        # start GUI process that measures and displays actual screen FPS
        if self._proc is None or not self._proc.is_alive():
            # pass the manager.Value proxy to the child process
            # The GUI will measure screen refresh rate
            self._proc = Process(target=_fps_gui.run_gui, args=(self._fps_value,), daemon=True)
            self._proc.start()

    def stop(self):
        """Stop GUI process."""
        if self._proc:
            try:
                if self._proc.is_alive():
                    self._proc.terminate()
                    self._proc.join(timeout=2)
            except Exception:
                pass

        # shutdown manager to clean up proxies
        try:
            self._manager.shutdown()
        except Exception:
            pass