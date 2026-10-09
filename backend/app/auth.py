import logging

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from .classeviva import CvSession, store
from .config import get_settings
from .errors import AppError
from .security import client_ip, create_token, current_session, limiter, rate_limit, too_many

log = logging.getLogger("skedoo")
router = APIRouter(prefix="/auth", tags=["Auth"])

FAILURE_WINDOW = 15 * 60  # secondi


class LoginIn(BaseModel):
  # limiti stretti: sono input non fidato che finisce nei log e nelle richieste a ClasseViva
  username: str = Field(min_length=1, max_length=64, pattern=r"^[^\s\x00-\x1f]+$")
  password: str = Field(min_length=1, max_length=256)


class User(BaseModel):
  id: str
  nome: str
  cognome: str


class TokenOut(BaseModel):
  access_token: str
  token_type: str = "bearer"
  expires_in: int  # secondi
  utente: User


@router.post("/login", response_model=TokenOut)
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
    session = await store.login(username, body.password)
  except AppError as e:
    if e.code == "invalid_credentials":
      limiter.add(f"fail:{pair}", FAILURE_WINDOW)
      log.warning("login fallito ip=%s user=%s", ip, username)
    raise
  limiter.reset(f"fail:{pair}")
  token, expires_in = create_token(username, session.sid)
  return TokenOut(access_token=token, expires_in=expires_in, utente=User(**session.profile))


@router.get("/me", response_model=User)
def me(session: CvSession = Depends(current_session)):
  """Utente del token: utile all'avvio dell'app per sapere se è ancora loggato."""
  return User(**session.profile)


@router.post("/logout", status_code=204)
def logout(session: CvSession = Depends(current_session)):
  """Chiude la sessione di QUESTO dispositivo (gli altri restano collegati)."""
  store.logout(session.sid)
