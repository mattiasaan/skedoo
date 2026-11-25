import logging
import re
import unicodedata

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field, field_validator

from .classeviva import ActiveSession, pseudonym, store
from .config import get_settings
from .errors import AppError
from .security import client_ip, create_token, current_session, limiter, rate_limit, too_many

log = logging.getLogger("skedoo")
router = APIRouter(prefix="/auth", tags=["Auth"])

FAILURE_WINDOW = 15 * 60  # secondi


USERNAME = re.compile(r"[\x21-\x7e]{1,64}")  # ASCII stampabile, senza spazi


class LoginIn(BaseModel):
  # limiti stretti: sono input non fidato che finisce nei log e nelle richieste a ClasseViva
  username: str = Field(min_length=1, max_length=64)
  password: str = Field(min_length=1, max_length=256)

  @field_validator("username")
  @classmethod
  def _one_form_per_username(cls, value: str) -> str:
    """Un solo modo di scrivere ogni username. NFKC riporta ad ASCII le varianti "di compatibilità" (es. "Ｓ123X" a
    tutta larghezza diventa "S123X") e il resto fuori da ASCII si rifiuta: altrimenti "Ŝ123X", "S123X" + spazio a
    larghezza zero ecc. avrebbero ognuna i propri contatori di tentativi e di blocco, aggirabili se ClasseViva le
    considera lo stesso account. Gli username ClasseViva sono codici (S1234567X) o indirizzi email."""
    value = unicodedata.normalize("NFKC", value).strip()
    if not USERNAME.fullmatch(value):
      raise ValueError("username non valido")
    return value


class School(BaseModel):
  codice: str | None = None
  nome: str | None = None
  dedica: str | None = None
  citta: str | None = None
  provincia: str | None = None


class User(BaseModel):
  id: str
  nome: str
  cognome: str
  tipo: str | None = None  # studente | genitore (dal codice ClasseViva), None se non riconoscibile
  scuola: School | None = None


class TokenOut(BaseModel):
  access_token: str
  token_type: str = "bearer"
  expires_in: int  # secondi
  utente: User


@router.post("/login", response_model=TokenOut, response_model_exclude_none=True)
async def login(body: LoginIn, request: Request):
  """Login con le credenziali ClasseViva: l'UNICO endpoint senza JWT, quindi ha limiti suoi:
  tentativi per IP, tentativi per (IP, username) e blocco dopo troppe password sbagliate."""
  s = get_settings()
  ip, username = client_ip(request), body.username.strip()
  pair = f"{ip}|{username.lower()}"
  rate_limit(f"login-ip:{ip}", s.login_attempts * 6, code="too_many_attempts")  # per IP: 6x il limite per utente
  rate_limit(f"login:{pair}", s.login_attempts, code="too_many_attempts")
  if limiter.count(f"fail:{pair}", FAILURE_WINDOW) >= s.login_failures:  # bloccato anche con la password giusta
    raise too_many(FAILURE_WINDOW, "too_many_attempts")
  try:
    session, key = await store.login(username, body.password)
  except AppError as e:
    if e.code == "invalid_credentials":
      limiter.add(f"fail:{pair}", FAILURE_WINDOW)
      log.warning("login fallito ip=%s user=%s", ip, pseudonym(username))  # mai il codice personale nei log
    raise
  limiter.reset(f"fail:{pair}")
  token, expires_in = create_token(username, session.sid, key)
  return TokenOut(access_token=token, expires_in=expires_in, utente=User(**session.profile))


@router.get("/me", response_model=User, response_model_exclude_none=True)
def me(session: ActiveSession = Depends(current_session)):
  """Utente del token: utile all'avvio dell'app per sapere se è ancora loggato."""
  return User(**session.profile)


class RefreshOut(BaseModel):
  access_token: str
  token_type: str = "bearer"
  expires_in: int  # secondi


@router.post("/refresh", response_model=RefreshOut)
def refresh(session: ActiveSession = Depends(current_session)):
  """Nuovo token per la STESSA sessione (stessi `sid` e chiave), senza password: chi usa l'app non resta mai
  senza token. Il vecchio token resta valido fino alla sua scadenza. Dopo `session_max_days` dal login
  risponde 401 `session_expired`."""
  token, expires_in = create_token(session.username, session.sid, session.key, session.auth_time)
  return RefreshOut(access_token=token, expires_in=expires_in)


@router.post("/logout", status_code=204)
def logout(session: ActiveSession = Depends(current_session)):
  """Chiude la sessione di QUESTO dispositivo (gli altri restano collegati)."""
  store.logout(session.sid)
