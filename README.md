# BarcodeScanner

barcode_lib/
├── __init__.py
├── main.py                # Punto de entrada
├── reader.py              # Clase principal BarcodeReader
├── utils.py               # Carga dinámica y lectura de configuración
├── config/
│   ├── __init__.py
│   └── mappings.json      # Diccionario de rutas para modos, estados, configs
├── handlers/              # Modos de escaneo
│   ├── __init__.py
│   ├── base.py            # Clase ModeBase
│   ├── add.py             # AddMode
│   ├── input.py           # InputMode
│   ├── output.py          # OutputMode
│   ├── remove.py          # RemoveMode
│   └── set.py             # SetMode (maneja % y SKU)
├── states/
│   ├── __init__.py
│   └── functions.py       # Funciones como back(), show(), exit()
├── configs/
│   ├── __init__.py
│   └── functions.py       # sound on/off, etc.
└── db/
    ├── __init__.py
    └── logger.py          # Clase ScanLogger (SQLite)
    
## Basic Information:
    - Add:
    - Remove: Deletes product (SKU) from cache (product database)
    
    - Back: Undo last action
    - Show: Shows last actions
    
    - Opened: Not implemented
    
    - Input: Adds items to stock database
    - Output: Removes items from stock database
    
    - Set: Enables item edition. Current settings:
        - 100%: Sets item as opened, but not used
        - 75%: Sets item to 3/4 remaining
        - 50%: Sets item as half used
        - 25% Sets item as 25% remaining
        - 0%: Sets item as empty
        
    - Exit: Close program
    
    - Sound on/off: Not implemented.

## TODO

- Resolve WebScrapping

- Implement add mode

- Solve output mode: Calling unnecesary logger.log()

- Add set mode to barcode images.

- Implement product type: 
    - Manual: Use set mode and scan product to add, then another product of the same class to map together as same product.
    - Automatic: Using webscrapping.
