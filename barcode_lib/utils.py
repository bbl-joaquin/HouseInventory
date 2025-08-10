import importlib, json
from pathlib import Path
def import_from_path(path: str):
    module_path, obj_name = path.rsplit('.', 1)
    module = importlib.import_module(module_path)
    return getattr(module, obj_name)
def load_config():
    p = Path(__file__).parent / "config" / "mappings.json"
    return json.loads(p.read_text(encoding="utf-8"))
