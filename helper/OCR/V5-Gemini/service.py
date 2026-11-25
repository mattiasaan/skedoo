"""Servizio HTTP dell'OCR con Gemini: stessa interfaccia del servizio della V4, il worker non cambia.

  POST /ocr?nome=<file.png>   Authorization: Bearer <OCR_TOKEN>, corpo = byte dell'immagine
                              -> lo stesso JSON che main.py scrive in <out>/<nome>.json
  GET  /health                {"status": "ok" | "starting"} (senza dati, senza token)

Avvio (nel container):  uvicorn service:build --factory --host 0.0.0.0 --port 8090

Variabili d'ambiente:
  OCR_TOKEN          obbligatorio, almeno 32 caratteri: lo stesso impostato nel backend
  GEMINI_API_KEY     obbligatoria: chiave di Google AI Studio (https://aistudio.google.com/apikey)
  GEMINI_MODELS      modelli separati da virgola, in ordine di preferenza (default: config.json)
  OCR_MAX_IMAGE_MB   dimensione massima di un'immagine (default 20)

Una lettura alla volta: il piano gratuito ha pochi messaggi al minuto, le richieste in più aspettano.
Codici di errore: 503 quota Gemini esaurita (Retry-After) o chiave in verifica, 502 errore di Gemini,
500 errore interno. Il dettaglio va solo nei log del servizio.
"""
from __future__ import annotations

import asyncio
import hmac
import logging
import os
import re
import threading
import time
import urllib.error
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from gemini_ocr.config import load_config, parse_models
from gemini_ocr.engine import GeminiEngine, GeminiError, InvalidKey, QuotaExhausted
from gemini_ocr.pipeline import processa_array

EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
MIN_TOKEN_LENGTH = 32

log = logging.getLogger("skedoo.ocr")


class InvalidImage(Exception):
    """Il corpo della richiesta non è un'immagine decodificabile (risposta 422 con messaggio fisso)."""


class Settings:
    def __init__(self, env=os.environ):
        self.token = env.get("OCR_TOKEN", "")
        if len(self.token) < MIN_TOKEN_LENGTH:
            raise SystemExit(f"OCR_TOKEN mancante o troppo corto (almeno {MIN_TOKEN_LENGTH} caratteri)")
        self.api_key = env.get("GEMINI_API_KEY", "").strip()
        if not self.api_key:
            raise SystemExit("GEMINI_API_KEY mancante: creala su https://aistudio.google.com/apikey")
        self.max_bytes = int(env.get("OCR_MAX_IMAGE_MB") or 20) * 1024 * 1024
        self.cfg = load_config()
        models = parse_models(env.get("GEMINI_MODELS", ""))
        if models:
            self.cfg["gemini"]["models"] = models
        self.cfg["salva_ritagli"] = False  # il servizio restituisce solo il JSON


class State:
    """Motore pronto (dopo la verifica della chiave) e lucchetto per una lettura alla volta."""

    def __init__(self):
        self.engine: GeminiEngine | None = None
        self.lock = asyncio.Lock()
        self.stop = threading.Event()


def make_engine(settings: Settings) -> GeminiEngine:
    return GeminiEngine.from_config(settings.cfg, settings.api_key, log=log.info)


