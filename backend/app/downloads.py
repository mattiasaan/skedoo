"""Download dei file di ClasseViva: allegati della bacheca e file della didattica.

Il file passa dal server a pezzi da 64 KB e non sta mai tutto in memoria (Classeviva.py invece legge
`response.content`: sul Raspberry un file da 250 MB peserebbe tutto sulla RAM). La richiesta usa i cookie della
sessione ClasseViva dell'utente (`ActiveSession.connection`) ed è fatta fuori dal lock della sessione, così un
download lungo non blocca le altre chiamate dello stesso utente.

Limiti:
- `max_download_mb`: se ClasseViva dichiara un file più grande si risponde 413 prima di iniziare; se non dichiara
  la dimensione, il trasferimento si interrompe al limite (il client vede un download fallito, non un file troncato);
- `max_parallel_downloads` download contemporanei per utente (429 oltre).
"""
import asyncio
import json
import logging
import re
import threading
import time
from collections.abc import Callable
from email.message import Message
from urllib.parse import quote, urljoin, urlsplit

import requests
from fastapi.responses import JSONResponse, StreamingResponse

from .classeviva import ActiveSession, Connection
from .config import get_settings
from .errors import AppError

log = logging.getLogger("skedoo")

CHUNK = 64 * 1024
TIMEOUT = (10, 60)  # secondi: connessione, attesa massima tra un pezzo e l'altro
MAX_REDIRECTS = 3
MAX_JSON_BYTES = 256 * 1024  # le risposte JSON (link, testo, errori) sono piccole
_CONTENT_TYPE = re.compile(r"^[\w.+-]+/[\w.+-]+$")


class _Slots:
  """Download in corso per utente. Uno slot fermo da più di STALE_SECONDS si considera perso (es. il client si è
  disconnesso prima che il trasferimento iniziasse): ogni pezzo inoltrato lo rinnova con `touch`."""
  STALE_SECONDS = 120  # più del timeout di lettura verso ClasseViva

  def __init__(self):
    self._active: dict[str, dict[object, float]] = {}
    self._lock = threading.Lock()

  def take(self, user: str, limit: int) -> object:
    now = time.monotonic()
    with self._lock:
      active = {k: t for k, t in self._active.get(user, {}).items() if now - t < self.STALE_SECONDS}
      if len(active) >= limit:
        raise AppError(429, "too_many_downloads", "Hai già dei download in corso: aspetta che finiscano")
      token = object()
      active[token] = now
      self._active[user] = active
    return token

  def touch(self, user: str, token: object) -> None:
    with self._lock:
      active = self._active.get(user)
      if active is not None and token in active:
        active[token] = time.monotonic()

  def release(self, user: str, token: object) -> None:
    with self._lock:
      active = self._active.get(user, {})
      active.pop(token, None)
      if not active:
        self._active.pop(user, None)

  def clear(self) -> None:
    with self._lock:
      self._active.clear()


slots = _Slots()


def _trusted(url: str) -> bool:
  """I redirect si seguono solo in https verso ClasseViva (es. la CDN cdndoc.spaggiari.eu)."""
  parts = urlsplit(url)
  host = (parts.hostname or "").lower()
  return parts.scheme == "https" and (host == "spaggiari.eu" or host.endswith(".spaggiari.eu"))


def _open(conn: Connection, url: str) -> tuple[requests.Session, requests.Response]:
  """GET in streaming con i cookie dell'utente. Chi riceve la risposta deve chiudere risposta e sessione."""
  http = requests.Session()
  http.headers.update(conn.headers)
  http.cookies.update(conn.cookies)
  try:
    for _ in range(MAX_REDIRECTS + 1):
      response = http.get(url, stream=True, timeout=TIMEOUT, allow_redirects=False)
      if not response.is_redirect:
        return http, response
      target = urljoin(url, response.headers.get("location", ""))
      response.close()
      if not _trusted(target):
        log.warning("Download: redirect di ClasseViva verso un dominio esterno, ignorato")
        break
      url = target
  except requests.RequestException as e:
    http.close()
    log.warning("Download: ClasseViva non raggiungibile (%s)", e.__class__.__name__)
    raise AppError(502, "classeviva_error", "ClasseViva non ha risposto, riprova tra poco") from e
  http.close()
  raise AppError(502, "classeviva_error", "ClasseViva non ha restituito il file")


def _close(http: requests.Session, response: requests.Response) -> None:
  response.close()
  http.close()


