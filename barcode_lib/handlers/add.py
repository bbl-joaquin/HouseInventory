from barcode_lib.handlers.base import ModeBase

class AddMode(ModeBase):
    def __init__(self, reader):
        self.reader = reader

    def process_code(self, code: str):
        print(f"[AddMode] Processed code: {code}")
