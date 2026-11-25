"""Notifiche push (Web Push con VAPID): iscrizione e disiscrizione dei dispositivi.

Il browser crea l'iscrizione con la chiave pubblica (GET /push/public-key) e la manda qui insieme alla classe.
L'invio delle variazioni nuove lo fa app/push_sender.py. Endpoint attivi solo con le notifiche configurate
(VAPID_* e DATABASE_URL), altrimenti 503 `push_disabled`.
"""
from datetime import datetime, timezone
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import db as appdb
from .changes import validate_class
from .classeviva import ActiveSession
from .config import get_settings
from .errors import AppError
from .push_sender import mark_current_as_sent
from .school import require_galilei
from .security import current_session, rate_limit


def require_push() -> None:
  if not get_settings().push_enabled:
    raise AppError(503, "push_disabled", "Le notifiche push non sono attive su questo server")


router = APIRouter(prefix="/push", tags=["Notifiche push"],
                   dependencies=[Depends(current_session), Depends(require_galilei), Depends(require_push)])

# Il server fa una POST all'endpoint scelto dal browser: si accettano solo i servizi push veri,
# altrimenti chiunque abbia un account potrebbe far chiamare all'API indirizzi interni (SSRF).
PUSH_SERVICES = (
  "fcm.googleapis.com", "android.googleapis.com",  # Chrome, Edge su Android, Samsung Internet...
  "push.services.mozilla.com",  # Firefox
  "notify.windows.com",  # Edge su Windows
  "push.apple.com",  # Safari (macOS, e iOS con l'app aggiunta alla Home)
)
BASE64URL = r"^[A-Za-z0-9_-]+={0,2}$"
# Le iscrizioni non sono legate all'account (privacy): senza un limite un solo utente potrebbe riempire il database
# di endpoint finti, e ogni variazione della classe diventerebbe migliaia di invii. L'app si iscrive a ogni avvio
# e ignora gli errori (riprova al giro dopo), quindi il limite è largo.
SUBSCRIBE_PER_HOUR = 20


def is_push_service(endpoint: str) -> bool:
  try:
    parts = urlsplit(endpoint)
    port = parts.port
  except ValueError:
    return False
  host = (parts.hostname or "").lower()
  return (parts.scheme == "https" and port in (None, 443) and not parts.username and not parts.password
          and any(host == service or host.endswith("." + service) for service in PUSH_SERVICES))


class Keys(BaseModel):
  p256dh: str = Field(min_length=80, max_length=100, pattern=BASE64URL)  # punto P-256 non compresso (65 byte)
  auth: str = Field(min_length=16, max_length=32, pattern=BASE64URL)  # segreto di 16 byte


class Endpoint(BaseModel):
  endpoint: str = Field(max_length=1024)

  @field_validator("endpoint")
  @classmethod
  def _push_service(cls, value: str) -> str:
    if not is_push_service(value):
      raise ValueError("endpoint di un servizio push non riconosciuto")
    return value


class Subscription(Endpoint):
  """Come PushSubscription.toJSON() del browser (expirationTime è ignorato)."""
  keys: Keys


class SubscribeIn(BaseModel):
  subscription: Subscription
  classe: str = Field(min_length=1, max_length=16)


class PublicKeyOut(BaseModel):
  public_key: str


def _session() -> Session:
  return Session(appdb.get_engine())


@router.get("/public-key", response_model=PublicKeyOut)
def public_key():
  """Chiave VAPID pubblica (applicationServerKey per PushManager.subscribe)."""
  return PublicKeyOut(public_key=get_settings().vapid_public_key)


def save_subscription(db: Session, sub: Subscription, class_id: str) -> bool:
  """Crea o aggiorna l'iscrizione (stesso endpoint = stesso dispositivo). True se è nuova o ha cambiato classe."""
  row = db.scalar(select(appdb.PushSubscription).where(appdb.PushSubscription.endpoint == sub.endpoint))
  if row is None:
    db.add(appdb.PushSubscription(endpoint=sub.endpoint, p256dh=sub.keys.p256dh, auth=sub.keys.auth,
                                  class_id=class_id, created_at=datetime.now(timezone.utc)))
    return True
  changed = row.class_id != class_id
  row.p256dh, row.auth, row.class_id = sub.keys.p256dh, sub.keys.auth, class_id
  return changed


def _only_subscriber(db: Session, class_id: str) -> bool:
  """Con altri dispositivi iscritti `push_sent` è già aggiornato per la classe (lo tiene aggiornato l'invio)."""
  db.flush()
  total = db.scalar(select(func.count()).select_from(appdb.PushSubscription).where(appdb.PushSubscription.class_id == class_id))
  return total == 1


@router.post("/subscribe", status_code=204)
def subscribe(body: SubscribeIn, session: ActiveSession = Depends(current_session)):
  """Iscrive il dispositivo alle variazioni della classe. Si può ripetere (all'avvio, al cambio di classe):
  aggiorna l'iscrizione esistente invece di crearne un'altra. Al massimo SUBSCRIBE_PER_HOUR all'ora per utente."""
  rate_limit(f"push-subscribe:{session.username.lower()}", SUBSCRIBE_PER_HOUR, 3600)
  class_id = validate_class(body.classe)
  for attempt in range(2):  # due richieste insieme con lo stesso endpoint: la seconda trova la riga e la aggiorna
    try:
      with _session() as db, db.begin():
        if save_subscription(db, body.subscription, class_id) and _only_subscriber(db, class_id):
          # si notificano le variazioni che compaiono da ora: quelle già pubblicate sono nell'app
          mark_current_as_sent(db, class_id, datetime.now(ZoneInfo(get_settings().timezone)).date())
      return
    except IntegrityError:
      if attempt:
        raise


@router.post("/unsubscribe", status_code=204)
def unsubscribe(body: Endpoint):
  """Cancella l'iscrizione del dispositivo (notifiche spente, logout). Nessun errore se non esiste."""
  with _session() as db, db.begin():
    db.execute(delete(appdb.PushSubscription).where(appdb.PushSubscription.endpoint == body.endpoint))
