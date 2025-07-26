def zero_percent(reader):
    print("[State] Set to 0%")

def exit_program(reader):
    print("[State] Exiting program")
    exit()
    
def show(reader):
    rows = reader.logger.last()
    print("\n ID | SKU        | PRODUCT                  | BRAND        | MODE   | TIMESTAMP")
    print("----|------------|---------------------------|--------------|--------|---------------------")
    for row in reversed(rows):
        rec_id, sku, product, brand, *_ , mode, timestamp = row
        print(f"{rec_id:3d} | {sku:10s} | {product[:25]:25s} | {brand[:12]:12s} | {mode:6s} | {timestamp}")
        
def back(reader):
    if not reader.history:
        print("[Undo] No actions to undo.")
        return

    action = reader.history.pop()

    if action[0] == "scan":
        reader.logger.delete_last()
        print(f"[Undo] Removed scan: {action[1]} ({action[2]})")

    elif action[0] == "mode":
        prev_mode_class = action[1]
        reader.current_mode = prev_mode_class(reader)
        print(f"[Undo] Reverted to mode: {reader.current_mode.__class__.__name__}")

def remove_from_cache(sku: str):
    cache = load_cache()
    if sku in cache:
        del cache[sku]
        save_cache(cache)
        print(f"[Remove] SKU {sku} eliminado del cache.")
    else:
        print(f"[Remove] SKU {sku} no estaba en el cache.")

def stock(reader):
    cursor = reader.logger.stock_conn.execute("""
        SELECT sku, product, brand, category, stock
        FROM stock
        ORDER BY stock DESC
    """)
    rows = cursor.fetchall()

    print("\n SKU        | PRODUCT                  | BRAND        | CATEGORY     | STOCK")
    print("------------|---------------------------|--------------|--------------|------")
    for sku, product, brand, category, stock in rows:
        print(f"{sku:12s} | {product[:25]:25s} | {brand[:12]:12s} | {category[:12]:12s} | {stock:5d}")

def rebuild_stock(reader):
    response = input("WARNING: This will rebuild the stock database from scratch based on the log. To confirm scan again the rebuild_stock barcode.").strip().lower()
    if response == "rebuild_stock":
        reader.logger.rebuild_stock()
    else:
        print("Operation cancelled")

def clear_all(reader):
    response = input("WARNING: This will delete every log in the database. To confirm scan again the clear_all barcode.").strip().lower()
    if response == "clear_all":
        reader.logger.clear_all()
    else:
        print("Operation cancelled")
