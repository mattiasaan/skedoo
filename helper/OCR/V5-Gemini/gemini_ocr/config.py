"""Configurazione: le chiavi della V4 (griglia orari, elenchi di classi e aule, ...) + la sezione "gemini"."""
from pathlib import Path

from .v4 import load_v4_config

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
    """config.json di questa cartella (o `path`). Le chiavi della V4 passano dal suo caricatore (default,
    elenchi di classi e aule relativi alla cartella del file); "gemini" si completa con GEMINI_DEFAULTS."""
    p = Path(path) if path else HERE / "config.json"
    if not p.is_file():
        raise FileNotFoundError(f"Configurazione non trovata: {p}")
    cfg = load_v4_config(str(p))
    gemini = dict(GEMINI_DEFAULTS)
    gemini.update(cfg.get("gemini") or {})
    if isinstance(gemini["models"], str):
        gemini["models"] = [gemini["models"]]
    cfg["gemini"] = gemini
    cfg.pop("ollama", None)  # non usato qui
    return cfg


def parse_models(value: str) -> list:
    """'a, b ,c' -> ['a', 'b', 'c'] (variabile GEMINI_MODELS / opzione --modello)."""
    return [m.strip() for m in (value or "").split(",") if m.strip()]
