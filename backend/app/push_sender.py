"""Invio automatico delle notifiche push quando compaiono variazioni nuove.

Un task dell'API (avviato nel lifespan di main.py) ogni PUSH_CHECK_SECONDS:
  1. legge le variazioni dal file del worker (data/dati-bacheca/data.json, lo stesso di /changes);
  2. per ogni classe con dispositivi iscritti cerca quelle di oggi e dei giorni futuri non ancora notificate;
  3. per ogni giorno con novità manda UNA notifica con tutte le variazioni di quel giorno (con lo stesso `tag`
     sostituisce quella precedente: sul telefono resta sempre l'elenco aggiornato);
  4. le segna in `push_sent`, così dopo un riavvio o un file riscritto dall'OCR non ripartono.
Di notte (PUSH_QUIET_START - PUSH_QUIET_END) non parte niente: le novità aspettano la fine del silenzio.
I dispositivi che il servizio push dà per scomparsi (404/410) vengono cancellati.
"""
import asyncio
import hashlib
import json
import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, time, timedelta, timezone
from typing import Callable
from zoneinfo import ZoneInfo

from py_vapid import Vapid
from pywebpush import WebPushException, webpush
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from . import db as appdb
from .changes import ChangeOut, build_changes
from .config import get_settings
from .errors import AppError

log = logging.getLogger("skedoo.push")

TTL_SECONDS = 12 * 3600  # un telefono spento la riceve se si riaccende entro 12 ore, poi non serve più
SEND_TIMEOUT = 10
PARALLEL_SENDS = 8
WEEKDAYS = ("lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica")
GONE = (404, 410)  # iscrizione scaduta o revocata dall'utente: non tornerà più valida


# ---------- contenuto ----------
def change_key(change: ChangeOut) -> str:
  """Id + contenuto: se l'OCR corregge una variazione (altra aula, altro orario) la si notifica di nuovo."""
  raw = json.dumps([change.id, change.tipo, change.testo, change.nuova_aula, change.orario], ensure_ascii=False)
  return hashlib.sha256(raw.encode()).hexdigest()


def day_label(day: date, today: date) -> str:
  if day == today:
    return "oggi"
  if day == today + timedelta(days=1):
    return "domani"
  return f"{WEEKDAYS[day.weekday()]} {day.day}/{day.month}"


def hours_label(hours: list[int]) -> str:
  if not hours:
    return ""
  if len(hours) == 1:
    return f"{hours[0]}ª ora"
  return f"{hours[0]}ª-{hours[-1]}ª ora"


def change_line(change: ChangeOut) -> str:
  if change.tipo == "cambio_aula" and change.ore:
    return f"{change.testo} ({hours_label(change.ore)})"
  return change.testo


def build_message(class_id: str, day: date, changes: list[ChangeOut], today: date) -> dict:
  """Payload letto dal service worker del frontend (frontend/public/sw.js)."""
  return {
    "title": f"Variazioni {class_id} {day_label(day, today)}",
    "body": "\n".join(change_line(change) for change in changes),
    "tag": f"variazioni-{class_id}-{day.isoformat()}",
    "url": "./#home",
  }


def in_quiet_hours(moment: time, start: str, end: str) -> bool:
  begin, finish = time.fromisoformat(start), time.fromisoformat(end)
  if begin == finish:
    return False
  if begin < finish:  # es. 13:00-15:00
    return begin <= moment < finish
  return moment >= begin or moment < finish  # a cavallo della mezzanotte (22:00-06:30)


# ---------- variazioni da notificare ----------
def upcoming_changes(class_id: str, today: date) -> dict[str, list[ChangeOut]]:
  """Variazioni della classe da oggi in poi, per giorno ("YYYY-MM-DD"). Vuoto se il file non c'è ancora."""
  try:
    changes = build_changes(class_id)
  except AppError:
    return {}
  by_day: dict[str, list[ChangeOut]] = defaultdict(list)
  for change in changes:
    if change.data >= today.isoformat():
      by_day[change.data].append(change)
  return dict(by_day)


def sent_keys(db: Session, class_id: str) -> set[str]:
  return set(db.scalars(select(appdb.PushSent.change_key).where(appdb.PushSent.class_id == class_id)))


