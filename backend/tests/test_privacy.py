"""Privacy: i trattamenti fanno solo quello che dice l'informativa (frontend/src/legal/privacy.md)."""
import logging
import os
import time
from datetime import UTC, datetime, timedelta

from app import classeviva
from app.classeviva import pseudonym, store
from app.school import is_galilei
from conftest import login
from scripts.bacheca_fetch.fetch_bacheca import prune_files, recent

GALILEI = {"codice": "BZTF000000", "nome": "ITT", "dedica": "G. GALILEI", "citta": "Bolzano", "provincia": "BZ"}
ALTRA = {"codice": "RMPS000000", "nome": "LICEO SCIENTIFICO", "dedica": "A. RIGHI", "citta": "Roma", "provincia": "RM"}


# ---------- dati sanitari ----------
def test_absence_reason_is_never_returned_nor_cached(client, auth):
  r = client.get("/assenze", headers=auth).json()
  assert all("motivo" not in event for event in r["eventi"])
  cached = [value for session in store._sessions.values() for _, value in session._cache.values()]
  assert cached and "Salute" not in repr(cached)  # il motivo non resta neanche in memoria


# ---------- log ----------
def test_failed_login_logs_a_pseudonym_not_the_username(client, caplog):
  with caplog.at_level(logging.WARNING, logger="skedoo"):
    client.post("/auth/login", json={"username": "S7654321X", "password": "bad"})
  assert "S7654321X" not in caplog.text and "s7654321x" not in caplog.text
  assert pseudonym("S7654321X") in caplog.text and pseudonym("S7654321X") == pseudonym("s7654321x")


# ---------- durate in memoria ----------
def test_prune_drops_old_sessions_and_old_cache(client, settings, monkeypatch):
  auth = login(client, "S1X")
  client.get("/grades", headers=auth)
  session = next(iter(store._sessions.values()))
  assert session._cache
  real = time.monotonic
  monkeypatch.setattr(classeviva.time, "monotonic", lambda: real() + settings.cache_ttl_seconds + 1)
  store.prune()
  assert store._sessions and not session._cache  # sessione viva, risposte vecchie scartate
  monkeypatch.setattr(classeviva.time, "monotonic", lambda: real() + settings.jwt_ttl_hours * 3600 + 1)
  store.prune()
  assert not store._sessions  # inattiva oltre JWT_TTL_HOURS: via, con la password cifrata


# ---------- dati di una sola scuola ----------
def test_school_rule():
  assert is_galilei(GALILEI) is True
  assert is_galilei({**GALILEI, "dedica": "Galileo Galilei", "citta": "BOLZANO "}) is True
  assert is_galilei(ALTRA) is False
  assert is_galilei({**GALILEI, "citta": "Roma"}) is False  # altro Galilei
  assert is_galilei(None) is None


def test_other_schools_cannot_read_schedules_changes_and_push(client, auth):
  session = next(iter(store._sessions.values()))
  session._school = ALTRA
  for path in ("/schedules/classes", "/schedules/1A", "/changes?classe=1A", "/push/public-key"):
    r = client.get(path, headers=auth)
    assert r.status_code == 403 and r.json()["code"] == "school_not_supported", path
  session._school = GALILEI
  assert client.get("/schedules/classes", headers=auth).status_code == 200
  session._school = None  # carta ClasseViva non disponibile: scuola sconosciuta, accesso aperto
  assert client.get("/schedules/classes", headers=auth).status_code == 200


# ---------- immagini dei cartelloni ----------
def test_only_recent_communications_are_kept():
  now = datetime(2026, 11, 25, 12, tzinfo=UTC)
  matches = [{"pubDT": (now - timedelta(days=3)).isoformat()}, {"pubDT": (now - timedelta(days=40)).isoformat()},
             {"pubDT": "2026-11-20T08:00:00"}, {"pubDT": None}]
  assert [m["pubDT"] for m in recent(matches, 14, now)] == [matches[0]["pubDT"], "2026-11-20T08:00:00", None]


def test_old_files_are_deleted(tmp_path):
  old, new = tmp_path / "vecchio.png", tmp_path / "nuovo.png"
  old.write_bytes(b"x")
  new.write_bytes(b"x")
  month_ago = time.time() - 31 * 86400
  os.utime(old, (month_ago, month_ago))
  assert prune_files(tmp_path, 30) == 1
  assert not old.exists() and new.exists()
  assert prune_files(tmp_path / "manca", 30) == 0
