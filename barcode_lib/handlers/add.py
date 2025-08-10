from barcode_lib.handlers.base import ModeBase
class AddMode(ModeBase):
    def process_code(self, code:str):
        # CLI path: allow barcode for add; GUI path opens dialog
        self.reader.logger.add_or_refresh_product(code, allow_manual=False)
        print(f"[AddMode] Added/queued enrichment for SKU {code}")
