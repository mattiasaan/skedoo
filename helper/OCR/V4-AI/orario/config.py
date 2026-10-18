"""Caricamento configurazione (config.json) con valori di default."""
import json
import os
from pathlib import Path

DEFAULTS = {
    "motori": ["ollama", "rapidocr", "tesseract"],
    "ollama": {
        "host": "http://localhost:11434",
        "model": "qwen3-vl:4b",
        "scale": [3],
        "num_ctx": 4096,
        "timeout_s": 900,
        "keep_alive": "10m",
        "think": None,
    },
    "tesseract_cmd": None,
    "voti_minimi": 2,
    "politica": "maggioranza",       # "maggioranza" | "unanime"
    "orari_noti": [],
    "classi_file": None,             # JSON: lista di stringhe o di oggetti con campo "id"
    "aule_file": None,               # JSON: lista di stringhe ("AULA D205", "LAB. B119", "TALVERA")
    "classi_valide": None,           # in alternativa: lista diretta. None = solo controllo di formato
    "aule_valide": None,
    "aule_nominali": ["MAGNA", "CALABRONE", "UDIENZE", "TALVERA"],
    "salva_ritagli": True,
}


def _merge(base: dict, extra: dict) -> dict:
    out = dict(base)
    for k, v in extra.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def _carica_elenco(path, base: Path):
    p = Path(path)
    if not p.is_absolute():
        p = base / p
    if not p.is_file():
        raise FileNotFoundError(f"File elenco non trovato: {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    out = []
    for x in data:
        v = x.get("id") if isinstance(x, dict) else x
        if v:
            out.append(str(v).strip().upper().replace(" ", "") if isinstance(x, dict) else str(v).strip().upper())
    return sorted(set(out))


def core_aula(a: str) -> str:
    """'AULA D205' / 'LAB. D205' -> 'D205' (il prefisso non distingue l'aula)."""
    a = a.strip().upper()
    for pre in ("AULA ", "LAB. ", "LAB "):
        if a.startswith(pre):
            return a[len(pre):].strip()
    return a


def load_config(path=None) -> dict:
    cfg = dict(DEFAULTS)
    base = Path(__file__).resolve().parent.parent
    candidates = [path] if path else [Path("config.json"), base / "config.json"]
    for p in candidates:
        if p and Path(p).is_file():
            base = Path(p).resolve().parent
            with open(p, encoding="utf-8") as f:
                cfg = _merge(cfg, json.load(f))
            break
    if cfg.get("classi_file"):
        cfg["classi_valide"] = _carica_elenco(cfg["classi_file"], base)
    if cfg.get("aule_file"):
        cfg["aule_valide"] = _carica_elenco(cfg["aule_file"], base)
    if cfg.get("aule_valide"):
        cfg["_aule_core"] = sorted({core_aula(a) for a in cfg["aule_valide"]})
    return cfg


def find_tesseract(cfg: dict):
    """Percorso di tesseract: config -> PATH -> posizioni tipiche di Windows."""
    import shutil
    if cfg.get("tesseract_cmd") and os.path.isfile(cfg["tesseract_cmd"]):
        return cfg["tesseract_cmd"]
    found = shutil.which("tesseract")
    if found:
        return found
    for p in (r"C:\Program Files\Tesseract-OCR\tesseract.exe",
              r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
              os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe")):
        if os.path.isfile(p):
            return p
    return None
