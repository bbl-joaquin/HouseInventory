import sqlite3
from pathlib import Path
from datetime import datetime
from barcode_lib.web.scraper import scrape_product_info

DB_PATH = Path(__file__).parent / "scans.db"
STOCK_DB_PATH = Path(__file__).parent / "stock.db"

class ScanLogger:
    def __init__(self, db_path=DB_PATH, stock_db_path=STOCK_DB_PATH):
        self.conn = sqlite3.connect(db_path)
        self.stock_conn = sqlite3.connect(stock_db_path)
        self._init_table()
        self._init_stock_table()

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

    def _init_stock_table(self):
        self.stock_conn.execute("""
            CREATE TABLE IF NOT EXISTS stock (
                sku       TEXT PRIMARY KEY,
                product   TEXT,
                brand     TEXT,
                category  TEXT,
                image     TEXT,
                url       TEXT,
                stock     INTEGER NOT NULL
            )
        """)
        self.stock_conn.commit()

    def log(self, sku: str, mode: str):
        info = scrape_product_info(sku)
        ts = datetime.now().isoformat(sep=" ", timespec="seconds")

        self.conn.execute(
            """INSERT INTO scans (sku, product, brand, category, image, mode, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (sku, info["product"], info["brand"], info["category"], info["image"], mode, ts)
        )
        self.conn.commit()

        row = self.stock_conn.execute("SELECT stock FROM stock WHERE sku = ?", (sku,)).fetchone()
        current = row[0] if row else 0
        new_stock = current + 1 if mode == "input" else current - 1

        if new_stock > 0:
            self.stock_conn.execute("""
                INSERT INTO stock (sku, product, brand, category, image, url, stock)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(sku) DO UPDATE SET stock=excluded.stock
            """, (sku, info["product"], info["brand"], info["category"], info["image"], None, new_stock))
        elif new_stock <= 0:
            self.stock_conn.execute("DELETE FROM stock WHERE sku = ?", (sku,))
        self.stock_conn.commit()

        print(f"✅ {sku} | {info['product']} | {mode} | {ts}")

    def last(self, limit: int = 5):
        return self.conn.execute(
            "SELECT * FROM scans ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()

    def all(self):
        return self.conn.execute(
            "SELECT * FROM scans ORDER BY id DESC"
        ).fetchall()

    def delete_last(self):
        self.conn.execute(
            "DELETE FROM scans WHERE id = (SELECT MAX(id) FROM scans)"
        )
        self.conn.commit()

    def close(self):
        self.conn.close()
        self.stock_conn.close()
        
    def clear_all(self):
        self.stock_conn.execute("DELETE FROM stock")
        self.conn.execute("DELETE FROM scans")
        self.stock_conn.commit()
        
    def rebuild_stock(self):
        self.stock_conn.execute("DELETE FROM stock")
        self.stock_conn.commit()
        
        skus = self.conn.execute("SELECT DISTINCT sku FROM scans").fetchall()

        for (sku,) in skus:
            input_count = self.conn.execute("SELECT COUNT(*) FROM scans WHERE sku = ? AND mode = 'input'", (sku,)).fetchone()[0]
            output_count = self.conn.execute("SELECT COUNT(*) FROM scans WHERE sku = ? AND mode = 'output'", (sku,)).fetchone()[0]
            stock = input_count - output_count

            if stock > 0:
                row = self.conn.execute("""
                    SELECT product, brand, category, image, url
                    FROM scans
                    WHERE sku = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, (sku,)).fetchone()

                product, brand, category, image, url = row

                self.stock_conn.execute("""
                    INSERT INTO stock (sku, product, brand, category, image, url, stock)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (sku, product, brand, category, image, url, stock))

        self.stock_conn.commit()



