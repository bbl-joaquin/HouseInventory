import json
from datetime import datetime
from pathlib import Path
from barcode_lib.handlers.base import ModeBase

CACHE_PATH = Path(__file__).parent.parent / "product_cache.json"

class RemoveMode(ModeBase):
    def __init__(self, reader):
        self.reader = reader

    def process_code(self, code: str):
        cache = self._load_cache()
        if code in cache:
            del cache[code]
            self._save_cache(cache)
            self.reader.logger.log(code, "remove")
            self.reader.history.append(("remove", code, "remove", datetime.now()))
            print(f"[RemoveMode] Removed SKU: {code}")
        else:
            print(f"[RemoveMode] SKU not in cache: {code}")

    def _load_cache(self) -> dict:
        if not CACHE_PATH.exists():
            return {}
        return json.loads(CACHE_PATH.read_text())

    def _save_cache(self, cache: dict):
        CACHE_PATH.write_text(json.dumps(cache, indent=2, ensure_ascii=False))

