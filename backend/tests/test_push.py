"""Notifiche push: chiavi VAPID, configurazione, iscrizioni e invio delle variazioni nuove."""
import json
import os
from datetime import date, datetime, time, timedelta
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest
from py_vapid import Vapid
from pydantic import ValidationError
from pywebpush import WebPushException
from sqlalchemy import event, select
from sqlalchemy.orm import Session

from app import db as appdb, push_sender
from app.config import Settings
from app.db import Base, PushSent, PushSubscription, make_engine
from app.push import is_push_service
from conftest import login
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
  async def idle():  # il task periodico non parte nei test: si chiama run_once a mano
    return None
  monkeypatch.setattr(push_sender, "run_forever", idle)
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


# ---------- invio delle variazioni ----------
ROME = ZoneInfo("Europe/Rome")


def at(day: str, hhmm: str) -> datetime:
  return datetime.combine(date.fromisoformat(day), time.fromisoformat(hhmm), ROME)


def board(*days):
  return {"giorni": [{"data_iso": day, "entrate": [], "uscite": [], "cambi_aula": [], **content} for day, content in days]}


def write_board(data_dir, payload):
  path = data_dir / "dati-bacheca" / "data.json"
  path.parent.mkdir(exist_ok=True)
  previous = path.stat().st_mtime_ns if path.exists() else 0
  path.write_text(json.dumps(payload), encoding="utf-8")
  stamp = max(path.stat().st_mtime_ns, previous + 1_000_000_000)  # mtime sempre diverso: la cache si rinnova
  os.utime(path, ns=(stamp, stamp))


ENTRATA = {"entrate": [{"unit_id": "e1", "classi": ["4A"], "ora": "09:50"}]}
AULA = {"cambi_aula": [{"unit_id": "a1", "classe": "4A", "aula": "AULA B120", "orario": "09:50 - 11:45"}]}
ALTRA_CLASSE = {"cambi_aula": [{"unit_id": "a9", "classe": "2B", "aula": "AULA C002", "orario": "08:10 - 09:00"}]}


class FakeSend:
  def __init__(self, statuses=None):
    self.calls, self.statuses = [], statuses or {}

  def __call__(self, subscription_info, data, **kwargs):
    self.calls.append((subscription_info["endpoint"], json.loads(data), kwargs))
    status = self.statuses.get(subscription_info["endpoint"])
    if status:
      raise WebPushException("errore", response=SimpleNamespace(status_code=status))

  def messages(self):
    return [(endpoint, message["title"], message["body"]) for endpoint, message, _ in self.calls]


def add_subscription(engine, endpoint=FCM, class_id="4A"):
  with Session(engine) as db, db.begin():
    db.add(PushSubscription(endpoint=endpoint, p256dh=KEYS["p256dh"], auth=KEYS["auth"], class_id=class_id,
                            created_at=datetime.now(ROME)))


@pytest.fixture
def sender(push_on, engine, settings, data_dir, monkeypatch):
  monkeypatch.setattr(settings, "data_dir", data_dir)
  monkeypatch.setattr(settings, "timezone", "Europe/Rome")
  return FakeSend()


def test_sends_each_new_day_once(sender, engine, data_dir):
  write_board(data_dir, board(("2026-11-16", ENTRATA), ("2026-11-17", ENTRATA), ("2026-11-18", {"cambi_aula": AULA["cambi_aula"] + ALTRA_CLASSE["cambi_aula"]})))
  add_subscription(engine)
  assert push_sender.run_once(at("2026-11-17", "10:00"), sender) == 2  # il 16 è passato, la 2B non è iscritta
  assert sender.messages() == [
    (FCM, "Variazioni 4A oggi", "Entrata alle 09:50"),
    (FCM, "Variazioni 4A domani", "Aula cambiata: AULA B120 (3ª-4ª ora)"),
  ]
  _, message, options = sender.calls[0]
  assert message["tag"] == "variazioni-4A-2026-11-17" and message["url"] == "./#home"
  assert options["vapid_claims"] == {"sub": "mailto:a@example.com"} and options["ttl"] > 0
  assert push_sender.run_once(at("2026-11-17", "10:01"), sender) == 0  # niente di nuovo: niente doppioni


