"""Database degli orari: importazione, equivalenza con la modalità JSON, integrità.

Gira su SQLite. Con TEST_DATABASE_URL=postgresql://... gira su PostgreSQL vero
(le tabelle di quel database vengono cancellate e ricreate: usa un database vuoto di prova).
"""
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import db as appdb
from app.classeviva import store
from app.db import Base, Class, Lesson, make_engine
from app.main import app
from app.schedules import DbStore, JsonStore, get_store, load_json
from conftest import login
from scripts.import_schedules import import_classes, main as import_main


@pytest.fixture
def engine(tmp_path, monkeypatch):
  eng = make_engine(os.getenv("TEST_DATABASE_URL") or f"sqlite:///{tmp_path / 'test.db'}")
  if eng.dialect.name == "sqlite":
    event.listen(eng, "connect", lambda conn, _: conn.execute("PRAGMA foreign_keys=ON"))  # come PostgreSQL
  Base.metadata.drop_all(eng)
  Base.metadata.create_all(eng)
  monkeypatch.setattr(appdb, "get_engine", lambda: eng)  # DbStore usa questo database
  import app.schedules as sched
  monkeypatch.setattr(sched, "get_engine", lambda: eng)
  import app.main as main
  monkeypatch.setattr(main, "get_engine", lambda: eng)
  yield eng
  Base.metadata.drop_all(eng)
  eng.dispose()


def run_import(engine, data_dir):
  with Session(engine) as db, db.begin():
    return import_classes(db, load_json(data_dir))


def count(engine, model):
  with Session(engine) as db:
    return db.scalar(select(func.count()).select_from(model))


def test_import_writes_classes_and_lessons(engine, data_dir):
  assert run_import(engine, data_dir) == 4  # 3 di 1A (senza la riga rumorosa) + 1 di 2B
  assert (count(engine, Class), count(engine, Lesson)) == (2, 4)
  with Session(engine) as db:
    assert db.get(Class, "1A").giorni_attivi == ["lunedi", "martedi"]


def test_import_is_idempotent(engine, data_dir):
  run_import(engine, data_dir)
  run_import(engine, data_dir)
  assert (count(engine, Class), count(engine, Lesson)) == (2, 4)  # niente duplicati


def test_reimport_replaces_the_schedule_of_a_class(engine, data_dir):
  run_import(engine, data_dir)
  f = data_dir / "classi" / "1A.json"
  f.write_text(f.read_text().replace("Matematica", "Fisica"))
  run_import(engine, data_dir)
  assert [l.materia for l in DbStore().get("1A").giorni[0].lezioni] == ["Inglese", "Fisica"]


def test_class_without_schedule_keeps_existing_lessons(engine, data_dir, tmp_path_factory):
  run_import(engine, data_dir)
  index_only = tmp_path_factory.mktemp("index")
  (index_only / "classi_index.json").write_text(
    '[{"id": "1A", "nome": "1 A NUOVO", "docente_coordinatore": "NUOVO", "pomeriggio": false, "giorni_attivi": ["lunedi", "martedi"]}]')
  run_import(engine, index_only)
  c = DbStore().get("1A")
  assert c.nome == "1 A NUOVO"  # i dati della classe si aggiornano...
  assert len(c.giorni[0].lezioni) == 2  # ...ma l'orario che c'era non si perde


def test_db_gives_same_data_as_json(engine, data_dir):
  run_import(engine, data_dir)
  js, db = JsonStore(data_dir), DbStore()
  assert js.list() == db.list()
  assert all(js.get(c.id) == db.get(c.id) for c in js.list())
  assert db.get("nope") is None and db.get("1 a").id == "1A"


def test_failed_import_changes_nothing(engine, data_dir):
  classes = load_json(data_dir)
  classes["2B"].giorni[0].lezioni.append(classes["2B"].giorni[0].lezioni[0])  # slot doppio: fallisce a metà
  with pytest.raises(Exception):
    with Session(engine) as db, db.begin():
      import_classes(db, classes)
  assert count(engine, Class) == 0


def test_lesson_slot_is_unique(engine, data_dir):
  run_import(engine, data_dir)
  with Session(engine) as db:
    db.add(Lesson(class_id="2B", giorno="lunedi", inizio="08:10", materia="Doppione"))
    with pytest.raises(IntegrityError):
      db.flush()


def test_deleting_a_class_deletes_its_lessons(engine, data_dir):
  run_import(engine, data_dir)
  with Session(engine) as db, db.begin():
    db.execute(Class.__table__.delete().where(Class.id == "1A"))  # come farebbe un DELETE a mano in SQL
  assert (count(engine, Class), count(engine, Lesson)) == (1, 1)


def test_import_cli(tmp_path, data_dir, capsys):
  url = f"sqlite:///{tmp_path / 'cli.db'}"
  assert import_main(["--data-dir", str(data_dir), "--database-url", url]) == 0  # crea anche le tabelle
  assert "2 classi e 4 lezioni" in capsys.readouterr().out
  assert import_main(["--data-dir", str(tmp_path / "vuota"), "--database-url", url]) == 1  # nessun file: errore chiaro


# ---------- l'API in modalità db ----------
def test_api_serves_schedules_from_database(engine, data_dir, settings, client, monkeypatch):
  run_import(engine, data_dir)
  monkeypatch.setattr(settings, "schedule_source", "db")
  get_store.cache_clear()
  h = login(client)
  assert [c["id"] for c in client.get("/schedules/classes", headers=h).json()] == ["1A", "2B"]
  lun = client.get("/schedules/1a", headers=h).json()["giorni"][0]
  assert [l["materia"] for l in lun["lezioni"]] == ["Inglese", "Matematica"] and lun["lezioni"][0]["fine"] == "09:00"


def test_db_error_becomes_503_without_details(engine, settings, client, monkeypatch):
  from sqlalchemy.exc import OperationalError
  monkeypatch.setattr(settings, "schedule_source", "db")
  get_store.cache_clear()

  def broken(*_):
    raise OperationalError("SELECT secret", {}, Exception("password=hunter2 host=10.0.0.5"))

  monkeypatch.setattr(DbStore, "list", broken)
  r = client.get("/schedules/classes", headers=login(client))
  assert r.status_code == 503 and r.json()["code"] == "database_unavailable"
  assert "hunter2" not in r.text and "10.0.0.5" not in r.text
