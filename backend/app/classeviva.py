"""Sessioni ClasseViva.

Classeviva.py ha metodi `async` ma usa `requests` (sincrono): chiamati direttamente bloccherebbero FastAPI.
Qui ogni chiamata gira in un thread, con un lock per sessione e una piccola cache.

Ogni login crea una sessione con un `sid` (scritto nel JWT). Le sessioni stanno solo in memoria: la password
serve a ricollegarsi a ClasseViva quando la sua sessione scade, e non viene mai scritta su disco né nel JWT.
Se il server si riavvia le sessioni spariscono e il frontend riceve 401 `session_expired`: rifà il login.
"""
import asyncio
import logging
import secrets
import threading
import time

from classeviva import Utente, eccezioni

from .config import get_settings
from .errors import AppError

log = logging.getLogger("skedoo")


def translate(exc: Exception) -> AppError:
  """Da eccezione di Classeviva.py a errore per il frontend."""
  if isinstance(exc, eccezioni.PasswordNonValida):
    return AppError(401, "invalid_credentials", "Username o password ClasseViva non validi")
  if isinstance(exc, (eccezioni.FormatoNonValido, eccezioni.ParametroNonValido)):
    return AppError(422, "invalid_parameter", "Parametro non valido (formato data: YYYY-MM-DD)")
  if isinstance(exc, eccezioni.DataFuoriGamma):
    return AppError(422, "date_out_of_range", "Data fuori dall'anno scolastico corrente")
  log.error("Errore ClasseViva: %s", exc.__class__.__name__)
  return AppError(502, "classeviva_error", "ClasseViva non ha risposto correttamente, riprova tra poco")


class CvSession:
  def __init__(self, username: str, utente: Utente):
    self.sid = secrets.token_urlsafe(18)
    self.username = username
    self.utente = utente
    self.last_used = time.monotonic()
    self._lock = threading.Lock()
    self._cache: dict[tuple, tuple[float, object]] = {}
    self._school: dict | None = None
    self._card_profile: dict = {}

  def _run(self, method: str, args: tuple):
    with self._lock:  # la sessione requests non è fatta per l'uso concorrente
      try:
        return asyncio.run(getattr(self.utente, method)(*args))
      except eccezioni.ErroreHTTP as e:
        if isinstance(e, eccezioni.ErroreHTTP404):
          raise
        self.utente.inizio = None  # sessione probabilmente scaduta su ClasseViva: nuovo login e un solo tentativo
        return asyncio.run(getattr(self.utente, method)(*args))

  async def call(self, method: str, *args):
    """Chiama un metodo di Utente (es. call("voti", "26")), con cache per `cache_ttl_seconds`."""
    self.last_used = time.monotonic()
    key = (method, args)
    hit = self._cache.get(key)
    if hit and time.monotonic() - hit[0] < get_settings().cache_ttl_seconds:
      return hit[1]
    try:
      result = await asyncio.to_thread(self._run, method, args)
    except Exception as e:
      raise translate(e) from e
    self._cache[key] = (time.monotonic(), result)
    return result

  @property
  def profile(self) -> dict:
    d = getattr(self.utente, "dati", None)
    if not isinstance(d, dict):
      d = getattr(self.utente, "_dati", None) or {}
    return {
      "id": self.username,
      "nome": d.get("firstName") or self._card_profile.get("firstName", ""),
      "cognome": d.get("lastName") or self._card_profile.get("lastName", ""),
      "scuola": self._school,
    }

  async def load_school(self) -> None:
    """Carica la scuola dalla carta ClasseViva, senza inserirla nel JWT."""
    if self._school is not None or not hasattr(self.utente, "carta"):
      return
    try:
      raw = await self.call("carta")
    except (AppError, eccezioni.ErroreHTTP, eccezioni.SenzaDati) as exc:
      log.warning("Scuola ClasseViva non disponibile: %s", exc.__class__.__name__)
      return
    card = raw.get("card", raw) if isinstance(raw, dict) else {}
    if not isinstance(card, dict):
      return
    self._card_profile = {
      "firstName": card.get("firstName") or "",
      "lastName": card.get("lastName") or "",
    }
    self._school = {
      "codice": card.get("schCode") or card.get("miurSchoolCode"),
      "nome": card.get("schName"),
      "dedica": card.get("schDedication"),
      "citta": card.get("schCity"),
      "provincia": card.get("schProv"),
    }


class SessionStore:
  def __init__(self):
    self._sessions: dict[str, CvSession] = {}
    self._lock = threading.Lock()

  async def login(self, username: str, password: str) -> CvSession:
    utente = Utente(username, password)
    try:
      await asyncio.to_thread(lambda: asyncio.run(utente.accedi()))
    except Exception as e:
      raise translate(e) from e
    # elimina le sessioni inattive da più della durata del token
    limit = get_settings().jwt_ttl_hours * 3600
    now = time.monotonic()
    session = CvSession(username, utente)
    await session.load_school()
    with self._lock:
      self._sessions = {
        k: s for k, s in self._sessions.items() if now - s.last_used < limit
      }
      self._sessions[session.sid] = session
    return session

  def get(self, sid: str, username: str) -> CvSession:
    with self._lock:
      s = self._sessions.get(sid)
    if s is None or s.username != username:
      raise AppError(401, "session_expired", "Sessione scaduta, effettua di nuovo il login")
    return s

  def logout(self, sid: str) -> None:
    with self._lock:
      self._sessions.pop(sid, None)


store = SessionStore()
