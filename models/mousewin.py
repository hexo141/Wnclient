from multiprocessing import Process
from . import _mousewin_gui


class mousewin:
    def __init__(self):
        self._proc = None

    def start(self):
        """Start the overlay GUI in a separate process (non-blocking).

        The GUI will read `models/mousewin.json` for runtime visual settings.
        """
        if self._proc is None or not self._proc.is_alive():
            # pass no args; the child will read the JSON itself
            self._proc = Process(target=_mousewin_gui.run_gui, daemon=True)
            self._proc.start()

    def stop(self):
        """Stop the GUI process."""
        if self._proc:
            try:
                if self._proc.is_alive():
                    self._proc.terminate()
                    self._proc.join(timeout=2)
            except Exception:
                pass
            self._proc = None
