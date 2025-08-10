from barcode_lib.handlers.base import ModeBase
import re

PCT_RE = re.compile(r"^\s*(\d{1,3})\s*%?\s*$")

class SetMode(ModeBase):
    """
    Flujo:
      - Escanear SKU  -> queda pendiente
      - Escanear %    -> aplica sobre el 'último item' (qty-1 + percent=pct) o reemplaza fracción abierta
    Reglas extra:
      - Si se escanea un comando (modo/estado/config) en cualquier paso, se despacha y NO se trata como SKU/%
    """
    def __init__(self, reader):
        super().__init__(reader)
        self._pending_sku = None

    def _is_command(self, code: str) -> bool:
        try:
            return (code in self.reader.modes) or (code in self.reader.states) or (code in self.reader.configs)
        except Exception:
            return False

    def process_code(self, code: str):
        code = (code or "").strip()
        if not code:
            return

        # 1) Comando tiene prioridad absoluta (bypass del modo set)
        if self._is_command(code):
            self.reader._dispatch(code)
            # resetear estado interno del modo set por si volvemos luego
            self._pending_sku = None
            return

        # 2) Paso 1: esperar SKU
        if self._pending_sku is None:
            self._pending_sku = code
            if self.reader.on_warning:
                self.reader.on_warning(f"[set] SKU {code} leído. Ahora escanea porcentaje (ej: 25%).")
            return

        # 3) Paso 2: esperar porcentaje
        m = PCT_RE.match(code)
        if not m:
            # no es porcentaje válido → permitir re-seleccionar SKU
            if self.reader.on_warning:
                self.reader.on_warning(f"[set] Valor '{code}' no es un porcentaje válido. Intenta '25%'.")
            return

        pct = max(0, min(100, int(m.group(1))))
        sku = self._pending_sku
        self.reader.logger.log_set(sku, pct)
        if self.reader.on_warning:
            self.reader.on_warning(f"[set] {sku} {pct}% aplicado.")
        # listo → reiniciar
        self._pending_sku = None