def mark_sent(db: Session, class_id: str, changes: list[ChangeOut], now: datetime, already: set[str]) -> None:
  for change in changes:
    key = change_key(change)
    if key not in already:
      db.add(appdb.PushSent(class_id=class_id, change_key=key, data=change.data, sent_at=now))
      already.add(key)


def mark_current_as_sent(db: Session, class_id: str, today: date) -> None:
  """Primo dispositivo di una classe: le variazioni già pubblicate le vede nell'app, si notificano solo le prossime."""
  already = sent_keys(db, class_id)
  now = datetime.now(timezone.utc)
  for changes in upcoming_changes(class_id, today).values():
    mark_sent(db, class_id, changes, now, already)


# ---------- invio ----------
Sender = Callable[..., object]


def _deliver(send: Sender, vapid: Vapid, subject: str, endpoint: str, p256dh: str, auth: str, data: str) -> int | None:
  """Codice HTTP dell'errore (None = consegnata al servizio push). Mai eccezioni: un dispositivo non blocca gli altri."""
  try:
    send(
      subscription_info={"endpoint": endpoint, "keys": {"p256dh": p256dh, "auth": auth}}, data=data,
      vapid_private_key=vapid, vapid_claims={"sub": subject},  # dizionario nuovo ogni volta: webpush lo modifica
      ttl=TTL_SECONDS, timeout=SEND_TIMEOUT, headers={"Urgency": "high"},
    )
    return None
  except WebPushException as exc:
    return exc.response.status_code if exc.response is not None else 0
  except Exception as exc:  # rete, timeout, chiavi del browser non valide
    log.warning("invio push non riuscito: %s", exc.__class__.__name__)
    return 0


def send_to_class(db: Session, class_id: str, message: dict, send: Sender, vapid: Vapid, now: datetime) -> int:
  subs = list(db.scalars(select(appdb.PushSubscription).where(appdb.PushSubscription.class_id == class_id)))
  data = json.dumps(message, ensure_ascii=False)
  subject = get_settings().vapid_subject
  with ThreadPoolExecutor(PARALLEL_SENDS) as pool:
    results = list(pool.map(lambda s: _deliver(send, vapid, subject, s.endpoint, s.p256dh, s.auth, data), subs))
  delivered = 0
  for sub, status in zip(subs, results):
    if status is None:
      sub.last_sent_at = now
      delivered += 1
    elif status in GONE:
      db.delete(sub)
    elif status:
      log.warning("servizio push ha risposto %s", status)
  return delivered


def run_once(now: datetime | None = None, send: Sender = webpush) -> int:
  """Un giro di controllo. Restituisce quante notifiche sono state consegnate ai servizi push."""
  s = get_settings()
  now = now or datetime.now(timezone.utc)
  local = now.astimezone(ZoneInfo(s.timezone))
  if in_quiet_hours(local.time(), s.push_quiet_start, s.push_quiet_end):
    return 0
  today = local.date()
  vapid = Vapid.from_string(private_key=s.vapid_private_key)
  delivered = 0
  with Session(appdb.get_engine()) as db:
    db.execute(delete(appdb.PushSent).where(appdb.PushSent.data < today.isoformat()))  # giorni passati
    db.commit()
    class_ids = list(db.scalars(select(appdb.PushSubscription.class_id).distinct()))
    for class_id in class_ids:
      already = sent_keys(db, class_id)
      for day, changes in sorted(upcoming_changes(class_id, today).items()):
        if all(change_key(change) in already for change in changes):
          continue
        message = build_message(class_id, date.fromisoformat(day), changes, today)
        delivered += send_to_class(db, class_id, message, send, vapid, now)
        mark_sent(db, class_id, changes, now, already)
        db.commit()  # classe per classe: un errore a metà non fa rimandare quelle già notificate
  if delivered:
    log.info("notifiche push consegnate: %d", delivered)
  return delivered


async def run_forever() -> None:
  interval = get_settings().push_check_seconds
  log.info("notifiche push attive: controllo ogni %ds", interval)
  while True:
    try:
      await asyncio.to_thread(run_once)
    except Exception:  # database giù, file illeggibile...: si riprova al giro dopo
      log.exception("controllo delle notifiche push non riuscito")
    await asyncio.sleep(interval)
