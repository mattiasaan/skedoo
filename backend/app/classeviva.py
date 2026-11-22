"""Sessioni ClasseViva.

Classeviva.py ha metodi `async` ma usa `requests` (sincrono): chiamati direttamente bloccherebbero FastAPI.
Qui ogni chiamata gira in un thread, con un lock per sessione e una piccola cache.

Ogni login crea una sessione con un `sid` (scritto nel JWT). Le sessioni stanno solo in memoria e se il server
si riavvia spariscono: il frontend riceve 401 `session_expired` e rifà il login.

La password serve a ricollegarsi a ClasseViva quando la sua sessione scade (circa ogni ora e mezza). Il server
la tiene SOLO cifrata (AES-256-GCM): la chiave è casuale per ogni sessione e sta solo nel JWT dell'utente, non sul
server. Chi copia la memoria del server trova solo password cifrate; ognuna viene decifrata per la durata di una
singola chiamata a ClasseViva di quell'utente e poi tolta dall'oggetto `Utente`.
"""
import asyncio
import logging
import secrets
import threading
import time
from contextlib import contextmanager
from typing import NamedTuple

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

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


class Connection(NamedTuple):
  """Quanto serve per chiamare ClasseViva senza passare da Classeviva.py (vedi `CvSession.connection`)."""
  student_id: str
  headers: dict
  cookies: object  # RequestsCookieJar, copiato: chi lo usa non tocca la sessione condivisa


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
    self._sealed: bytes | None = None  # nonce + password cifrata

  # ---------- password cifrata ----------
  def _aad(self) -> bytes:
    # lega il testo cifrato a questa sessione: non si può spostare su un'altra
    return f"{self.sid}|{self.username}".encode()

  def seal(self, password: str) -> bytes:
    """Cifra la password, la toglie da `Utente` e restituisce la chiave (da mettere nel JWT, non da tenere)."""
    key = AESGCM.generate_key(bit_length=256)
    nonce = secrets.token_bytes(12)
    self._sealed = nonce + AESGCM(key).encrypt(nonce, password.encode(), self._aad())
    self.utente.password = ""
    return key

  def _unseal(self, key: bytes) -> str:
    try:
      return AESGCM(key).decrypt(self._sealed[:12], self._sealed[12:], self._aad()).decode()
    except (InvalidTag, ValueError):
      raise AppError(401, "session_expired", "Sessione scaduta, effettua di nuovo il login")

  @contextmanager
  def _unlocked(self, key: bytes | None):
    """Lock della sessione e password in chiaro su `Utente` solo per la durata del blocco
    (serve se ClasseViva chiede un nuovo login). La sessione requests non è fatta per l'uso concorrente."""
    with self._lock:
      if self._sealed is not None:
        if key is None:
          raise AppError(401, "session_expired", "Sessione scaduta, effettua di nuovo il login")
        self.utente.password = self._unseal(key)
      try:
        yield
      finally:
        if self._sealed is not None:
          self.utente.password = ""

  def _run(self, method: str, args: tuple, key: bytes | None):
    with self._unlocked(key):
      try:
        return asyncio.run(getattr(self.utente, method)(*args))
      except eccezioni.ErroreHTTP as e:
        if isinstance(e, eccezioni.ErroreHTTP404):
          raise
        self.utente.inizio = None  # sessione probabilmente scaduta su ClasseViva: nuovo login e un solo tentativo
        return asyncio.run(getattr(self.utente, method)(*args))

  def _connect(self, key: bytes | None, relogin: bool) -> Connection:
    with self._unlocked(key):
      if relogin:
        self.utente.inizio = None
      if not self.utente.connesso:
        asyncio.run(self.utente.accedi())
      http = self.utente._sessione
      return Connection(str(self.utente._id), dict(http.headers), http.cookies.copy())

  async def call(self, method: str, *args, key: bytes | None = None):
    """Chiama un metodo di Utente (es. call("voti", "26")), con cache per `cache_ttl_seconds`."""
    now = self.last_used = time.monotonic()
    ttl = get_settings().cache_ttl_seconds
    cache_key = (method, args)
    hit = self._cache.get(cache_key)
    if hit and now - hit[0] < ttl:
      return hit[1]
    try:
      result = await asyncio.to_thread(self._run, method, args, key)
    except AppError:
      raise
    except Exception as e:
      raise translate(e) from e
    # la sessione può vivere giorni: si tengono solo le risposte ancora valide (es. tanti intervalli di agenda)
    self._cache = {k: v for k, v in self._cache.items() if now - v[0] < ttl}
    self._cache[cache_key] = (time.monotonic(), result)
    return result

  async def connection(self, *, key: bytes | None = None, relogin: bool = False) -> Connection:
    """Login su ClasseViva se serve, poi id studente, header e cookie per una richiesta fatta da noi.
    Serve ai download: Classeviva.py legge ogni file intero in memoria, e tenere il lock per tutto il
    trasferimento bloccherebbe le altre chiamate dell'utente. `relogin` forza un nuovo login."""
    self.last_used = time.monotonic()
    try:
      return await asyncio.to_thread(self._connect, key, relogin)
    except AppError:
      raise
    except Exception as e:
      raise translate(e) from e

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

  async def load_school(self, key: bytes | None = None) -> None:
    """Carica la scuola dalla carta ClasseViva, senza inserirla nel JWT."""
    if self._school is not None or not hasattr(self.utente, "carta"):
      return
    try:
      raw = await self.call("carta", key=key)
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


class ActiveSession:
  """La sessione vista da UNA richiesta: unisce la sessione sul server alla chiave arrivata col JWT.
  Vive solo per la durata della richiesta, così la chiave non resta in memoria sul server."""

  def __init__(self, session: CvSession, key: bytes):
    self._session, self._key = session, key

  def __getattr__(self, name):
    return getattr(self._session, name)

  async def call(self, method: str, *args):
    return await self._session.call(method, *args, key=self._key)

  async def connection(self, *, relogin: bool = False) -> Connection:
    return await self._session.connection(key=self._key, relogin=relogin)


class SessionStore:
  def __init__(self):
    self._sessions: dict[str, CvSession] = {}
    self._lock = threading.Lock()

  async def login(self, username: str, password: str) -> tuple[CvSession, bytes]:
    """Restituisce la sessione e la chiave della password cifrata: la chiave va nel JWT e NON va conservata."""
    utente = Utente(username, password)
    try:
      await asyncio.to_thread(lambda: asyncio.run(utente.accedi()))
    except Exception as e:
      raise translate(e) from e
    # elimina le sessioni inattive da più della durata del token
    limit = get_settings().jwt_ttl_hours * 3600
    now = time.monotonic()
    session = CvSession(username, utente)
    key = session.seal(password)
    await session.load_school(key)
    with self._lock:
      self._sessions = {
        k: s for k, s in self._sessions.items() if now - s.last_used < limit
      }
      self._sessions[session.sid] = session
    return session, key

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
