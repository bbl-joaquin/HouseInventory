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
