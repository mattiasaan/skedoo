"""Sicurezza: JWT, rate limit, e la dipendenza `current_session` che protegge gli endpoint."""
import base64
import binascii
import math
import threading
import time
from collections import deque
from typing import NamedTuple
from datetime import datetime, timedelta, timezone

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

from .classeviva import ActiveSession, store
from .config import get_settings
from .errors import AppError

ALGORITHM = "HS256"
ISSUER = AUDIENCE = "skedoo"


# ---------- JWT ----------
class TokenData(NamedTuple):
  username: str
  sid: str
  key: bytes
  auth_time: int  # istante del login (epoch, secondi): resta lo stesso a ogni rinnovo


def create_token(username: str, sid: str, key: bytes, auth_time: int | None = None) -> tuple[str, int]:
  """Il token contiene username, id di sessione e la chiave che decifra la password sul server, MAI la password.
  `sid` lo lega a una sessione sul server: logout o riavvio lo invalidano anche se non è ancora scaduto.
  `k` da sola non serve a nulla: la password cifrata esiste solo nella memoria del server.
  `auth` è l'istante del login: i rinnovi (POST /auth/refresh) non vanno oltre `session_max_days` da lì."""
  s = get_settings()
  now = datetime.now(timezone.utc)
  auth = datetime.fromtimestamp(auth_time, timezone.utc) if auth_time is not None else now
  exp = min(now + timedelta(hours=s.jwt_ttl_hours), auth + timedelta(days=s.session_max_days))
  if exp <= now:
    raise AppError(401, "session_expired", "Sessione scaduta, effettua di nuovo il login")
  k = base64.urlsafe_b64encode(key).rstrip(b"=").decode()
  claims = {"sub": username, "sid": sid, "k": k, "auth": int(auth.timestamp()),
            "iss": ISSUER, "aud": AUDIENCE, "iat": now, "exp": exp}
  return jwt.encode(claims, s.jwt_secret, algorithm=ALGORITHM), int((exp - now).total_seconds())


def decode_token(token: str) -> TokenData:
  """L'algoritmo è fissato (niente `alg: none`) e tutti i claim sono obbligatori (tranne `auth`: i token emessi
  prima dei rinnovi non ce l'hanno e valgono dal loro `iat`)."""
  try:
    claims = jwt.decode(
      token, get_settings().jwt_secret, algorithms=[ALGORITHM], audience=AUDIENCE, issuer=ISSUER,
      options={"require": ["exp", "iat", "sub", "iss", "aud"]},
    )
  except jwt.PyJWTError:
    raise AppError(401, "invalid_token", "Token non valido o scaduto")
  sub, sid, k = claims.get("sub"), claims.get("sid"), claims.get("k")
  if not all(isinstance(v, str) and v for v in (sub, sid, k)):
    raise AppError(401, "invalid_token", "Token non valido")
  auth = claims.get("auth", claims.get("iat"))
  if not isinstance(auth, int) or isinstance(auth, bool):
    raise AppError(401, "invalid_token", "Token non valido")
  try:
    key = base64.urlsafe_b64decode(k + "=" * (-len(k) % 4))
  except (binascii.Error, ValueError):
    raise AppError(401, "invalid_token", "Token non valido")
  if len(key) != 32:
    raise AppError(401, "invalid_token", "Token non valido")
  return TokenData(sub, sid, key, auth)


# ---------- rate limit (in memoria, un solo processo) ----------
class RateLimiter:
  """Finestra scorrevole: per ogni chiave tiene gli istanti delle ultime richieste."""

  def __init__(self):
    self._hits: dict[str, deque] = {}
    self._lock = threading.Lock()

  def _recent(self, key: str, window: float) -> deque:
    q = self._hits.setdefault(key, deque())
    now = time.monotonic()
    while q and now - q[0] >= window:
      q.popleft()
    if len(self._hits) > 20000:  # pulizia delle chiavi vecchie, perché la memoria non cresca all'infinito
      self._hits = {k: v for k, v in self._hits.items() if v and now - v[-1] < 3600}
    return q

  def hit(self, key: str, limit: int, window: float = 60) -> float | None:
    """Registra una richiesta. Se si supera il limite non la registra e restituisce i secondi da attendere."""
    with self._lock:
      q = self._recent(key, window)
      if len(q) >= limit:
        return window - (time.monotonic() - q[0]) if q else window
      q.append(time.monotonic())
    return None

  def add(self, key: str, window: float) -> None:
    with self._lock:
      self._recent(key, window).append(time.monotonic())

  def count(self, key: str, window: float) -> int:
    with self._lock:
      return len(self._recent(key, window))

  def reset(self, key: str) -> None:
    with self._lock:
      self._hits.pop(key, None)

  def clear(self) -> None:
    with self._lock:
      self._hits.clear()


limiter = RateLimiter()


def too_many(wait: float, code: str = "rate_limited") -> AppError:
  return AppError(429, code, "Troppe richieste, riprova tra poco", {"Retry-After": str(max(1, math.ceil(wait)))})


def rate_limit(key: str, limit: int, window: float = 60, code: str = "rate_limited") -> None:
  """Solleva 429 (con Retry-After) se `key` ha superato `limit` richieste nella finestra."""
  wait = limiter.hit(key, limit, window)
  if wait is not None:
    raise too_many(wait, code)


def client_ip(request: Request) -> str:
  """IP del client. X-Forwarded-For si legge solo con TRUST_PROXY_HEADERS=true (dietro a un proxy fidato),
  altrimenti chiunque potrebbe falsificarlo per aggirare i limiti."""
  if get_settings().trust_proxy_headers:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
      return forwarded.split(",")[-1].strip()[:64]  # l'ultima voce l'ha aggiunta il proxy, le altre le scrive il client
  return request.client.host if request.client else "-"


# ---------- dipendenze degli endpoint ----------
_bearer = HTTPBearer(auto_error=False)


def current_session(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> ActiveSession:
  """Richiede un JWT valido legato a una sessione viva e applica il limite per utente.
  Va su OGNI endpoint tranne il login."""
  if creds is None:
    raise AppError(401, "not_authenticated", "Autenticazione richiesta")
  token = decode_token(creds.credentials)
  session = store.get(token.sid, token.username)
  rate_limit(f"user:{token.username.lower()}", get_settings().rate_limit_user)
  return ActiveSession(session, token.key, token.auth_time)


def upstream_limit(session: ActiveSession = Depends(current_session)) -> None:
  """Limite più stretto per gli endpoint che chiamano ClasseViva (voti, agenda)."""
  rate_limit(f"upstream:{session.username.lower()}", get_settings().rate_limit_upstream)
