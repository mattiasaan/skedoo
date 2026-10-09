import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.middleware.trustedhost import TrustedHostMiddleware

from . import agenda, auth, grades, schedules
from .config import get_settings
from .db import get_engine
from .errors import AppError, error_response, register_error_handlers
from .security import client_ip, rate_limit

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
settings = get_settings()

MAX_BODY_BYTES = 16 * 1024  # le richieste sono piccole (il login pesa poche decine di byte)
SECURITY_HEADERS = {
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
  "Referrer-Policy": "no-referrer",
  "Cache-Control": "no-store",  # dati personali: mai in cache condivise (gli endpoint possono sovrascrivere)
}


@asynccontextmanager
async def lifespan(_: FastAPI):
  if settings.schedule_source == "db":  # se il database non risponde meglio fallire subito che a ogni richiesta
    with Session(get_engine()) as db:
      db.execute(select(1))
  yield


app = FastAPI(
  title="Skedoo API", version="0.3.0", lifespan=lifespan,
  docs_url=None if settings.is_production else "/docs",  # in produzione la documentazione è spenta
  redoc_url=None, openapi_url=None if settings.is_production else "/openapi.json",
)


@app.middleware("http")
async def protect(request: Request, call_next):
  """Per ogni richiesta: rate limit per IP, limite alla dimensione del body, header di sicurezza."""
  try:
    rate_limit(f"ip:{client_ip(request)}", settings.rate_limit_ip)
    length = request.headers.get("content-length")
    if "transfer-encoding" in request.headers or (length and (not length.isdigit() or int(length) > MAX_BODY_BYTES)):
      raise AppError(413, "payload_too_large", "Richiesta troppo grande")
  except AppError as e:
    response = error_response(e.status, e.code, e.message, e.headers)
  else:
    response = await call_next(request)
  for name, value in SECURITY_HEADERS.items():
    response.headers.setdefault(name, value)
  if settings.is_production:
    response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
  return response


# L'ultimo middleware aggiunto è il più esterno: CORS avvolge tutto, così anche gli errori 413/429 hanno gli header CORS
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.hosts)
app.add_middleware(
  CORSMiddleware, allow_origins=settings.origins, allow_methods=["GET", "POST"],
  allow_headers=["Authorization", "Content-Type"], expose_headers=["Retry-After"],
)
register_error_handlers(app)

for module in (auth, schedules, grades, agenda):
  app.include_router(module.router)


@app.get("/health", tags=["Health"])
def health():
  """Controllo di vita per Docker/hosting (non può portare un JWT). Non espone dati."""
  return {"status": "ok"}
