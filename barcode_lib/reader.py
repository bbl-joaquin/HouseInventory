from collections import deque
from barcode_lib.db.logger import ScanLogger
from barcode_lib.utils import import_from_path, load_config

class BarcodeReader:
    def __init__(self):
        cfg = load_config()
        self.logger = ScanLogger()
        self.modes = {k: import_from_path(v) for k,v in cfg["modes"].items()}
        self.states = {k: import_from_path(v) for k,v in cfg["states"].items()}
        self.configs= {k: import_from_path(v) for k,v in cfg["configs"].items()}
        self.current_mode = self.modes["input"](self)
        self.history = deque(maxlen=100)
        self._toast_seconds = 3
        # GUI callbacks
        self.on_mode_change = None
        self.on_warning = None
        self.on_log_refresh = None

    def read_code(self):
        code = input(self.current_mode.prompt()).strip()
        self._dispatch(code)

    def _dispatch(self, code: str):
        # Priority: modes -> states -> configs -> current mode
        if code in self.modes:
            self._set_mode(self.modes[code])
            return
        if code in self.states:
            self._run_callable(self.states[code])
            if getattr(self, 'on_log_refresh', None):
                self.on_log_refresh()
            return
        if code in self.configs:
            self._run_callable(self.configs[code])
            if getattr(self, 'on_log_refresh', None):
                self.on_log_refresh()
            return
        self.current_mode.process_code(code)
        if getattr(self, 'on_log_refresh', None):
            self.on_log_refresh()

    def _set_mode(self, mode_class):
        self.history.append(("mode", self.current_mode.__class__))
        self.current_mode = mode_class(self)
        if self.on_mode_change:
            name = self.current_mode.__class__.__name__.replace("Mode","").lower()
            self.on_mode_change(name)

    def _run_callable(self, fn): fn(self)
    def gui_toast(self, sku, mode): pass
    def gui_warn(self, text):
        if self.on_warning: self.on_warning(text)
    def undo_last(self):
        self.logger.undo_last()
        if self.on_log_refresh: self.on_log_refresh()
