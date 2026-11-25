"""Accesso al codice della V4 (pacchetto `orario`): segmentazione, parser, validatori, configurazione.

La V4 resta la fonte unica di regole e formato del JSON: questa cartella non ne contiene una copia.
Cartella della V4: variabile OCR_V4_DIR, altrimenti ../V4-AI accanto a questa cartella
(nel container: /app/V4-AI, vedi Dockerfile).
"""
import os
import sys
from pathlib import Path

V4_DIR = Path(os.environ.get("OCR_V4_DIR") or Path(__file__).resolve().parents[2] / "V4-AI").resolve()

if not (V4_DIR / "orario" / "pipeline.py").is_file():
    raise ImportError(f"Codice della V4 non trovato in {V4_DIR} (imposta OCR_V4_DIR)")
if str(V4_DIR) not in sys.path:
    sys.path.append(str(V4_DIR))  # in coda: main.py e service.py di questa cartella restano i nostri

from orario import parse  # noqa: E402
from orario import pipeline  # noqa: E402
from orario.config import load_config as load_v4_config  # noqa: E402
from orario.engines import ingrandisci  # noqa: E402
from orario.segment import righe_pannello, ritaglia_riga, segmenta_riquadri  # noqa: E402

__all__ = ["V4_DIR", "parse", "pipeline", "load_v4_config", "ingrandisci",
           "righe_pannello", "ritaglia_riga", "segmenta_riquadri"]
