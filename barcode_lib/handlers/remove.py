from barcode_lib.handlers.base import ModeBase
class RemoveMode(ModeBase):
    def process_code(self, code:str):
        self.reader.logger.remove_known_product(code)
        print(f"[RemoveMode] Removed SKU from known products: {code}")
