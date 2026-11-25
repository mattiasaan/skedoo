"""Codice ereditato dalla V4 (pacchetto `orario`): segmentazione, parser, validatori, configurazione.

`orario/` è una copia della V4 (history/OCR/V4-AI) tenuta in questa cartella: la V5 non dipende da file
esterni. Regole e formato del JSON stanno lì; questo modulo ne espone solo le parti usate da gemini_ocr.
"""
from orario import parse
from orario import pipeline
from orario.config import load_config as load_v4_config
from orario.engines import ingrandisci
from orario.segment import righe_pannello, ritaglia_riga, segmenta_riquadri

__all__ = ["parse", "pipeline", "load_v4_config", "ingrandisci",
           "righe_pannello", "ritaglia_riga", "segmenta_riquadri"]
