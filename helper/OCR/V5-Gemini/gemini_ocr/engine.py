"""Lettura dei ritagli con l'API Gemini (REST generateContent, nessuna libreria esterna).

Tutti i ritagli di un cartellone vanno in UNA richiesta (immagini numerate u01, u02, ...) e la risposta
è un JSON {"unita": [{"id": "u01", "righe": [...]}, ...]} vincolato da responseSchema.
Così un cartellone costa una sola richiesta: il piano gratuito ha pochi messaggi al giorno per modello.

Come nella V4 il modello trascrive soltanto: interpretazione e controlli restano al codice della V4.

Errori:
  - 429 per limite al minuto, 5xx, rete: si riprova (attesa indicata da Google, al massimo max_attesa_s)
  - 429 per quota giornaliera finita o 404 (modello non disponibile): si passa al modello successivo
  - altro 4xx (chiave non valida, richiesta rifiutata): GeminiError subito
"""
from __future__ import annotations

import base64
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request

import cv2

from .v4 import ingrandisci


DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


class GeminiError(Exception):
    """Errore dell'API Gemini (il messaggio non contiene mai la chiave)."""


class QuotaExhausted(GeminiError):
    """Quota esaurita per tutti i modelli configurati: riprovare più tardi."""


class InvalidKey(GeminiError):
    """Chiave API rifiutata da Google (400 API_KEY_INVALID, 401, 403)."""


class _Retry(Exception):
    def __init__(self, message, wait=None):
        super().__init__(message)
        self.wait = wait


class _NextModel(Exception):
    pass


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "Sei un trascrittore di testo. Ricevi alcuni ritagli di un cartellone di variazioni d'orario di una "
    "scuola italiana. Ogni ritaglio e' preceduto dal suo identificativo (u01, u02, ...) e dal tipo. "
    "Per OGNI ritaglio restituisci l'identificativo e il testo che vedi, una riga visiva per elemento "
    "di 'righe', dall'alto in basso. Riporta carattere per carattere solo cio' che e' scritto, compresi "
    "i simboli * ° + : - . (anche in apice). NON correggere, NON completare, NON inventare, NON usare il "
    "testo di altri ritagli. Se un ritaglio non contiene testo leggibile restituisci 'righe' vuoto."
)

ISTRUZIONI = {
    "riga": ("una sola riga del pannello CAMBIO AULA, di solito 'CLASSE : ORA - ORA AULA CODICE', per esempio "
             "'3 C/T : 11.45 - 13.25 AULA B207' oppure '1 MAQ1 : 09.50 - 10.40 LAB. B119'. Se all'inizio "
             "non c'e' la classe non scriverla. Una sola stringa in 'righe'."),
    "riquadro": ("riquadro con un'intestazione (es. 'ENTRA ALLE 09.00', 'ESCE ALLE 12.35', 'NO LEZ. POM.'), "
                 "righe di classi separate da '+' (es. '1 F + 4 J*') ed eventuali note che iniziano con * o °. "
                 "Mantieni '+', * e ° esattamente dove sono."),
    "info": "riquadro informativo: trascrivi tutto, compresi nomi, numeri, orari, classi e simboli.",
    "titolo": "titolo con giorno della settimana, numero e mese. Una sola stringa in 'righe'.",
}

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "unita": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "STRING"},
                    "righe": {"type": "ARRAY", "items": {"type": "STRING"}},
                },
                "required": ["id", "righe"],
            },
        },
    },
    "required": ["unita"],
}


def _png_b64(img) -> str:
    ok, buf = cv2.imencode(".png", img)
    if not ok:
        raise ValueError("ritaglio non codificabile in PNG")
    return base64.b64encode(buf.tobytes()).decode()


