import sqlite3, threading, queue
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from barcode_lib.web.scraper import scrape_product_info

# --- Paths ---
DB_DIR = Path(__file__).parent
DB_DIR.mkdir(parents=True, exist_ok=True)
SCANS_DB = DB_DIR / "scans.db"
STOCK_DB = DB_DIR / "stock.db"
CATALOG_DB = DB_DIR / "catalog.db"
IMAGE_DIR = DB_DIR / "images"
IMAGE_DIR.mkdir(exist_ok=True)

def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# -------------------- Catalog --------------------
class Catalog:
    def __init__(self, path: Path = CATALOG_DB):
        self.conn = sqlite3.connect(path)
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS products (
                sku TEXT PRIMARY KEY,
                product TEXT,
                brand TEXT,
                category TEXT,
                image TEXT,
                url TEXT,
                updated_at TEXT
            )"""
        )
        self.conn.commit()

    def upsert(self, sku: str, info: Dict[str, Any]):
        info = info or {}
        row = self.get(sku)
        if row:
            self.conn.execute(
                """UPDATE products
                   SET product=?, brand=?, category=?, image=?, url=?, updated_at=?
                   WHERE sku=?""",
                (
                    info.get("product"),
                    info.get("brand"),
                    info.get("category"),
                    info.get("image"),
                    info.get("url"),
                    _now(),
                    sku,
                ),
            )
        else:
            self.conn.execute(
                """INSERT OR REPLACE INTO products
                   (sku, product, brand, category, image, url, updated_at)
                   VALUES (?,?,?,?,?,?,?)""",
                (
                    sku,
                    info.get("product"),
                    info.get("brand"),
                    info.get("category"),
                    info.get("image"),
                    info.get("url"),
                    _now(),
                ),
            )
        self.conn.commit()

    def get(self, sku: str) -> Optional[Dict[str, Any]]:
        cur = self.conn.execute(
            "SELECT sku,product,brand,category,image,url FROM products WHERE sku=?",
            (sku,),
        )
        r = cur.fetchone()
        if not r:
            return None
        return {
            "sku": r[0],
            "product": r[1],
            "brand": r[2],
            "category": r[3],
            "image": r[4],
            "url": r[5],
        }

    def search(self, text: str, limit: int = 200) -> List[Tuple]:
        if text:
            q = f"%{text.lower()}%"
            cur = self.conn.execute(
                """SELECT sku,product,brand,category,image,url
                   FROM products
                   WHERE LOWER(sku) LIKE ? OR LOWER(product) LIKE ? OR LOWER(brand) LIKE ?
                   ORDER BY updated_at DESC LIMIT ?""",
                (q, q, q, limit),
            )
        else:
            cur = self.conn.execute(
                """SELECT sku,product,brand,category,image,url
                   FROM products ORDER BY updated_at DESC LIMIT ?""",
                (limit,),
            )
        return cur.fetchall()

    def remove(self, sku: str):
        self.conn.execute("DELETE FROM products WHERE sku=?", (sku,))
        self.conn.commit()

# -------------------- Scan Logger --------------------
class ScanLogger:
    def __init__(self):
        self.catalog = Catalog()
        self.scans = sqlite3.connect(SCANS_DB)
        self.stock = sqlite3.connect(STOCK_DB)

        # scans: agregamos 'value' para guardar info auxiliar (p.ej. "pct|delta" en set)
        self.scans.execute(
            """CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT,
                product TEXT,
                brand TEXT,
                category TEXT,
                image TEXT,
                url TEXT,
                mode TEXT,
                ts TEXT
            )"""
        )
        if not self._has_column(self.scans, "scans", "value"):
            self.scans.execute("ALTER TABLE scans ADD COLUMN value TEXT")
        self.scans.commit()

        # stock: qty y percent (percent=100 ⇒ no hay fracción abierta)
        self.stock.execute("""CREATE TABLE IF NOT EXISTS stock (sku TEXT PRIMARY KEY)""")
        self._ensure_stock_columns()
        self.stock.commit()

        # background enrichment queue
        self._q = queue.Queue()
        self._worker = threading.Thread(target=self._enrich_worker, daemon=True)
        self._worker.start()

    # ---------- helpers ----------
    @staticmethod
    def _has_column(conn: sqlite3.Connection, table: str, col: str) -> bool:
        cur = conn.execute(f"PRAGMA table_info({table})")
        return any(r[1] == col for r in cur.fetchall())

    def _ensure_stock_columns(self):
        for col in ("product", "brand", "category", "image", "url"):
            if not self._has_column(self.stock, "stock", col):
                self.stock.execute(f"ALTER TABLE stock ADD COLUMN {col} TEXT")
        if not self._has_column(self.stock, "stock", "qty"):
            self.stock.execute("ALTER TABLE stock ADD COLUMN qty INTEGER DEFAULT 0")
        if not self._has_column(self.stock, "stock", "percent"):
            self.stock.execute("ALTER TABLE stock ADD COLUMN percent INTEGER DEFAULT 100")

    # ---------- enrichment ----------
    def queue_enrich(self, sku: str, force: bool = False):
        self._q.put((sku, force))

    def _enrich_worker(self):
        while True:
            sku, force = self._q.get()
            try:
                info = self.catalog.get(sku)
                if force or not info or not info.get("product"):
                    data = scrape_product_info(sku, force_refresh=force) or {}
                    merged = (info or {}).copy()
                    for k in ("product", "brand", "category", "image", "url"):
                        if not merged.get(k) and data.get(k):
                            merged[k] = data[k]
                    self.catalog.upsert(sku, merged)
            except Exception:
                pass
            finally:
                self._q.task_done()

    # ---------- internals ----------
    def _append_scan(self, sku: str, mode: str, value: Optional[str] = None):
        info = self.catalog.get(sku) or {
            "product": None,
            "brand": None,
            "category": None,
            "image": None,
            "url": None,
        }
        self.scans.execute(
            """INSERT INTO scans (sku,product,brand,category,image,url,mode,ts,value)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                sku,
                info.get("product"),
                info.get("brand"),
                info.get("category"),
                info.get("image"),
                info.get("url"),
                mode,
                _now(),
                value,
            ),
        )
        self.scans.commit()

    # ---------- public API ----------
    def log_input(self, sku: str):
        self._append_scan(sku, "input")
        row = self.stock.execute("SELECT qty FROM stock WHERE sku=?", (sku,)).fetchone()
        if row:
            self.stock.execute("UPDATE stock SET qty=qty+1 WHERE sku=?", (sku,))
        else:
            info = self.catalog.get(sku) or {}
            self.stock.execute(
                """INSERT OR REPLACE INTO stock
                   (sku,product,brand,category,image,url,qty,percent)
                   VALUES (?,?,?,?,?,?,?,100)""",
                (
                    sku,
                    info.get("product"),
                    info.get("brand"),
                    info.get("category"),
                    info.get("image"),
                    info.get("url"),
                    1,
                ),
            )
        self.stock.commit()
        self.queue_enrich(sku)

    def log_output(self, sku: str) -> bool:
        self._append_scan(sku, "output")
        row = self.stock.execute("SELECT qty, percent FROM stock WHERE sku=?", (sku,)).fetchone()
        if not row:
            return False

        qty, pct = row
        pct = 100 if pct is None else int(pct)

        # consumir fracción abierta primero
        if 0 < pct < 100:
            self.stock.execute("UPDATE stock SET percent=100 WHERE sku=?", (sku,))
            self.stock.commit()
            return True

        if qty and qty > 0:
            self.stock.execute("UPDATE stock SET qty=qty-1 WHERE sku=?", (sku,))
            self.stock.commit()
            return True
        return False

    def log_set(self, sku: str, pct: int):
        try:
            pct = int(pct)
        except Exception:
            pct = 100
        pct = max(0, min(100, pct))

        row = self.stock.execute("SELECT qty, percent FROM stock WHERE sku=?", (sku,)).fetchone()
        delta = 0
        if row:
            qty, cur_pct = row
            cur_pct = 100 if cur_pct is None else int(cur_pct)
            if 0 < cur_pct < 100:
                self.stock.execute("UPDATE stock SET percent=? WHERE sku=?", (pct, sku))
                delta = 0
            else:
                if qty and qty > 0:
                    self.stock.execute("UPDATE stock SET qty=?, percent=? WHERE sku=?", (qty - 1, pct, sku))
                    delta = -1
                else:
                    self.stock.execute("UPDATE stock SET percent=? WHERE sku=?", (pct, sku))
                    delta = 0
        else:
            info = self.catalog.get(sku) or {}
            self.stock.execute(
                """INSERT OR REPLACE INTO stock
                   (sku,product,brand,category,image,url,qty,percent)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (sku, info.get("product"), info.get("brand"), info.get("category"), info.get("image"), info.get("url"), 0, pct),
            )
            delta = 0

        self.stock.commit()
        self._append_scan(sku, "set", value=f"{pct}|{delta}")
        self.queue_enrich(sku)

    def add_or_refresh_product(self, sku: str, allow_manual: bool = True):
        if not self.catalog.get(sku):
            self.catalog.upsert(sku, {"product": None, "brand": None, "category": None, "image": None, "url": None})
        self.queue_enrich(sku, force=False)

    def remove_known_product(self, sku: str):
        self.catalog.remove(sku)

    # ---------- queries ----------
    def last(self, n: int = 20):
        cur = self.scans.execute("SELECT * FROM scans ORDER BY id DESC LIMIT ?", (n,))
        return cur.fetchall()

    def stock_table(self, limit: int = 200):
        cur = self.stock.execute(
            """SELECT sku,product,brand,category,image,url,qty,percent
               FROM stock
               ORDER BY product COLLATE NOCASE ASC
               LIMIT ?""",
            (limit,),
        )
        return cur.fetchall()

    def rebuild_stock(self):
        self.stock.execute("DELETE FROM stock")
        skus = [r[0] for r in self.scans.execute("SELECT DISTINCT sku FROM scans").fetchall()]
        for sku in skus:
            ins = self.scans.execute("SELECT COUNT(*) FROM scans WHERE sku=? AND mode='input'", (sku,)).fetchone()[0]
            outs = self.scans.execute("SELECT COUNT(*) FROM scans WHERE sku=? AND mode='output'", (sku,)).fetchone()[0]
            qty = int(ins) - int(outs)
            if qty > 0:
                info = self.catalog.get(sku) or {}
                self.stock.execute(
                    """INSERT OR REPLACE INTO stock
                       (sku,product,brand,category,image,url,qty,percent)
                       VALUES (?,?,?,?,?,?,?,100)""",
                    (sku, info.get("product"), info.get("brand"), info.get("category"), info.get("image"), info.get("url"), qty),
                )
        self.stock.commit()

    def clear_all(self):
        self.scans.execute("DELETE FROM scans"); self.scans.commit()
        self.stock.execute("DELETE FROM stock"); self.stock.commit()

    def set_all_percent(self, pct: int):
        pct = max(0, min(100, int(pct)))
        self.stock.execute("UPDATE stock SET percent=?", (pct,))
        self.stock.commit()

