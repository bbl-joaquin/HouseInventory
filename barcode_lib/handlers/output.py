from datetime import datetime
from barcode_lib.handlers.base import ModeBase
class OutputMode(ModeBase):
    def process_code(self, code:str):
        ok = self.reader.logger.log_output(code)
        self.reader.history.append(("scan", code, "output", datetime.now()))
        if ok:
            print(f"[OutputMode] Processed code: {code}")
        else:
            msg=f"[OutputMode] Warning: SKU {code} not in stock. Nothing changed."
            print(msg)
            self.reader.gui_warn(msg)
