from barcode_lib.handlers.base import ModeBase

class SetMode(ModeBase):
    def __init__(self, reader):
        self.reader = reader
        self._current_sku = None

    def prompt(self):
        base = self.__class__.__name__.replace("Mode", "").lower()
        if self._current_sku is None:
            return f"[{base}] Scan code:"
        return f"[{base}] Scan set value:"

    def process_code(self, code: str):
        try:
            self._current_sku = self._current_sku or code
            if code.endswith("%"):
                percentage = int(code[:-1])
                print(f"[SetMode] Remaining for {self._current_sku}: {percentage}%")
                self._current_sku = None
        except Exception:
            print(f"[SetMode] Invalid input: {code}")
            self._current_sku = None

