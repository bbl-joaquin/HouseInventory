from datetime import datetime
from barcode_lib.handlers.base import ModeBase

class InputMode(ModeBase):
    def __init__(self, reader):
        self.reader = reader

    def process_code(self, code: str):
        self.reader.logger.log(code, "input")
        self.reader.history.append(("scan", code, "input", datetime.now()))
        print(f"[InputMode] Processed code: {code}")
