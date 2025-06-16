from datetime import datetime
from barcode_lib.handlers.base import ModeBase

class OutputMode(ModeBase):
    def __init__(self, reader):
        self.reader = reader

    def process_code(self, code: str):
        self.reader.logger.log(code, "output")
        self.reader.history.append(("scan", code, "input", datetime.now()))
        print(f"[OutputMode] Processed code: {code}")
