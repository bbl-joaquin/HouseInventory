from datetime import datetime
from barcode_lib.handlers.base import ModeBase
class InputMode(ModeBase):
    def process_code(self, code:str):
        self.reader.logger.log_input(code)
        self.reader.history.append(("scan", code, "input", datetime.now()))
        self.reader.gui_toast(code, "input")
        print(f"[InputMode] Processed code: {code}")
