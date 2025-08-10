import os, io, requests, tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk

THUMB_SIZE = (260, 260)

def run_gui(reader):
    app = tk.Tk()
    app.title("HouseInventory")
    app.geometry("1240x780")

    add_dialog_win = {"ref": None}  # para cerrar al salir de modo add

    # ---------- helpers ----------
    def current_mode_name() -> str:
        return reader.current_mode.__class__.__name__.replace("Mode", "").lower()

    def is_command(code: str) -> bool:
        try:
            return (code in reader.modes) or (code in reader.states) or (code in reader.configs)
        except Exception:
            return False

    def fetch_image(url_or_path):
        try:
            if not url_or_path:
                return None
            if str(url_or_path).startswith(("http://", "https://")):
                r = requests.get(url_or_path, timeout=5)
                im = Image.open(io.BytesIO(r.content))
            else:
                im = Image.open(url_or_path)
            im = im.resize(THUMB_SIZE)
            return ImageTk.PhotoImage(im)
        except Exception:
            return None

    def qty_with_fraction(qty, percent) -> str:
        try:
            q = float(qty or 0)
            p = 0 if percent is None else int(percent)
            frac = 0.0 if p <= 0 or p >= 100 else (p / 100.0)
            val = q + frac
            s = f"{val:.2f}".rstrip("0").rstrip(".")
            return s
        except Exception:
            return str(qty if qty is not None else "")

    # ---------- Top bar ----------
    top = ttk.Frame(app, padding=8)
    top.pack(fill="x")

    ttk.Label(top, text="Mode:").pack(side="left")
    mode_var = tk.StringVar(value=current_mode_name())
    ttk.Label(top, textvariable=mode_var, font=("Arial", 12, "bold")).pack(side="left", padx=(4, 12))

    def set_mode(name: str):
        # cerrar diálogo Add si estaba abierto
        if add_dialog_win["ref"] is not None and add_dialog_win["ref"].winfo_exists():
            try:
                add_dialog_win["ref"].destroy()
            except Exception:
                pass
            add_dialog_win["ref"] = None
        # cambiar modo usando mappings existentes
        cls = reader.modes[name]
        try:
            reader.history.append(("mode", reader.current_mode.__class__))
        except Exception:
            pass
        reader.current_mode = cls(reader)
        on_mode_change(name)

    # Botones
    ttk.Button(top, text="Input",  command=lambda: set_mode("input")).pack(side="left", padx=4)
    ttk.Button(top, text="Output", command=lambda: set_mode("output")).pack(side="left", padx=4)
    ttk.Button(top, text="Add",    command=lambda: set_mode("add")).pack(side="left", padx=4)
    ttk.Button(top, text="Set",    command=lambda: set_mode("set")).pack(side="left", padx=4)

    ttk.Button(
        top,
        text="Back (undo)",
        command=lambda: (getattr(reader, "undo_last", lambda: None)(), refresh_logs(), refresh_stock(), code_entry.focus_set())
    ).pack(side="left", padx=10)

    # Entrada de códigos
    ttk.Label(top, text="Scan/Input:").pack(side="left", padx=(12, 4))
    code_var = tk.StringVar()
    code_entry = ttk.Entry(top, textvariable=code_var, width=36, font=("Arial", 12))
    code_entry.pack(side="left", padx=8)
    code_entry.focus_set()

    def on_enter(event=None):
        code = code_var.get().strip()
        if not code:
            return
        m = current_mode_name()

        # En modos ADD y SET, si es comando → DESPACHAR (bypass del flujo de edición)
        if m in ("add", "set") and is_command(code):
            reader._dispatch(code)
        else:
            if m == "add" and not is_command(code):
                # abrir diálogo con prefill
                open_add_dialog(prefill_sku=code)
            else:
                reader._dispatch(code)

        code_var.set("")
        refresh_logs(); refresh_stock(); refresh_known()
        code_entry.focus_set()

    code_entry.bind("<Return>", on_enter)

    # ---------- Notebook ----------
    nb = ttk.Notebook(app)
    nb.pack(fill="both", expand=True)

    # Logs tab
    log_tab = ttk.Frame(nb)
    nb.add(log_tab, text="Logs")
    log_text = tk.Text(log_tab, height=12, state="disabled")
    log_text.pack(fill="both", expand=True, padx=8, pady=8)

    def refresh_logs():
        rows = reader.logger.last(50)
        log_text.configure(state="normal")
        log_text.delete("1.0", "end")
        for r in rows[::-1]:
            r = (r + (None,))[:10]  # asegurar largo
            _id, sku, _p, _b, _c, _i, _u, mode, ts, val = r
            if mode == "set":
                pct = ""
                if val:
                    try:
                        pct = str(val).split("|", 1)[0]
                    except Exception:
                        pct = str(val)
                if pct and not pct.endswith("%"):
                    pct += "%"
                line = f"#{_id}  {ts}  SET    {sku}  {pct}"
            else:
                line = f"#{_id}  {ts}  {str(mode).upper():6}  {sku}"
            log_text.insert("end", line + "\n")
        log_text.configure(state="disabled")

    # Stock tab
    stock_tab = ttk.Frame(nb)
    nb.add(stock_tab, text="Stock")
    left = ttk.Frame(stock_tab); left.pack(side="left", fill="both", expand=True)
    right = ttk.Frame(stock_tab, width=360); right.pack(side="right", fill="y")

    cols = ("sku", "product", "brand", "stock")
    stock_table = ttk.Treeview(left, columns=cols, show="headings", selectmode="browse")
    for c, w in [("sku", 160), ("product", 520), ("brand", 200), ("stock", 100)]:
        stock_table.heading(c, text=c.title())
        stock_table.column(c, width=w, anchor="w")
    stock_table.pack(fill="both", expand=True, padx=8, pady=8)

    detail_img = ttk.Label(right); detail_img.pack(padx=8, pady=(12, 6))
    detail_name = ttk.Label(right, text="", font=("Arial", 12, "bold")); detail_name.pack(anchor="w", padx=8)
    detail_sku  = ttk.Label(right, text=""); detail_sku.pack(anchor="w", padx=8)
    detail_brand= ttk.Label(right, text=""); detail_brand.pack(anchor="w", padx=8)
    detail_cat  = ttk.Label(right, text=""); detail_cat.pack(anchor="w", padx=8)
    detail_url  = ttk.Label(right, text="", foreground="gray"); detail_url.pack(anchor="w", padx=8)

    def on_stock_select(event=None):
        sel = stock_table.selection()
        if not sel:
            return
        values = stock_table.item(sel[0], "values")
        sku = values[0]
        info = reader.logger.catalog.get(sku) or {"product": "", "brand": "", "category": "", "image": None, "url": None}
        detail_name.configure(text=info.get("product") or "")
        detail_sku.configure(text=f"SKU: {sku}")
        detail_brand.configure(text=f"Marca: {info.get('brand') or ''}")
        detail_cat.configure(text=f"Categoría: {info.get('category') or ''}")
        detail_url.configure(text=info.get('url') or "")
        photo = fetch_image(info.get("image"))
        if photo:
            detail_img.configure(image=photo); detail_img.image = photo
        else:
            detail_img.configure(image=""); detail_img.image = None

    stock_table.bind("<<TreeviewSelect>>", on_stock_select)

    def refresh_stock(desc: bool = False):
        rows = reader.logger.stock_table()
        rows = sorted(rows, key=lambda r: r[6], reverse=desc)
        stock_table.delete(*stock_table.get_children())
        for r in rows:
            sku, product, brand, category, image, url, qty, percent = r
            display = qty_with_fraction(qty, percent)
            stock_table.insert("", "end", values=(sku, product or "", brand or "", display))

    # Known DB tab
    prod_tab = ttk.Frame(nb); nb.add(prod_tab, text="Known DB")
    top_search = ttk.Frame(prod_tab); top_search.pack(fill="x")
    q = tk.StringVar()
    search_entry = ttk.Entry(top_search, textvariable=q, width=40)
    search_entry.pack(side="left", padx=8, pady=8)
    ttk.Button(top_search, text="Search", command=lambda: refresh_known()).pack(side="left", padx=6, pady=8)

    frame = ttk.Frame(prod_tab); frame.pack(fill="both", expand=True)
    left2 = ttk.Frame(frame); left2.pack(side="left", fill="both", expand=True)
    right2 = ttk.Frame(frame, width=360); right2.pack(side="right", fill="y")

    prod_table = ttk.Treeview(left2, columns=("sku", "product", "brand", "category"), show="headings", selectmode="browse")
    for c, w in [("sku", 160), ("product", 520), ("brand", 200), ("category", 160)]:
        prod_table.heading(c, text=c.title()); prod_table.column(c, width=w, anchor="w")
    prod_table.pack(fill="both", expand=True, padx=8, pady=8)

    detail_img2 = ttk.Label(right2); detail_img2.pack(padx=8, pady=(12, 6))
    detail_name2 = ttk.Label(right2, text="", font=("Arial", 12, "bold")); detail_name2.pack(anchor="w", padx=8)
    detail_sku2  = ttk.Label(right2, text=""); detail_sku2.pack(anchor="w", padx=8)
    detail_brand2= ttk.Label(right2, text=""); detail_brand2.pack(anchor="w", padx=8)
    detail_cat2  = ttk.Label(right2, text=""); detail_cat2.pack(anchor="w", padx=8)
    detail_url2  = ttk.Label(right2, text="", foreground="gray"); detail_url2.pack(anchor="w", padx=8)

    def on_prod_select(event=None):
        sel = prod_table.selection()
        if not sel: return
        sku = prod_table.item(sel[0], "values")[0]
        info = reader.logger.catalog.get(sku) or {"product": "", "brand": "", "category": "", "image": None, "url": None}
        detail_name2.configure(text=info.get("product") or "")
        detail_sku2.configure(text=f"SKU: {sku}")
        detail_brand2.configure(text=f"Marca: {info.get('brand') or ''}")
        detail_cat2.configure(text=f"Categoría: {info.get('category') or ''}")
        detail_url2.configure(text=info.get("url") or "")
        photo = fetch_image(info.get("image"))
        if photo:
            detail_img2.configure(image=photo); detail_img2.image = photo
        else:
            detail_img2.configure(image=""); detail_img2.image = None

    prod_table.bind("<<TreeviewSelect>>", on_prod_select)

    def refresh_known():
        selected_sku = None
        sel = prod_table.selection()
        if sel:
            try:
                selected_sku = prod_table.item(sel[0], "values")[0]
            except Exception:
                selected_sku = None

        text = q.get().strip()
        rows = reader.logger.catalog.search(text, 200) if text else reader.logger.catalog.search("", 200)
        prod_table.delete(*prod_table.get_children())
        for sku, product, brand, category, image, url in rows:
            prod_table.insert("", "end", values=(sku, product or "", brand or "", category or ""))

        if selected_sku:
            for iid in prod_table.get_children():
                if prod_table.item(iid, "values")[0] == selected_sku:
                    prod_table.selection_set(iid)
                    prod_table.see(iid)
                    break

    def remove_selected():
        sel = prod_table.selection()
        if not sel:
            messagebox.showinfo("Remove", "Select a product in Known DB.")
            code_entry.focus_set()
            return
        sku = prod_table.item(sel[0], "values")[0]
        if messagebox.askyesno("Confirm", f"Remove SKU {sku} from catalog?"):
            reader.logger.remove_known_product(sku)
            refresh_known()
            code_entry.focus_set()
            
    ttk.Button(top_search, text="Remove", command=remove_selected).pack(side="left", padx=6, pady=8)

    # ---------- Add dialog ----------
    def open_add_dialog(prefill_sku: str = ""):
        # Si ya está abierto, enfocarlo
        if add_dialog_win["ref"] is not None and add_dialog_win["ref"].winfo_exists():
            try:
                add_dialog_win["ref"].lift(); add_dialog_win["ref"].focus_force()
            except Exception:
                pass
            return

        d = tk.Toplevel(app)
        add_dialog_win["ref"] = d
        d.title("Add product")
        d.grab_set()
        d.transient(app)

        def on_close():
            try:
                d.destroy()
            finally:
                add_dialog_win["ref"] = None
                code_entry.focus_set()

        d.protocol("WM_DELETE_WINDOW", on_close)

        ttk.Label(d, text="SKU:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        e_sku = ttk.Entry(d, width=50); e_sku.grid(row=0, column=1, padx=6, pady=6)
        if prefill_sku:
            e_sku.insert(0, prefill_sku)
        e_sku.focus_set()

        fields = {}
        for i, name in enumerate(["product", "brand", "category", "url"], start=1):
            ttk.Label(d, text=name.title() + ":").grid(row=i, column=0, sticky="e", padx=6, pady=4)
            ent = ttk.Entry(d, width=50); ent.grid(row=i, column=1, padx=6, pady=4)
            fields[name] = ent

        ttk.Label(d, text="Image:").grid(row=5, column=0, sticky="e", padx=6, pady=4)
        img_frame = ttk.Frame(d); img_frame.grid(row=5, column=1, sticky="w", padx=6, pady=4)
        img_path_var = tk.StringVar(value="")
        ttk.Label(img_frame, textvariable=img_path_var, width=46).pack(side="left", padx=(0, 6))

        def choose_image():
            path = filedialog.askopenfilename(title="Choose image",
                                              filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.webp;*.bmp")])
            if path:
                img_path_var.set(path)

        ttk.Button(img_frame, text="Upload...", command=choose_image).pack(side="left")

        # --- interceptar comandos mientras el foco está en el diálogo ---
        def handle_possible_command(text: str) -> bool:
            code = (text or "").strip()
            if not code:
                return False
            if is_command(code):
                # cerrar diálogo y despachar
                try:
                    on_close()
                except Exception:
                    pass
                reader._dispatch(code)
                # notificar a la GUI del nuevo modo (para que actualice label y foco)
                if hasattr(reader, "on_mode_change") and callable(reader.on_mode_change):
                    try:
                        new_mode = reader.current_mode.__class__.__name__.replace("Mode", "").lower()
                        reader.on_mode_change(new_mode)
                    except Exception:
                        pass
                return True
            return False

        def try_autofill(event=None):
            sku_text = e_sku.get().strip()
            # primero: si es comando, bypass inmediato
            if handle_possible_command(sku_text):
                return
            if not sku_text:
                return
            # autofill normal
            info = reader.logger.catalog.get(sku_text)
            if not info:
                from barcode_lib.web.scraper import scrape_product_info
                data = scrape_product_info(sku_text, force_refresh=False) or {}
                if data:
                    reader.logger.catalog.upsert(sku_text, data)
                    info = data
                else:
                    info = {}
            for k in ("product", "brand", "category", "url"):
                if info.get(k) and not fields[k].get():
                    fields[k].insert(0, info[k])

        # Bindings en el diálogo: Enter y perder foco del SKU
        e_sku.bind("<Return>", try_autofill)
        e_sku.bind("<FocusOut>", try_autofill)

        def save():
            sku = e_sku.get().strip()
            if handle_possible_command(sku):
                return  # ya cambió de modo y se cerró
            if not sku:
                messagebox.showerror("Missing SKU", "Please enter SKU.")
                return
            info = {k: (v.get().strip() or None) for k, v in fields.items()}
            img = img_path_var.get().strip() or None
            if img:
                info["image"] = img
            reader.logger.catalog.upsert(sku, info)
            reader.logger.queue_enrich(sku)
            on_close()
            refresh_known(); refresh_stock(); refresh_logs()

        ttk.Button(d, text="Save", command=save).grid(row=10, column=1, sticky="e", padx=6, pady=8)

    # Notificación de cambio de modo (pistola o botón)
    def on_mode_change(name: str):
        mode_var.set(name)
        if name == "add":
            open_add_dialog()
        else:
            # si salimos de add, cerrar el diálogo si siguiera abierto
            if add_dialog_win["ref"] is not None and add_dialog_win["ref"].winfo_exists():
                try:
                    add_dialog_win["ref"].destroy()
                except Exception:
                    pass
                add_dialog_win["ref"] = None
        code_entry.focus_set()

    reader.on_mode_change = on_mode_change

    # ---------- Arranque ----------
    def periodic():
        refresh_logs(); refresh_stock(); refresh_known()
        app.after(1500, periodic)

    refresh_logs(); refresh_stock(); refresh_known()
    code_entry.focus_set()
    periodic()
    app.mainloop()

