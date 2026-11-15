"""Servizio HTTP dell'OCR, usato dal backend (worker della bacheca) al posto di lanciare main.py.

  POST /ocr?nome=<file.png>   Authorization: Bearer <OCR_TOKEN>, corpo = byte dell'immagine
                              -> lo stesso JSON che main.py scrive in <out>/<nome>.json
  GET  /health                {"status": "ok" | "starting"} (senza dati, senza token)

Avvio (nel container):  uvicorn service:build --factory --host 0.0.0.0 --port 8090

Variabili d'ambiente:
  OCR_TOKEN          obbligatorio, almeno 32 caratteri: lo stesso impostato nel backend
  OLLAMA_HOST        default http://ollama:11434
  OCR_MODEL          default: quello di config.json
  OCR_MAX_IMAGE_MB   dimensione massima di un'immagine (default 20)
  OCR_PULL_MODEL     true (default): scarica il modello in Ollama se manca

Una sola lettura alla volta: sul Raspberry il modello usa tutta la CPU, le richieste in più aspettano.
"""
from __future__ import annotations

import asyncio
import hmac
import json
import logging
import os
import re
import tempfile
import threading
import time
import urllib.error
import urllib.request
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from orario.config import load_config
from orario.engines import EngineUnavailable, OllamaVLM
from orario.pipeline import processa_immagine

EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
MIN_TOKEN_LENGTH = 32

log = logging.getLogger("skedoo.ocr")


class Settings:
    def __init__(self, env=os.environ):
        self.token = env.get("OCR_TOKEN", "")
        if len(self.token) < MIN_TOKEN_LENGTH:
            raise SystemExit(f"OCR_TOKEN mancante o troppo corto (almeno {MIN_TOKEN_LENGTH} caratteri)")
        self.max_bytes = int(env.get("OCR_MAX_IMAGE_MB") or 20) * 1024 * 1024
        self.pull_model = (env.get("OCR_PULL_MODEL") or "true").lower() not in {"0", "false", "no"}
        self.cfg = load_config()
        self.cfg["ollama"]["host"] = (env.get("OLLAMA_HOST") or "http://ollama:11434").rstrip("/")
        if env.get("OCR_MODEL"):
            self.cfg["ollama"]["model"] = env["OCR_MODEL"]
        self.cfg["salva_ritagli"] = False  # il servizio restituisce solo il JSON


class State:
    """Motore pronto (dopo l'eventuale download del modello) e lucchetto per una lettura alla volta."""

    def __init__(self):
        self.engine: OllamaVLM | None = None
        self.lock = asyncio.Lock()
        self.stop = threading.Event()


def _ollama(host: str, path: str, payload: dict | None = None, timeout: float = 10) -> dict:
    request = urllib.request.Request(
        host + path, data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - host dalla configurazione
        return json.loads(response.read().decode())


def make_engine(cfg: dict) -> OllamaVLM:
    oc = cfg["ollama"]
    scale = oc.get("scale", 3)
    return OllamaVLM(oc["host"], oc["model"], scale=scale[0] if isinstance(scale, list) else scale,
                     num_ctx=oc.get("num_ctx", 4096), timeout_s=oc.get("timeout_s", 900),
                     keep_alive=oc.get("keep_alive", "10m"), think=oc.get("think"))


def prepare(settings: Settings, state: State, retry_seconds: float = 30) -> None:
    """Aspetta Ollama, scarica il modello se manca e prepara il motore. Gira in un thread all'avvio."""
    host, model = settings.cfg["ollama"]["host"], settings.cfg["ollama"]["model"]
    while not state.stop.is_set():
        try:
            state.engine = make_engine(settings.cfg)
            log.info("OCR pronto: %s su %s", model, host)
            return
        except EngineUnavailable as exc:
            log.warning("%s", exc)
        if settings.pull_model:
            try:
                _ollama(host, "/api/tags", timeout=5)  # Ollama risponde: allora manca solo il modello
                log.info("Scarico il modello %s (può richiedere parecchi minuti)...", model)
                _ollama(host, "/api/pull", {"model": model, "stream": False}, timeout=4 * 3600)
                continue
            except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
                log.warning("Ollama non pronto (%s), riprovo tra %ss", exc, retry_seconds)
        state.stop.wait(retry_seconds)


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

    app = FastAPI(title="Skedoo OCR", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
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
            return _error(503, "Modello OCR in preparazione, riprova più tardi", {"Retry-After": "60"})
        async with state.lock:
            started = time.perf_counter()
            try:
                result = await asyncio.to_thread(_process, bytes(body), name, state.engine, settings.cfg)
            except ValueError as exc:
                return _error(422, str(exc))
            except Exception:  # noqa: BLE001 - l'errore va nei log del servizio, non al client
                log.exception("OCR fallito per %s", name)
                return _error(500, "Lettura dell'immagine fallita")
        log.info("%s letto in %.0fs (%s voci)", name, time.perf_counter() - started, result.get("n_voci"))
        return result

    return app


def _process(data: bytes, name: str, engine, cfg: dict) -> dict:
    import cv2
    import numpy as np

    if cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR) is None:
        raise ValueError("Il file non è un'immagine leggibile")
    with tempfile.TemporaryDirectory(prefix="ocr-") as workdir:
        path = Path(workdir) / name
        path.write_bytes(data)
        return processa_immagine(path, engine, cfg, outdir=None, log=log.info)


def build() -> FastAPI:
    """Factory per uvicorn: `uvicorn service:build --factory`."""
    logging.basicConfig(level=os.getenv("OCR_LOG_LEVEL", "INFO").upper(),
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    return create_app()