# ---------------------------------------------------------------------------
# Motore
# ---------------------------------------------------------------------------
class GeminiEngine:
    """Interfaccia usata da gemini_ocr.pipeline: read_batch([(uid, kind, crop), ...]) -> {uid: righe}."""

    kinds = {"riga", "riquadro", "titolo", "info"}

    def __init__(self, api_key: str, models, base_url=DEFAULT_BASE_URL,
                 scale=2, timeout_s=180, max_unita_per_richiesta=40, max_tentativi=4, max_attesa_s=90,
                 generation_config=None, sleep=time.sleep, log=None):
        if not api_key:
            raise GeminiError("GEMINI_API_KEY mancante: creala su https://aistudio.google.com/apikey")
        self.models = [models] if isinstance(models, str) else list(models)
        if not self.models:
            raise GeminiError("nessun modello Gemini configurato")
        self._key = api_key
        self.base_url = base_url.rstrip("/")
        self.scale = scale
        self.timeout = timeout_s
        self.batch = max(1, int(max_unita_per_richiesta))
        self.max_tentativi = max(1, int(max_tentativi))
        self.max_attesa = max_attesa_s
        self.generation_config = dict(generation_config or {})
        self._sleep = sleep
        self._log = log or (lambda m: None)
        self._esauriti = {}      # modello -> istante fino a cui non riprovarlo (quota giornaliera finita)
        self.model = self.models[0]   # modello dell'ultima lettura riuscita (va nel JSON: motore.modello)
        self.name = f"gemini:{self.model}@{scale}x"

    @classmethod
    def from_config(cls, cfg: dict, api_key: str, log=None, **kw):
        g = cfg["gemini"]
        return cls(api_key, g["models"], base_url=g.get("base_url") or DEFAULT_BASE_URL,
                   scale=g.get("scale", 2), timeout_s=g.get("timeout_s", 180),
                   max_unita_per_richiesta=g.get("max_unita_per_richiesta", 40),
                   max_tentativi=g.get("max_tentativi", 4), max_attesa_s=g.get("max_attesa_s", 90),
                   generation_config=g.get("generation_config"), log=log, **kw)

    def supports(self, kind: str) -> bool:
        return kind in self.kinds

    # ------------------------------------------------------------------ HTTP
    def _request(self, method, path, payload=None):
        req = urllib.request.Request(
            f"{self.base_url}/{path}", method=method,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={"Content-Type": "application/json", "x-goog-api-key": self._key})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:  # noqa: S310 - base_url dalla configurazione
            return json.loads(r.read().decode())

    def verifica(self) -> list:
        """Controlla chiave e modelli (GET /models, non consuma quota). Restituisce i modelli disponibili
        tra quelli configurati. InvalidKey se la chiave è rifiutata, GeminiError/URLError altrimenti."""
        try:
            data = self._request("GET", "models?pageSize=1000")
        except urllib.error.HTTPError as exc:
            err = self._http_error(exc, "verifica")
            raise (err if isinstance(err, GeminiError) else GeminiError(str(err))) from None
        nomi = {m.get("name", "").removeprefix("models/") for m in data.get("models", [])}
        return [m for m in self.models if m in nomi]

    def _http_error(self, exc: urllib.error.HTTPError, model: str) -> Exception:
        try:
            body = json.loads(exc.read(20000).decode("utf-8", "replace"))
        except (ValueError, OSError):
            body = {}
        finally:
            exc.close()
        err = body.get("error", {}) if isinstance(body, dict) else {}
        message = str(err.get("message") or exc.reason or "")[:200]
        details = err.get("details") or []
        text = json.dumps(details)
        if exc.code in (401, 403) or "API_KEY_INVALID" in text or "API key not valid" in message:
            return InvalidKey(f"Gemini: chiave API rifiutata ({exc.code})")
        if exc.code == 429:
            wait = None
            for d in details:
                if str(d.get("@type", "")).endswith("RetryInfo"):
                    m = re.match(r"([\d.]+)s", str(d.get("retryDelay", "")))
                    wait = float(m.group(1)) if m else None
            giornaliera = "PerDay" in text or "per day" in message.lower()
            if giornaliera:
                return _NextModel(f"{model}: quota giornaliera esaurita")
            return _Retry(f"{model}: limite di richieste raggiunto (429)", wait)
        if exc.code == 404:
            return _NextModel(f"{model}: modello non disponibile (404)")
        if exc.code >= 500:
            return _Retry(f"{model}: errore del servizio ({exc.code})")
        return GeminiError(f"Gemini: richiesta rifiutata ({exc.code}): {message}")

    def _generate(self, model: str, payload: dict) -> dict:
        """Una chiamata con i tentativi per gli errori temporanei."""
        attesa = 2.0
        for tentativo in range(1, self.max_tentativi + 1):
            try:
                try:
                    return self._request("POST", f"models/{urllib.parse.quote(model)}:generateContent", payload)
                except urllib.error.HTTPError as exc:
                    raise self._http_error(exc, model) from None
                except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
                    raise _Retry(f"{model}: rete ({type(exc).__name__})") from None
            except _Retry as r:
                if tentativo == self.max_tentativi:
                    raise GeminiError(str(r)) from None
                wait = min(self.max_attesa, r.wait if r.wait is not None else attesa)
                self._log(f"[GEMINI] {r} - nuovo tentativo tra {wait:.0f}s")
                self._sleep(wait)
                attesa *= 2
        raise AssertionError("non raggiungibile")

    # ------------------------------------------------------------------ lettura
    def _payload(self, items) -> dict:
        parts = []
        for sid, kind, crop in items:
            parts.append({"text": f"{sid} (tipo {kind}): {ISTRUZIONI[kind]}"})
            img = ingrandisci(crop, self.scale, border=12) if self.scale and self.scale != 1 else crop
            parts.append({"inline_data": {"mime_type": "image/png", "data": _png_b64(img)}})
        parts.append({"text": f"Restituisci una voce per ciascuno dei {len(items)} ritagli."})
        gen = {"responseMimeType": "application/json", "responseSchema": RESPONSE_SCHEMA}
        gen.update(self.generation_config)
        return {"systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "contents": [{"role": "user", "parts": parts}],
                "generationConfig": gen}

    def _leggi_blocco(self, items) -> dict:
        payload = self._payload(items)
        ultimo = None
        for model in self.models:
            if self._esauriti.get(model, 0) > time.time():
                continue
            try:
                resp = self._generate(model, payload)
            except _NextModel as exc:
                ultimo = exc
                self._log(f"[GEMINI] {exc}: passo al modello successivo")
                self._esauriti[model] = time.time() + 3600   # riprova tra un'ora (la quota si azzera a mezzanotte PT)
                continue
            self.model = model
            self.name = f"gemini:{model}@{self.scale}x"
            return estrai_unita(resp)
        raise QuotaExhausted(f"Gemini: nessun modello disponibile ({ultimo or 'quote esaurite'})")

    def read_batch(self, items) -> dict:
        """items: [(uid, kind, crop)] -> {uid: [righe lette]}. Un uid assente = non letto dal modello."""
        out = {}
        for start in range(0, len(items), self.batch):
            blocco = items[start:start + self.batch]
            ids = {f"u{i:02d}": uid for i, (uid, _, _) in enumerate(blocco, start + 1)}
            letti = self._leggi_blocco([(sid, kind, crop) for sid, (_, kind, crop) in zip(ids, blocco)])
            for sid, righe in letti.items():
                if sid in ids and ids[sid] not in out:
                    out[ids[sid]] = righe
        return out

    def read(self, crop, kind) -> list:
        """Un solo ritaglio (stessa interfaccia del motore della V4)."""
        return self.read_batch([("x", kind, crop)]).get("x") or []