def prepare(settings: Settings, state: State, retry_seconds: float = 30, invalid_key_seconds: float = 600) -> None:
    """Verifica chiave e modelli (senza consumare quota) e prepara il motore. Gira in un thread all'avvio."""
    engine = make_engine(settings)
    while not state.stop.is_set():
        try:
            disponibili = engine.verifica()
        except InvalidKey as exc:
            log.error("%s: controlla GEMINI_API_KEY in deploy/.env (riprovo tra %ss)", exc, invalid_key_seconds)
            state.stop.wait(invalid_key_seconds)
            continue
        except (GeminiError, urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            log.warning("Gemini non raggiungibile (%s), riprovo tra %ss", exc, retry_seconds)
            state.stop.wait(retry_seconds)
            continue
        if not disponibili:
            log.warning("Nessuno dei modelli %s risulta nell'elenco di Gemini: provo comunque",
                        engine.models)
        state.engine = engine
        log.info("OCR pronto: Gemini %s", ", ".join(disponibili or engine.models))
        return


def safe_name(name: str) -> str | None:
    """Nome del file solo per l'id delle voci (es. 15128149_1_2_NOV_16_STU_1): niente percorsi."""
    base = re.split(r"[\\/]", name or "")[-1]
    base = re.sub(r"[^A-Za-z0-9._-]", "_", base).lstrip(".")[-120:]
    path = Path(base)
    return base if path.stem and path.suffix.lower() in EXT else None


def _error(status: int, message: str, headers: dict | None = None) -> JSONResponse:
    return JSONResponse({"detail": message}, status_code=status, headers=headers)


def create_app(settings: Settings | None = None, start_engine: bool = True) -> FastAPI:
    settings = settings or Settings()
    state = State()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if start_engine:
            threading.Thread(target=prepare, args=(settings, state), daemon=True).start()
        yield
        state.stop.set()

    app = FastAPI(title="Skedoo OCR (Gemini)", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    app.state.ocr = state

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/health")
    def health():
        return {"status": "ok" if state.engine else "starting"}

    @app.post("/ocr")
    async def ocr(request: Request, nome: str = "cartellone.png"):
        auth = request.headers.get("authorization", "")
        scheme, _, token = auth.partition(" ")
        if scheme.lower() != "bearer" or not hmac.compare_digest(token.encode(), settings.token.encode()):
            return _error(401, "Token non valido", {"WWW-Authenticate": "Bearer"})
        name = safe_name(nome)
        if not name:
            return _error(422, "Nome file non valido: serve un'immagine (.png, .jpg, ...)")
        length = request.headers.get("content-length")
        if length is None or not length.isdigit():
            return _error(411, "Content-Length obbligatorio")
        if int(length) > settings.max_bytes:
            return _error(413, "Immagine troppo grande")
        body = bytearray()
        async for chunk in request.stream():
            body += chunk
            if len(body) > settings.max_bytes:
                return _error(413, "Immagine troppo grande")
        if not body:
            return _error(422, "Immagine vuota")
        if state.engine is None:
            return _error(503, "OCR in preparazione, riprova più tardi", {"Retry-After": "60"})
        async with state.lock:
            started = time.perf_counter()
            try:
                result = await asyncio.to_thread(_process, bytes(body), name, state.engine, settings.cfg)
            except InvalidImage:
                return _error(422, "Il file non è un'immagine leggibile")
            except QuotaExhausted:
                log.warning("Quota Gemini esaurita per %s", name)
                return _error(503, "Quota Gemini esaurita, riprova più tardi", {"Retry-After": "3600"})
            except GeminiError as exc:
                log.error("Gemini ha rifiutato la lettura di %s: %s", name, exc)
                return _error(502, "Lettura con Gemini fallita")
            except Exception:  # noqa: BLE001 - l'errore va nei log del servizio, mai al client
                log.exception("OCR fallito per %s", name)
                return _error(500, "Lettura dell'immagine fallita")
        log.info("%s letto in %.0fs con %s (%s voci)", name, time.perf_counter() - started,
                 result.get("motore", {}).get("modello"), result.get("n_voci"))
        return result

    return app


def _process(data: bytes, name: str, engine, cfg: dict) -> dict:
    import cv2
    import numpy as np

    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise InvalidImage
    return processa_array(img, name, engine, cfg, outdir=None, log=log.info)


def build() -> FastAPI:
    """Factory per uvicorn: `uvicorn service:build --factory`."""
    logging.basicConfig(level=os.getenv("OCR_LOG_LEVEL", "INFO").upper(),
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    return create_app()
