"""
> src.main.py

Barcode Scan Logger

This script provides a simple command-line interface to log barcode SKU scans into a SQLite database. For each scan, it records the SKU, session mode (input or output), and the timestamp in ISO format.

Usage:
    python src.main.py --mode [input|output]

Arguments:
    --mode      Sets the session mode. Use 'input' to log incoming stock, or 'output' to log outgoing stock.

Database:
    By default, a SQLite database file named 'scans.db' is created (if it does not already exist) in the working directory. It contains a table 'scans' with the following columns:
        - id:        Auto-incrementing primary key.
        - sku:       Text field for the scanned barcode.
        - mode:      Text field constrained to 'input' or 'output'.
        - timestamp: Text field storing date and time in ISO 8601 format.

Functions:
    init_db(db_path: str) -> sqlite3.Connection
        Initializes the database connection, applies migrations, and returns a Connection object.

    main()
        Runs the main loop to prompt for SKU inputs and logs each scan until the user exits.

"""

import sqlite3
from datetime import datetime

# 2) Initialize (and migrate) database
def init_db(db_path: str = "scans.db") -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            sku       TEXT    NOT NULL,
            mode      TEXT    CHECK(mode IN ('input','output')) NOT NULL,
            timestamp TEXT    NOT NULL
        )
    """)
    conn.commit()
    return conn

# 3) Main loop
def main(mode:str = "input"):
    conn = init_db()
    cursor = conn.cursor()
    print(f"\n=== Session mode: {mode} ===\n"
          "Scan a barcode (or type 'exit')\n")

    try:
        while True:
            sku = input("SKU: ").strip()
            if sku.lower() == "exit":
                break
            # Mode change parsing
            if sku.lower() == "input":
                mode = "input"
                print("Changed into input mode")
            elif sku.lower() == "output":
                mode = "output"
                print("Changed into output mode")
            elif sku.lower() == "show":
                cursor.execute(
                    "SELECT id, sku, mode, timestamp "
                    "FROM scans "
                    "ORDER BY id DESC LIMIT 5"
                )
                rows = cursor.fetchall()
                if rows:
                    print("\n ID | SKU           | MODE   | TIMESTAMP")
                    print("----|---------------|--------|---------------------")
                    # reverse so oldest of the five shows first
                    for rec_id, rec_sku, rec_mode, rec_ts in rows:
                        print(f"{rec_id:3d} | {rec_sku:10s} | {rec_mode:6s} | {rec_ts}")
                    print()
                else:
                    print("⚠️  No scans logged yet.\n")
                continue
            elif sku.lower() == "back":
                cursor.execute(
                     "SELECT id, sku, mode, timestamp FROM scans " 
                     "ORDER BY id DESC LIMIT 1"
                )
                row = cursor.fetchone()
                if row:
                    print(f"🗑️ Ready to remove: {row}")
                    confirmation = input("If certain, scan 'back' again: ")
                    if confirmation.lower() == "back":
                        cursor.execute(
                            "DELETE FROM scans " \
                            "WHERE id = (SELECT MAX(id) FROM scans)",
                        )
                        conn.commit()
                        print("Latest record removed!")
                    else:
                        print("Removal aborted")
                else:
                    print("There are no rows to remove")
            else:
                # Capture ISO‐style date + time (e.g. “2025-05-14 15:23:08”)
                ts = datetime.now().isoformat(sep=" ", timespec="seconds")

                cursor.execute(
                    "INSERT INTO scans (sku, mode, timestamp) VALUES (?, ?, ?)",
                    (sku, mode, ts)
                )
                conn.commit()

                print(f"✅  {sku} | {mode} | {ts}\n")

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        conn.close()
        print("Goodbye.")

if __name__ == "__main__":
    main()