"""
Motori di trascrizione. Ognuno riceve il ritaglio di UN'unita' (una riga o un
riquadro) e restituisce le righe di testo che legge. Nient'altro: l'interpretazione
e il controllo sono fatti dal codice (parse.py / consensus.py).

Famiglie indipendenti (sbagliano in modi diversi, quindi il loro accordo conta):
  ollama    modello di visione locale (es. Qwen3-VL)
  rapidocr  OCR neurale (modelli PaddleOCR via ONNX)
  tesseract OCR classico
"""
import base64
import json
import re
import urllib.request
import urllib.error

import cv2
import numpy as np

from .segment import righe_testo, ritaglia_riga


class EngineUnavailable(Exception):
    pass


# ---------------------------------------------------------------------------
# Utilita' immagine
# ---------------------------------------------------------------------------
def _bordo_colore(img: np.ndarray):
    h, w = img.shape[:2]
    mg = max(1, min(2, h // 4, w // 4))
    ring = np.vstack([img[:mg].reshape(-1, 3), img[-mg:].reshape(-1, 3),
                      img[:, :mg].reshape(-1, 3), img[:, -mg:].reshape(-1, 3)])
    return tuple(int(v) for v in np.median(ring, axis=0))


def ingrandisci(img: np.ndarray, scale: float, border: int = 10) -> np.ndarray:
    """Ingrandisce (Lanczos) e aggiunge un margine del colore di sfondo."""
    big = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_LANCZOS4)
    return cv2.copyMakeBorder(big, border, border, border, border,
                              cv2.BORDER_CONSTANT, value=_bordo_colore(img))


def _png_b64(img: np.ndarray) -> str:
    ok, buf = cv2.imencode(".png", img)
    return base64.b64encode(buf.tobytes()).decode()


def binarizza_riga(crop: np.ndarray, altezza=72) -> np.ndarray:
    """Riga singola -> bianco/nero con testo nero su fondo bianco (per Tesseract)."""
    h = crop.shape[0]
    scale = max(2.0, altezza / max(h, 1))
    big = cv2.resize(crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(big, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    if bw.mean() < 127:                 # maggioranza scura = sfondo scuro -> inverti
        bw = cv2.bitwise_not(bw)
    return cv2.copyMakeBorder(bw, 14, 14, 14, 14, cv2.BORDER_CONSTANT, value=255)


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------
class Engine:
    family = "base"
    name = "base"
    kinds = {"riga", "riquadro", "titolo", "info"}

    def supports(self, kind: str) -> bool:
        return kind in self.kinds

    def read(self, crop: np.ndarray, kind: str) -> list:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Ollama (Qwen3-VL o altro modello di visione)
# ---------------------------------------------------------------------------
_PROMPT_RIGA = (
    "Trascrivi ESATTAMENTE il testo scritto in questa immagine: e' una sola riga di un "
    "orario scolastico, di solito nel formato 'CLASSE : ORA - ORA AULA CODICE', per esempio "
    "'3 C/T : 11.45 - 13.25 AULA B207' oppure '1 MAQ1 : 09.50 - 10.40 LAB. B119'. "
    "Riporta carattere per carattere solo cio' che vedi, compresi eventuali simboli * o °. "
    "NON correggere, NON completare, NON inventare. Se all'inizio della riga non c'e' la "
    "classe, non scriverla. Rispondi solo con JSON: {\"testo\": \"...\"}"
)
_PROMPT_BOX = (
    "Trascrivi ESATTAMENTE il testo di questo riquadro di un orario scolastico, una riga "
    "visiva per volta, dall'alto in basso. Sono tipiche: un'intestazione (es. 'ENTRA ALLE "
    "09.00', 'ESCE ALLE 12.35'), una o piu' righe di classi separate da '+' (es. '1 F + 4 J*'), "
    "ed eventuali note che iniziano con * o °. Mantieni i '+' e i simboli * e ° (anche se in "
    "apice) esattamente dove li vedi. NON correggere, NON completare, NON inventare. "
    "Rispondi solo con JSON: {\"righe\": [\"...\", \"...\"]}"
)
_PROMPT_INFO = (
    "Trascrivi ESATTAMENTE tutto il testo di questo riquadro informativo di un orario "
    "scolastico, una riga visiva per volta, dall'alto in basso, compresi nomi, numeri, orari, "
    "classi e simboli (* ° + -). NON correggere, NON completare, NON inventare. "
    "Rispondi solo con JSON: {\"righe\": [\"...\", \"...\"]}"
)
_PROMPT_TITOLO = (
    "Trascrivi ESATTAMENTE il testo di questo titolo (giorno della settimana, numero e mese). "
    "Rispondi solo con JSON: {\"testo\": \"...\"}"
)
_SCHEMA_TESTO = {"type": "object", "properties": {"testo": {"type": "string"}}, "required": ["testo"]}
_SCHEMA_RIGHE = {"type": "object",
                 "properties": {"righe": {"type": "array", "items": {"type": "string"}}},
                 "required": ["righe"]}


class OllamaVLM(Engine):
    family = "ollama"

    def __init__(self, host, model, scale=3, num_ctx=4096, timeout_s=900,
                 keep_alive="10m", think=None):
        self.host = host.rstrip("/")
        self.model = model
        self.scale = scale
        self.num_ctx = num_ctx
        self.timeout = timeout_s
        self.keep_alive = keep_alive
        self.think = think
        self.name = f"ollama:{model}@{scale}x"
        self._check()

    def _http(self, path, payload=None, timeout=30):
        req = urllib.request.Request(
            self.host + path,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())

    def _check(self):
        try:
            tags = self._http("/api/tags", timeout=5)
        except Exception as e:      # noqa: BLE001
            raise EngineUnavailable(
                f"Ollama non raggiungibile su {self.host} ({e}). "
                "Avvia Ollama e fai: ollama pull " + self.model)
        names = [m.get("name", "") for m in tags.get("models", [])]
        base = self.model.split(":")[0]
        if not any(n == self.model or n.startswith(self.model) for n in names):
            raise EngineUnavailable(
                f"Modello '{self.model}' non installato (presenti: {names or 'nessuno'}). "
                f"Esegui: ollama pull {self.model}")

    def read(self, crop, kind):
        if kind == "riga":
            prompt, schema = _PROMPT_RIGA, _SCHEMA_TESTO
        elif kind == "titolo":
            prompt, schema = _PROMPT_TITOLO, _SCHEMA_TESTO
        elif kind == "info":
            prompt, schema = _PROMPT_INFO, _SCHEMA_RIGHE
        else:
            prompt, schema = _PROMPT_BOX, _SCHEMA_RIGHE
        img = ingrandisci(crop, self.scale, border=12)
        payload = {
            "model": self.model,
            "stream": False,
            "format": schema,
            "keep_alive": self.keep_alive,
            "options": {"temperature": 0, "seed": 0, "num_ctx": self.num_ctx},
            "messages": [{"role": "user", "content": prompt, "images": [_png_b64(img)]}],
        }
        if self.think is not None:
            payload["think"] = self.think
        resp = self._http("/api/chat", payload, timeout=self.timeout)
        content = resp.get("message", {}).get("content", "")
        return _estrai_righe(content)


def _estrai_righe(content: str) -> list:
    """Interpreta la risposta JSON del modello (tollerante a testo extra)."""
    data = None
    try:
        data = json.loads(content)
    except Exception:       # noqa: BLE001
        m = re.search(r"\{.*\}", content, re.S)
        if m:
            try:
                data = json.loads(m.group(0))
            except Exception:   # noqa: BLE001
                data = None
    if not isinstance(data, dict):
        raise ValueError(f"risposta del modello non in JSON: {content[:120]!r}")
    if "righe" in data and isinstance(data["righe"], list):
        return [str(x) for x in data["righe"] if str(x).strip()]
    if "testo" in data:
        return [ln for ln in str(data["testo"]).splitlines() if ln.strip()]
    raise ValueError(f"JSON senza 'testo' o 'righe': {content[:120]!r}")


# ---------------------------------------------------------------------------
# RapidOCR (PaddleOCR via ONNX)
# ---------------------------------------------------------------------------
class RapidOCREngine(Engine):
    family = "rapidocr"
    name = "rapidocr"

    def __init__(self, scale=5):
        try:
            from rapidocr_onnxruntime import RapidOCR
        except Exception as e:      # noqa: BLE001
            raise EngineUnavailable(f"rapidocr-onnxruntime non installato ({e}). "
                                    "pip install rapidocr-onnxruntime")
        self.ocr = RapidOCR()
        self.scale = scale

    def _ocr_riga(self, crop):
        img = ingrandisci(crop, self.scale, border=16)
        res, _ = self.ocr(img)
        if not res:
            return ""
        items = sorted(res, key=lambda r: min(p[0] for p in r[0]))
        return " ".join(t for _, t, _ in items)

    def read(self, crop, kind):
        if kind in ("riga", "titolo"):
            return [self._ocr_riga(crop)]
        # riquadri: immagine intera, righe raggruppate per posizione (sfondi misti ok)
        img = ingrandisci(crop, self.scale, border=16)
        res, _ = self.ocr(img)
        if not res:
            return []
        items = []
        for box, text, score in res:
            ys = [p[1] for p in box]
            xs = [p[0] for p in box]
            items.append({"cy": (min(ys) + max(ys)) / 2, "h": max(ys) - min(ys),
                          "x": min(xs), "t": text})
        items.sort(key=lambda i: i["cy"])
        lines, cur = [], []
        for it in items:
            if cur and abs(it["cy"] - cur[-1]["cy"]) > 0.6 * max(it["h"], cur[-1]["h"]):
                lines.append(cur)
                cur = []
            cur.append(it)
        if cur:
            lines.append(cur)
        return [" ".join(i["t"] for i in sorted(ln, key=lambda i: i["x"])) for ln in lines]


# ---------------------------------------------------------------------------
# Tesseract
# ---------------------------------------------------------------------------
_WL = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ.:-/*+° "


class TesseractEngine(Engine):
    family = "tesseract"
    name = "tesseract"
    kinds = {"riga", "riquadro", "titolo"}      # non adatto ai riquadri con sfondi misti
    stretto = True                              # preferisce il ritaglio senza margini rossi

    def __init__(self, cmd=None):
        try:
            import pytesseract
        except Exception as e:      # noqa: BLE001
            raise EngineUnavailable(f"pytesseract non installato ({e})")
        if cmd:
            pytesseract.pytesseract.tesseract_cmd = cmd
        try:
            langs = set(pytesseract.get_languages(config=""))
        except Exception as e:      # noqa: BLE001
            raise EngineUnavailable(f"Tesseract non trovato ({e})")
        self.pt = pytesseract
        self.lang = "ita+eng" if {"ita", "eng"} <= langs else "eng"

    def _line(self, crop, whitelist=True):
        bw = binarizza_riga(crop)
        cfg = "--oem 3 --psm 7"
        if whitelist:
            cfg += f" -c tessedit_char_whitelist={_WL.replace(' ', '')}"
            cfg += " -c preserve_interword_spaces=1"
        txt = self.pt.image_to_string(bw, lang=self.lang, config=cfg)
        return " ".join(txt.split())

    def read(self, crop, kind):
        if kind == "riga":
            return [self._line(crop)]
        if kind == "titolo":
            return [self._line(crop, whitelist=False)]
        # riquadro: una riga di testo alla volta
        out = []
        for r in righe_testo(crop):
            sub = ritaglia_riga(crop, r, pad=2)
            if sub.size:
                out.append(self._line(sub, whitelist=False))
        return [x for x in out if x]
