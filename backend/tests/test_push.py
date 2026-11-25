"""Notifiche push: chiavi VAPID, configurazione, iscrizioni e invio delle variazioni nuove."""
import pytest
from py_vapid import Vapid
from pydantic import ValidationError
from sqlalchemy import event, select
from sqlalchemy.orm import Session

from app import db as appdb
from app.config import Settings
from app.db import Base, PushSubscription, make_engine
from app.push import is_push_service
from scripts.generate_vapid import generate


# ---------- chiavi e configurazione ----------
def test_generated_keys_are_usable_by_pywebpush():
  public, private = generate()
  assert len(public) == 87 and len(private) == 43  # 65 e 32 byte in base64url senza "="
  vapid = Vapid.from_string(private_key=private)  # lo stesso caricamento che fa pywebpush.webpush
  assert vapid.public_key is not None


def test_push_needs_both_keys_and_database():
  public, private = generate()
  base = {"vapid_public_key": public, "vapid_private_key": private, "vapid_subject": "mailto:admin@example.com"}
  assert Settings(_env_file=None, **base, database_url="sqlite://").push_enabled
  assert not Settings(_env_file=None, **base).push_enabled  # senza database le iscrizioni non si salvano
  assert not Settings(_env_file=None).push_enabled


@pytest.mark.parametrize("values", [
  {"vapid_public_key": "x"},  # manca la privata
  {"vapid_public_key": "x", "vapid_private_key": "y"},  # manca il contatto
  {"vapid_public_key": "x", "vapid_private_key": "y", "vapid_subject": "admin@example.com"},  # senza mailto:
])
def test_invalid_push_configuration_is_rejected(values):
  with pytest.raises(ValidationError):
    Settings(_env_file=None, **values)


# ---------- iscrizioni ----------
FCM = "https://fcm.googleapis.com/fcm/send/abc123"
KEYS = {"p256dh": "B" + "A" * 86, "auth": "c2VncmV0by1kaS0xNmI"}


@pytest.fixture
def engine(tmp_path, monkeypatch):
  eng = make_engine(f"sqlite:///{tmp_path / 'push.db'}")
  event.listen(eng, "connect", lambda conn, _: conn.execute("PRAGMA foreign_keys=ON"))
  Base.metadata.create_all(eng)
  monkeypatch.setattr(appdb, "get_engine", lambda: eng)
  import app.main as main
  monkeypatch.setattr(main, "get_engine", lambda: eng)
  yield eng
  eng.dispose()


@pytest.fixture
def push_on(engine, settings, monkeypatch):
  public, private = generate()
  for name, value in {"vapid_public_key": public, "vapid_private_key": private, "vapid_subject": "mailto:a@example.com",
                      "database_url": "sqlite://"}.items():
    monkeypatch.setattr(settings, name, value)
  return public


def subscriptions(engine):
  with Session(engine) as db:
    return [(s.endpoint, s.class_id, s.auth) for s in db.scalars(select(PushSubscription).order_by(PushSubscription.id))]


def subscribe(client, auth, endpoint=FCM, classe="4a", keys=KEYS):
  return client.post("/push/subscribe", headers=auth, json={"subscription": {"endpoint": endpoint, "keys": keys}, "classe": classe})


def test_push_disabled_without_configuration(client, auth):
  r = client.get("/push/public-key", headers=auth)
  assert r.status_code == 503 and r.json()["code"] == "push_disabled"


def test_public_key_requires_login(push_on, client, auth):
  assert client.get("/push/public-key").status_code == 401
  assert client.get("/push/public-key", headers=auth).json() == {"public_key": push_on}


def test_subscribe_upserts_by_endpoint(push_on, client, auth, engine):
  assert subscribe(client, auth).status_code == 204
  assert subscriptions(engine) == [(FCM, "4A", KEYS["auth"])]
  new_keys = {**KEYS, "auth": "bnVvdm8tc2VncmV0by0xNg"}
  assert subscribe(client, auth, classe="3C", keys=new_keys).status_code == 204  # stesso dispositivo: niente doppioni
  assert subscriptions(engine) == [(FCM, "3C", new_keys["auth"])]
  assert client.post("/push/unsubscribe", headers=auth, json={"endpoint": FCM}).status_code == 204
  assert subscriptions(engine) == []
  assert client.post("/push/unsubscribe", headers=auth, json={"endpoint": FCM}).status_code == 204  # già cancellata


@pytest.mark.parametrize("endpoint", [
  "http://fcm.googleapis.com/fcm/send/x",  # niente https
  "https://127.0.0.1/x", "https://localhost/x", "https://db:5432/x",  # indirizzi interni (SSRF)
  "https://fcm.googleapis.com.evil.it/x", "https://evilfcm.googleapis.com.it/x",
  "https://user:pw@fcm.googleapis.com/x", "https://fcm.googleapis.com:8443/x",
])
def test_subscribe_rejects_unknown_push_services(push_on, client, auth, engine, endpoint):
  assert subscribe(client, auth, endpoint=endpoint).status_code == 422
  assert subscriptions(engine) == []


def test_subscribe_validates_keys_and_class(push_on, client, auth):
  assert subscribe(client, auth, keys={**KEYS, "auth": "corto"}).status_code == 422
  assert subscribe(client, auth, keys={**KEYS, "p256dh": "<script>" * 12}).status_code == 422
  assert subscribe(client, auth, classe="4A;DROP").status_code == 422
  assert subscribe(client, auth).status_code == 204
  assert subscribe(client, {}).status_code == 401


def test_known_push_services():
  for endpoint in ("https://fcm.googleapis.com/fcm/send/x", "https://updates.push.services.mozilla.com/wpush/v2/x",
                   "https://wns2-par02p.notify.windows.com/w/?token=x", "https://web.push.apple.com/QH4x"):
    assert is_push_service(endpoint), endpoint
