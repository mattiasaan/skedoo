import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import classeviva  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.main import app  # noqa: E402
from app.schedules import get_store  # noqa: E402
from app.security import limiter  # noqa: E402
from classeviva import eccezioni  # noqa: E402

# --- dati finti di ClasseViva ---
GRADES = [
  {"evtId": 1, "subjectId": 10, "subjectDesc": "MATEMATICA", "evtDate": "2026-09-30", "decimalValue": 7.0,
   "displayValue": "7", "componentDesc": "Scritto", "periodPos": 1, "periodDesc": "Primo periodo",
   "weightFactor": 1.0, "color": "green", "canceled": False, "notesForFamily": ""},
  {"evtId": 2, "subjectId": 10, "subjectDesc": "MATEMATICA", "evtDate": "2026-10-02", "decimalValue": 5.5,
   "displayValue": "5½", "componentDesc": "Orale", "periodPos": 1, "periodDesc": "Primo periodo",
   "weightFactor": 2.0, "color": "red", "canceled": False},
  {"evtId": 5, "subjectId": 10, "subjectDesc": "MATEMATICA", "evtDate": "2026-12-01", "decimalValue": 10.0,
   "displayValue": "10", "periodPos": 2, "periodDesc": "Secondo periodo", "weightFactor": 1.0, "canceled": False},
  {"evtId": 3, "subjectId": 11, "subjectDesc": "ITALIANO", "evtDate": "2026-10-01", "decimalValue": None,
   "displayValue": "Ottimo", "periodPos": 1, "weightFactor": 1.0, "canceled": False},
  {"evtId": 4, "subjectId": 11, "subjectDesc": "ITALIANO", "evtDate": "2026-10-03", "decimalValue": 9.0,
   "displayValue": "9", "periodPos": 1, "weightFactor": 1.0, "canceled": True},
]
AGENDA = [
  {"evtId": 7, "evtCode": "AGHW", "evtDatetimeBegin": "2026-10-06T00:00:00+02:00", "evtDatetimeEnd": "2026-10-06T23:59:59+02:00",
   "isFullDay": True, "notes": "Es. 4 pag 12", "authorName": "ROSSI Mario", "subjectDesc": "MATEMATICA"},
  {"evtId": 8, "evtCode": "AGNT", "evtDatetimeBegin": "2026-10-06T10:30:00+02:00", "evtDatetimeEnd": "2026-10-06T11:30:00+02:00",
   "isFullDay": False, "notes": "Verifica", "authorName": "BIANCHI Anna", "subjectDesc": "ITALIANO"},
  {"evtId": 9, "evtCode": "AGEV", "evtDatetimeBegin": "2026-10-05T08:00:00+02:00", "evtDatetimeEnd": "2026-10-05T09:00:00+02:00",
   "isFullDay": False, "notes": None},
]


class FakeUtente:
  """Al posto di classeviva.Utente: password "good" = login ok."""
  calls: list = []
  fail = False

  def __init__(self, id_, password):
    self.id, self.password, self.inizio, self._dati = id_, password, None, {}

  async def accedi(self):
    if self.password != "good":
      raise eccezioni.PasswordNonValida("no")
    self._dati = {"firstName": "Mario", "lastName": "Rossi"}

  async def voti(self, anno):
    FakeUtente.calls.append(("voti", anno))
    if FakeUtente.fail:
      raise eccezioni.ErroreHTTP("boom: dettaglio interno")
    return GRADES

  async def agenda_da_a(self, inizio, fine):
    FakeUtente.calls.append(("agenda", inizio, fine))
    if inizio > "2026-12-31":
      raise eccezioni.DataFuoriGamma("fuori")
    return AGENDA


# --- dati di prova degli orari ---
CLASS_1A = {
  "id": "1A", "nome": "1 A", "docente_coordinatore": "PATELLA Nadia", "pomeriggio": True,
  "giorni_attivi": ["lunedi", "martedi"],
  "orario": {
    "lunedi": {
      "08:10": {"materia": "Inglese", "materia_completa": "Lingua inglese", "docenti": ["ALIAJ Mimoza"], "aula": "AULA B 205"},
      "09:00": {"materia": "Matematica", "docenti": ["FESSLER Stefano", "FESSLER Stefano", "PNRR (301)"]},
      "10:40": {"materia": None, "docenti": []},  # rumore dell'OCR: scartato
    },
    "martedi": {"08:10": {"materia": "Storia", "docenti": ["BIANCHI Anna"], "aula": "AULA B 107"}},
  },
}
CLASS_2B = {"id": "2B", "nome": "2 B", "docente_coordinatore": "VERDI Luca", "pomeriggio": False,
            "giorni_attivi": ["lunedi"], "orario": {"lunedi": {"08:10": {"materia": "Fisica", "docenti": ["X Y"]}}}}


@pytest.fixture
def data_dir(tmp_path):
  (tmp_path / "classi").mkdir()
  (tmp_path / "classi" / "1A.json").write_text(json.dumps(CLASS_1A))
  (tmp_path / "tutte_le_classi.json").write_text(json.dumps({"2B": CLASS_2B}))
  return tmp_path


@pytest.fixture
def settings():
  return get_settings()


@pytest.fixture
def client(monkeypatch, settings, data_dir):
  monkeypatch.setattr(classeviva, "Utente", FakeUtente)
  monkeypatch.setattr(settings, "data_dir", data_dir)
  FakeUtente.calls, FakeUtente.fail = [], False
  classeviva.store._sessions.clear()
  limiter.clear()
  get_store.cache_clear()
  with TestClient(app) as c:
    yield c
  get_store.cache_clear()


def login(client, username="S123X", password="good"):
  r = client.post("/auth/login", json={"username": username, "password": password})
  assert r.status_code == 200, r.text
  return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def auth(client):
  return login(client)