def estrai_unita(resp: dict) -> dict:
    """Dalla risposta di generateContent a {id: [righe]}. GeminiError se bloccata o non in JSON."""
    feedback = resp.get("promptFeedback") or {}
    if feedback.get("blockReason"):
        raise GeminiError(f"Gemini: richiesta bloccata ({feedback['blockReason']})")
    cands = resp.get("candidates") or []
    if not cands:
        raise GeminiError("Gemini: risposta senza candidati")
    cand = cands[0]
    testo = "".join(p.get("text", "") for p in (cand.get("content") or {}).get("parts", [])
                    if not p.get("thought"))
    try:
        data = json.loads(testo)
    except ValueError:
        m = re.search(r"\{.*\}", testo, re.S)
        try:
            data = json.loads(m.group(0)) if m else None
        except ValueError:
            data = None
    if not isinstance(data, dict) or not isinstance(data.get("unita"), list):
        raise GeminiError(f"Gemini: risposta non in JSON (finishReason={cand.get('finishReason')})")
    out = {}
    for u in data["unita"]:
        if not isinstance(u, dict) or not isinstance(u.get("righe"), list):
            continue
        sid = str(u.get("id", "")).strip().lower()
        out.setdefault(sid, [str(x) for x in u["righe"] if str(x).strip()])
    return out
