import sys, threading, time
from barcode_lib.reader import BarcodeReader
from barcode_lib.gui import run_gui

def stdin_loop(reader: BarcodeReader):
    # Read from same terminal and dispatch; non-blocking exit when GUI closes
    for line in sys.stdin:
        code = line.strip()
        if not code: continue
        try:
            reader._dispatch(code)
        except Exception as e:
            print("ERR:", e)

def main():
    no_gui = "--no-gui" in sys.argv
    reader = BarcodeReader()
    if no_gui:
        print("Barcode reader ready. Current mode:", reader.current_mode.__class__.__name__)
        try:
            while True:
                reader.read_code()
        except KeyboardInterrupt:
            print("\nExiting.")
    else:
        t = threading.Thread(target=stdin_loop, args=(reader,), daemon=True)
        t.start()
        run_gui(reader)

if __name__ == "__main__":
    main()
