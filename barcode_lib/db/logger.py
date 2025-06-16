import sqlite3
from pathlib import Path
from datetime import datetime
from barcode_lib.web.scraper import scrape_product_info


DB_PATH = Path(__file__).parent / "scans.db"

class ScanLogger:
    def __init__(self, db_path=DB_PATH):
        self.conn = sqlite3.connect(db_path)
        self._init_table()

    def _init_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS scans (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            sku        TEXT    NOT NULL,
            product    TEXT,
            brand      TEXT,
            category   TEXT,
            image      TEXT,
            url        TEXT,
            mode       TEXT    NOT NULL,
            timestamp  TEXT    NOT NULL
        )

        """)
        self.conn.commit()

    def log(self, sku: str, mode: str):
        info = scrape_product_info(sku)
        ts = datetime.now().isoformat(sep=" ", timespec="seconds")
        self.conn.execute(
            """INSERT INTO scans (sku, product, brand, category, image, mode, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (sku, info["product"], info["brand"], info["category"], info["image"], mode, ts)
        )
        self.conn.commit()
        print(f"✅ {sku} | {info['product']} | {mode} | {ts}")


    def last(self, limit: int = 5):
        return self.conn.execute(
            "SELECT * FROM scans ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()

    def delete_last(self):
        self.conn.execute(
            "DELETE FROM scans WHERE id = (SELECT MAX(id) FROM scans)"
        )
        self.conn.commit()

    def close(self):
        self.conn.close()