def _read_small(response: requests.Response) -> bytes | None:
  """Il corpo intero se sta in MAX_JSON_BYTES, altrimenti None."""
  data = bytearray()
  for chunk in response.iter_content(CHUNK):
    data += chunk
    if len(data) > MAX_JSON_BYTES:
      return None
  return bytes(data)


def safe_filename(name: str | None) -> str | None:
  """Nome del file senza percorsi né caratteri di controllo, al massimo 180 caratteri."""
  if not name:
    return None
  name = re.sub(r"[\x00-\x1f\x7f/\\]", "", name).strip().strip(".")
  return name[:180] or None


def _upstream_filename(response: requests.Response) -> str | None:
  header = response.headers.get("content-disposition")
  if not header:
    return None
  message = Message()
  message["content-disposition"] = header
  return safe_filename(message.get_filename())  # gestisce anche filename*=UTF-8''...


def content_disposition(filename: str | None) -> str:
  if not filename:
    return "attachment"
  ascii_name = filename.encode("ascii", "ignore").decode().replace('"', "") or "file"
  return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(filename, safe='')}"


async def stream_file(
  session: ActiveSession,
  build_url: Callable[[str], str],
  *,
  on_json: Callable[[object], dict | None] | None = None,
) -> StreamingResponse | JSONResponse:
  """Scarica da ClasseViva l'URL `build_url(id_studente)` e lo inoltra al client in streaming.

  Se ClasseViva risponde con un JSON invece che con un file, `on_json` può trasformarlo in una risposta per il
  frontend (es. il link di un materiale); se non c'è o restituisce None, il contenuto non è scaricabile."""
  settings = get_settings()
  limit = settings.max_download_mb * 1024 * 1024
  user = session.username.lower()
  token = slots.take(user, settings.max_parallel_downloads)
  http = response = None
  try:
    conn = await session.connection()
    http, response = await asyncio.to_thread(_open, conn, build_url(conn.student_id))
    if response.status_code in (401, 403):  # sessione ClasseViva scaduta: nuovo login e un solo altro tentativo
      _close(http, response)
      conn = await session.connection(relogin=True)
      http, response = await asyncio.to_thread(_open, conn, build_url(conn.student_id))

    if response.status_code == 404:
      raise AppError(404, "file_not_found", "File non trovato su ClasseViva")
    if response.status_code != 200:
      log.warning("Download: ClasseViva ha risposto HTTP %s", response.status_code)
      raise AppError(502, "classeviva_error", "ClasseViva non ha restituito il file, riprova tra poco")

    content_type = (response.headers.get("content-type") or "").split(";")[0].strip().lower()
    if content_type == "application/json":
      raw = await asyncio.to_thread(_read_small, response)
      try:
        data = json.loads(raw) if raw is not None else None
      except ValueError:
        data = None
      result = on_json(data) if on_json and data is not None else None
      if result is None:
        raise AppError(502, "not_downloadable", "ClasseViva non fornisce questo contenuto come file: aprilo dall'app o dal sito ClasseViva")
      _close(http, response)
      slots.release(user, token)
      return JSONResponse(result)

    # con Content-Encoding (gzip...) la lunghezza dichiarata è quella compressa: non si può inoltrare
    declared = response.headers.get("content-length", "")
    length = int(declared) if declared.isdigit() and not response.headers.get("content-encoding") else None
    if length is not None and length > limit:
      raise AppError(413, "file_too_large", f"Il file supera il limite di {settings.max_download_mb} MB: scaricalo dall'app o dal sito ClasseViva")
  except BaseException:
    if response is not None:
      _close(http, response)
    slots.release(user, token)
    raise

  async def body():
    chunks = response.iter_content(CHUNK)
    sent = 0
    try:
      while True:
        chunk = await asyncio.to_thread(next, chunks, None)
        if chunk is None:
          return
        sent += len(chunk)
        if sent > limit:
          # un'eccezione (e non un semplice return) chiude la connessione senza terminare la risposta:
          # il client vede un download fallito invece di un file troncato che sembra completo
          raise RuntimeError(f"Download interrotto: oltre il limite di {settings.max_download_mb} MB")
        slots.touch(user, token)
        yield chunk
    finally:
      _close(http, response)
      slots.release(user, token)

  headers = {"Content-Disposition": content_disposition(_upstream_filename(response))}
  if length is not None:
    headers["Content-Length"] = str(length)
  media_type = content_type if _CONTENT_TYPE.match(content_type) else "application/octet-stream"
  return StreamingResponse(body(), media_type=media_type, headers=headers)
