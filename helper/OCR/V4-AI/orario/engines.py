"""
Motore di trascrizione: Qwen3-VL via Ollama.

Riceve il ritaglio di UN'unita' (una riga o un riquadro) e restituisce le righe di
testo che legge. Nient'altro: l'interpretazione e il controllo di coerenza sono fatti
dal codice (parse.py / validazione.py / pipeline.py).
"""
import base64
import json
import re
import time
import urllib.request
import urllib.error

import cv2
import numpy as np


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


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------
class Engine:
    """Interfaccia minima del motore (serve anche ai motori finti dei test)."""
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

    def _chat_con_retry(self, payload, tentativi=2):
        """Con un solo motore un errore di rete transitorio non deve perdere l'unita'."""
        for i in range(tentativi):
            try:
                return self._http("/api/chat", payload, timeout=self.timeout)
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                if i == tentativi - 1:
                    raise
                time.sleep(2)

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
        resp = self._chat_con_retry(payload)
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
