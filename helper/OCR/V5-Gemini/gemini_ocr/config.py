"""Configurazione: quella della V4 (griglia orari, elenchi di classi e aule, ...) + la sezione "gemini"."""
import json
from pathlib import Path

from .v4 import V4_DIR, load_v4_config

HERE = Path(__file__).resolve().parent.parent

GEMINI_DEFAULTS = {
    # in ordine di preferenza: se la quota giornaliera del primo è finita si passa al successivo
    "models": ["gemini-flash-latest", "gemini-flash-lite-latest"],
    "base_url": "https://generativelanguage.googleapis.com/v1beta",
    "scale": 2,                      # ingrandimento del ritaglio prima dell'invio
    "timeout_s": 90,                 # per richiesta (Gemini a volte resta appeso)
    "max_unita_per_richiesta": 40,   # ritagli per richiesta (di solito un cartellone = una richiesta)
    "max_tentativi": 4,              # per errori temporanei (rete, 5xx, limite al minuto)
    "max_attesa_s": 90,              # attesa massima tra due tentativi
    "generation_config": {},         # campi extra per generationConfig (es. temperature, thinkingConfig)
}


def load_config(path=None) -> dict:
    """config.json di questa cartella (o `path`) sopra la configurazione della V4 indicata da base_config."""
    p = Path(path) if path else HERE / "config.json"
    own = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}
    base = own.get("base_config")
    base_path = (p.parent / base).resolve() if base else V4_DIR / "config.json"
    cfg = load_v4_config(str(base_path))
    gemini = dict(GEMINI_DEFAULTS)
    gemini.update(own.get("gemini") or {})
    if isinstance(gemini["models"], str):
        gemini["models"] = [gemini["models"]]
    cfg["gemini"] = gemini
    cfg.pop("ollama", None)  # non usato qui
    return cfg


def parse_models(value: str) -> list:
    """'a, b ,c' -> ['a', 'b', 'c'] (variabile GEMINI_MODELS / opzione --modello)."""
    return [m.strip() for m in (value or "").split(",") if m.strip()]
