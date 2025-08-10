from tabulate import tabulate
def zero_percent(reader): reader.logger.set_all_percent(0); print("[State] Set 0% to all."); 
def exit_program(reader): print("[State] Exiting program"); raise KeyboardInterrupt
def show(reader):
    rows=reader.logger.last(10); headers=["ID","SKU","PRODUCT","BRAND","MODE","TIMESTAMP"]
    view=[[r[0],r[1],r[2] or "",r[3] or "",r[7],r[8]] for r in rows]
    print(tabulate(view, headers=headers, tablefmt="github"))
def back(reader): reader.logger.undo_last(); print("[State] Last action undone.")
def stock(reader):
    rows=reader.logger.stock_table(limit=100); headers=["SKU","PRODUCT","BRAND","STOCK"]
    view=[[r[0],r[1] or "",r[2] or "",r[6]] for r in rows]; print(tabulate(view, headers=headers, tablefmt="github"))
def rebuild_stock(reader):
    ans=input("Type 'REBUILD' to rebuild: ").strip()
    if ans.upper()=="REBUILD": reader.logger.rebuild_stock(); print("[State] Rebuilt from scans.")
    else: print("Cancelled.")
def clear_all(reader):
    ans=input("Type 'DELETE ALL' to erase: ").strip()
    if ans.upper()=="DELETE ALL": reader.logger.clear_all(); print("[State] All logs cleared.")
    else: print("Cancelled.")
def info(reader):
    sku=input("SKU to inspect: ").strip()
    info=reader.logger.catalog.get(sku) or {"product":None,"brand":None,"category":None,"url":None}
    print(tabulate([[sku,info.get("product"),info.get("brand"),info.get("category"),info.get("url")]], headers=["SKU","PRODUCT","BRAND","CATEGORY","URL"], tablefmt="github"))
