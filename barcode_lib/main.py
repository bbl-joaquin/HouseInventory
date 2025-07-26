from barcode_lib.reader import BarcodeReader

def main():
    reader = BarcodeReader()
    print("Barcode reader ready. Current mode:", reader.current_mode.__class__.__name__)
    while True:
        try:
            reader.read_code()
        except KeyboardInterrupt:
            print("\nExiting.")
            break

if __name__ == "__main__":
    main()