def test_new_change_resends_the_whole_day(sender, engine, data_dir):
  write_board(data_dir, board(("2026-11-18", AULA)))
  add_subscription(engine)
  push_sender.run_once(at("2026-11-17", "10:00"), sender)
  write_board(data_dir, board(("2026-11-18", {**AULA, **ENTRATA})))
  assert push_sender.run_once(at("2026-11-17", "12:00"), sender) == 1
  assert sender.messages()[-1] == (FCM, "Variazioni 4A domani", "Aula cambiata: AULA B120 (3ª-4ª ora)\nEntrata alle 09:50")


def test_corrected_change_is_notified_again(sender, engine, data_dir):
  write_board(data_dir, board(("2026-11-18", AULA)))
  add_subscription(engine)
  push_sender.run_once(at("2026-11-17", "10:00"), sender)
  corrected = {"cambi_aula": [{**AULA["cambi_aula"][0], "aula": "AULA B121"}]}
  write_board(data_dir, board(("2026-11-18", corrected)))
  assert push_sender.run_once(at("2026-11-17", "10:05"), sender) == 1
  assert "B121" in sender.messages()[-1][2]


def test_quiet_hours_postpone_notifications(sender, engine, data_dir):
  write_board(data_dir, board(("2026-11-18", AULA)))
  add_subscription(engine)
  assert push_sender.run_once(at("2026-11-17", "23:30"), sender) == 0
  assert push_sender.run_once(at("2026-11-18", "06:29"), sender) == 0
  assert push_sender.run_once(at("2026-11-18", "06:30"), sender) == 1
  assert sender.messages() == [(FCM, "Variazioni 4A oggi", "Aula cambiata: AULA B120 (3ª-4ª ora)")]


def test_expired_subscriptions_are_removed(sender, engine, data_dir):
  gone, broken = "https://fcm.googleapis.com/fcm/send/gone", "https://fcm.googleapis.com/fcm/send/broken"
  sender.statuses = {gone: 410, broken: 500}
  write_board(data_dir, board(("2026-11-18", AULA)))
  for endpoint in (FCM, gone, broken):
    add_subscription(engine, endpoint)
  assert push_sender.run_once(at("2026-11-17", "10:00"), sender) == 1
  assert {endpoint for endpoint, _, _ in subscriptions(engine)} == {FCM, broken}  # 500 = problema temporaneo


def test_old_sent_rows_are_cleaned(sender, engine, data_dir):
  write_board(data_dir, board(("2026-11-18", AULA)))
  add_subscription(engine)
  push_sender.run_once(at("2026-11-17", "10:00"), sender)
  push_sender.run_once(at("2026-11-19", "10:00"), sender)
  with Session(engine) as db:
    assert db.scalars(select(PushSent)).all() == []


def test_missing_board_file_sends_nothing(sender, engine):
  add_subscription(engine)
  assert push_sender.run_once(at("2026-11-17", "10:00"), sender) == 0


def test_first_subscriber_gets_only_future_changes(push_on, client, auth, engine, data_dir, settings):
  zone = ZoneInfo(settings.timezone)
  today = datetime.now(zone).date()
  tomorrow = (today + timedelta(days=1)).isoformat()
  write_board(data_dir, board((tomorrow, AULA)))
  assert subscribe(client, auth).status_code == 204
  send, noon = FakeSend(), datetime.combine(today, time(12), zone)
  assert push_sender.run_once(noon, send) == 0  # già pubblicata quando si è iscritto: la vede nell'app
  write_board(data_dir, board((tomorrow, {**AULA, **ENTRATA})))
  assert push_sender.run_once(noon, send) == 1
  assert subscribe(client, login(client, "G123X"), endpoint=FCM + "-2").status_code == 204  # secondo dispositivo
  assert push_sender.run_once(noon, send) == 0  # push_sent era già aggiornato: nessun doppione


def test_message_helpers():
  today = date(2026, 11, 25)
  assert [push_sender.day_label(today + timedelta(days=n), today) for n in (0, 1, 2)] == ["oggi", "domani", "venerdì 27/11"]
  assert push_sender.hours_label([3]) == "3ª ora" and push_sender.hours_label([3, 4, 5]) == "3ª-5ª ora"
  quiet = push_sender.in_quiet_hours
  assert quiet(time(23), "22:00", "06:30") and quiet(time(3), "22:00", "06:30") and not quiet(time(12), "22:00", "06:30")
  assert quiet(time(14), "13:00", "15:00") and not quiet(time(15), "13:00", "15:00")
  assert not quiet(time(3), "00:00", "00:00")  # inizio = fine: silenzio spento
