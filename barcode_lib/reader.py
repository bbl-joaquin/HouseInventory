from collections import deque
from barcode_lib.db.logger import ScanLogger
from barcode_lib.utils import import_from_path, load_config

class BarcodeReader:
    def __init__(self):
        config = load_config()
        self.logger = ScanLogger()
        
        self.modes = {k: import_from_path(v) for k, v in config["modes"].items()}
        self.states = {k: import_from_path(v) for k, v in config["states"].items()}
        self.configs = {k: import_from_path(v) for k, v in config["configs"].items()}

        self.current_mode = next(iter(self.modes.values()))(self)
        self.history = deque(maxlen=15)

    def read_code(self):
        prompt = self.current_mode.prompt()
        code = input(prompt).strip().lower()
        self._dispatch(code)

    def _dispatch(self, code: str):
        for table, action in [
            (self.modes, self._set_mode),
            (self.states, self._run_callable),
            (self.configs, self._run_callable),
        ]:
            if code in table:
                action(table[code])
                return


        self.current_mode.process_code(code)

    def _set_mode(self, mode_class):
        self.history.append(("mode", self.current_mode.__class__))
        print(f"Mode switched to: {mode_class.__name__}")
        self.current_mode = mode_class(self)

    def _run_callable(self, func):
        func(self)
