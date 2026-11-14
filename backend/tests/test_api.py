"""Gli endpoint: login, orari, voti, agenda."""
import json
import asyncio
from datetime import date

from app.classeviva import store
from app.classeviva import CvSession
from app.schedules import load_json
from conftest import FakeUtente, login


# ---------- auth ----------
def test_login_and_me(client):
  r = client.post("/auth/login", json={"username": "S123X", "password": "good"})
  body = r.json()
  assert r.status_code == 200 and body["token_type"] == "bearer"
  assert body["utente"] == {"id": "S123X", "nome": "Mario", "cognome": "Rossi"}
  assert "good" not in body["access_token"]  # la password non è nel token
  me = client.get("/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
  assert me.json()["cognome"] == "Rossi"


def test_profile_uses_card_identity_when_login_data_is_empty():
  class CardUtente:
    dati = {}

    async def carta(self):
      return {"firstName": "MARIO", "lastName": "ROSSI", "schCode": "BZII0002"}

  session = CvSession("S10854114S", CardUtente())
  asyncio.run(session.load_school())

  assert session.profile["nome"] == "MARIO"
  assert session.profile["cognome"] == "ROSSI"


def test_login_wrong_password(client):
  r = client.post("/auth/login", json={"username": "S123X", "password": "bad"})
  assert r.status_code == 401 and r.json()["code"] == "invalid_credentials"


def test_logout_closes_only_this_device(client):
  phone, laptop = login(client), login(client)
  assert client.post("/auth/logout", headers=phone).status_code == 204
  assert client.get("/auth/me", headers=phone).json()["code"] == "session_expired"
  assert client.get("/auth/me", headers=laptop).status_code == 200


def test_session_lost_after_server_restart(client, auth):
  store._sessions.clear()  # come un riavvio: il frontend deve rifare il login
  r = client.get("/agenda", headers=auth)
  assert r.status_code == 401 and r.json()["code"] == "session_expired"


# ---------- orari ----------
def test_list_classes(client, auth):
  assert [c["id"] for c in client.get("/schedules/classes", headers=auth).json()] == ["1A", "2B"]


def test_week_schedule(client, auth):
  s = client.get("/schedules/1a", headers=auth).json()  # maiuscole/minuscole non contano
  assert s["id"] == "1A" and [d["giorno"] for d in s["giorni"]] == ["lunedi", "martedi"]
  lun = s["giorni"][0]
  assert lun["etichetta"] == "Lunedì"
  # la riga senza materia (rumore OCR) è scartata, il docente doppio è unico
  assert [l["materia"] for l in lun["lezioni"]] == ["Inglese", "Matematica"]
  assert lun["lezioni"][1]["docenti"] == ["FESSLER Stefano", "PNRR (301)"]
  first = lun["lezioni"][0]
  assert (first["ora"], first["inizio"], first["fine"], first["aula"]) == (1, "08:10", "09:00", "AULA B 205")


def test_today(client, auth):
  t = client.get("/schedules/1A/today", headers=auth).json()
  assert t["attivo"] == (t["giorno"] in {"lunedi", "martedi"}) and bool(t["lezioni"]) == t["attivo"]


def test_schedule_not_found_and_bad_id(client, auth):
  assert client.get("/schedules/ZZ", headers=auth).json()["code"] == "class_not_found"
  assert client.get("/schedules/1A;DROP", headers=auth).status_code == 422  # formato dell'id validato


def test_loader_skips_bad_files_and_reads_index_only_classes(tmp_path):
  (tmp_path / "classi").mkdir()
  (tmp_path / "classi" / "rotto.json").write_text("{non json")
  (tmp_path / "classi" / "senza_id.json").write_text(json.dumps({"nome": "X"}))
  (tmp_path / "classi_index.json").write_text(json.dumps(
    [{"id": "9Z", "nome": "9 Z", "docente_coordinatore": "X", "pomeriggio": False, "giorni_attivi": ["lunedi", "venerdi"]}]))
  classes = load_json(tmp_path)
  assert list(classes) == ["9Z"]  # i file non validi sono ignorati
  assert [(d.giorno, d.lezioni) for d in classes["9Z"].giorni] == [("lunedi", []), ("venerdi", [])]


# ---------- voti ----------
def test_grades_grouped_with_averages(client, auth):
  r = client.get("/grades", headers=auth).json()
  mat = {m["materia"]: m for m in r["materie"]}
  assert [m["materia"] for m in r["materie"]] == ["ITALIANO", "MATEMATICA"]
  assert mat["MATEMATICA"]["media"] == 7.0  # (7*1 + 5.5*2 + 10*1) / 4, media pesata
  assert [g["id"] for g in mat["MATEMATICA"]["voti"]] == [5, 2, 1]  # dal più recente
  assert mat["MATEMATICA"]["voti"][1]["voto"] == "5½" and mat["MATEMATICA"]["voti"][1]["colore"] == "red"
  assert mat["ITALIANO"]["media"] is None  # "Ottimo" non è numerico, il 9 è annullato
  assert r["media_generale"] == 7.0
  assert ("voti", "26") in FakeUtente.calls  # anno scolastico 2026/27


def test_grades_period_filter(client, auth):
  r = client.get("/grades?periodo=1", headers=auth).json()
  assert r["periodo"] == 1
  assert {m["materia"]: m["media"] for m in r["materie"]}["MATEMATICA"] == 6.0  # il 10 del secondo periodo è escluso


def test_grades_are_cached(client, auth):
  client.get("/grades", headers=auth)
  client.get("/grades?periodo=2", headers=auth)
  assert FakeUtente.calls.count(("voti", "26")) == 1  # una sola chiamata a ClasseViva


def test_grades_errors(client, auth):
  assert client.get("/grades?anno=2026", headers=auth).status_code == 422
  FakeUtente.fail = True
  r = client.get("/grades", headers=auth)
  assert r.status_code == 502 and r.json()["code"] == "classeviva_error"
  assert "boom" not in r.text  # i dettagli interni non arrivano al client


def test_grades_include_period_position_and_teachers(client, auth):
  r = client.get("/grades", headers=auth).json()
  mat = {m["materia"]: m for m in r["materie"]}
  assert mat["MATEMATICA"]["docenti"] == ["BIANCHI ANNA"]
  assert mat["ITALIANO"]["docenti"] == []
  assert [g["periodo_pos"] for g in mat["MATEMATICA"]["voti"]] == [2, 1, 1]


def test_grades_work_without_teachers(client, auth):
  FakeUtente.no_subjects = True
  r = client.get("/grades", headers=auth)
  assert r.status_code == 200
  assert all(m["docenti"] == [] for m in r.json()["materie"])


# ---------- assenze ----------
def test_absences_types_and_summary(client, auth):
  r = client.get("/assenze", headers=auth).json()
  assert [e["id"] for e in r["eventi"]] == [22, 25, 24, 23, 21]  # dal più recente
  assert {e["id"]: e["tipo"] for e in r["eventi"]} == {21: "assenza", 22: "assenza", 23: "ritardo", 24: "ritardo", 25: "uscita"}
  assert r["riepilogo"] == {"assenze": 2, "ritardi": 2, "uscite": 1, "da_giustificare": 2}


def test_absences_need_both_dates(client, auth):
  r = client.get("/assenze?da=2026-10-01", headers=auth)
  assert r.status_code == 422 and r.json()["code"] == "invalid_range"


# ---------- agenda ----------
def test_agenda_grouped_by_day(client, auth):
  days = client.get("/agenda?da=2026-10-05&a=2026-10-10", headers=auth).json()["giorni"]
  assert [d["data"] for d in days] == ["2026-10-05", "2026-10-06"]
  day6 = days[1]["eventi"]
  assert [e["id"] for e in day6] == [7, 8]  # prima "tutto il giorno", poi per ora
  assert day6[0]["tipo"] == "compito" and day6[0]["tutto_il_giorno"] and day6[0]["ora_inizio"] is None
  assert (day6[1]["tipo"], day6[1]["ora_inizio"], day6[1]["ora_fine"], day6[1]["testo"]) == ("annotazione", "10:30", "11:30", "Verifica")
  assert days[0]["eventi"][0]["tipo"] == "evento"


def test_agenda_default_range(client, auth):
  assert client.get("/agenda", headers=auth).status_code == 200
  da, a = (date.fromisoformat(x) for x in FakeUtente.calls[-1][1:])
  assert (a - da).days == 13


def test_agenda_errors(client, auth):
  code = lambda q: client.get(f"/agenda?{q}", headers=auth).json()["code"]
  assert code("da=2026-10-10&a=2026-10-01") == "invalid_range"
  assert code("da=2026-01-01&a=2028-01-01") == "range_too_large"
  assert code("da=2027-03-01&a=2027-03-02") == "date_out_of_range"  # fuori dall'anno scolastico (da ClasseViva)
  assert client.get("/agenda?da=boh", headers=auth).status_code == 422


# ---------- variazioni (file prodotto da bacheca -> OCR) ----------
def write_board_data(data_dir, payload):
  (data_dir / "dati-bacheca").mkdir(exist_ok=True)
  (data_dir / "dati-bacheca" / "data.json").write_text(json.dumps(payload), encoding="utf-8")


BOARD_DAYS = {"giorni": [
  {"data_iso": "2026-11-17",
   "entrate": [{"unit_id": "e1", "ora": "09:50", "classi": ["1A", "2B"]}],
   "uscite": [{"unit_id": "u1", "ora": "12:35", "classi": ["3C/T"], "note": "Assemblea"}],
   "senza_lezioni_pomeridiane": [{"unit_id": "p1", "classi": ["1A"]}],
   "cambi_aula": [{"unit_id": "a1", "classe": "1A", "orario": "09:50 - 11:45", "aula": "AULA B108"},
                  {"unit_id": "a2", "classe_dedotta": "1A", "orario": "10:55 - 11:45", "aula": "LAB. B201"}]},
  {"data_iso": "2026-11-18", "entrate": [], "uscite": [], "cambi_aula": [{"unit_id": "a3", "classe": "1a", "orario": "08:10 - 09:00", "aula": "AULA B1"}]},
]}


def test_changes_multiple_days_and_hours(client, auth, data_dir):
  write_board_data(data_dir, BOARD_DAYS)
  changes = client.get("/changes?classe=1A", headers=auth).json()
  by_id = {c["id"].split("-")[0] + "-" + c["id"].split("-")[-1]: c for c in changes}
  assert [c["data"] for c in changes] == ["2026-11-17"] * 4 + ["2026-11-18"]
  assert by_id["entrate-e1"]["tipo"] == "entrata_posticipata" and by_id["entrate-e1"]["ora"] == 3
  assert by_id["aula-a1"]["ore"] == [3, 4]  # la 5ª inizia alle 11:45, quando il cambio finisce and by_id["aula-a1"]["nuova_aula"] == "AULA B108"
  assert by_id["aula-a2"]["ore"] == [4]  # orario fuori griglia: solo le ore che si sovrappongono (4ª: 10:40-11:30)
  assert by_id["pomeriggio-p1"]["tipo"] == "senza_lezioni_pomeridiane" and by_id["pomeriggio-p1"]["ora"] == 8
  only_day = client.get("/changes?classe=1A&data=2026-11-18", headers=auth).json()
  assert [c["nuova_aula"] for c in only_day] == ["AULA B1"]


def test_changes_articulated_class_and_filters(client, auth, data_dir):
  write_board_data(data_dir, BOARD_DAYS)
  exits = client.get("/changes/entrate-uscite?classe=3T", headers=auth).json()
  assert [(c["tipo"], c["ora"]) for c in exits] == [("uscita_anticipata", 6)]  # "3C/T" vale anche per 3T
  rooms = client.get("/changes/cambi-aula?classe=1A", headers=auth).json()
  assert {c["tipo"] for c in rooms} == {"cambio_aula"}


def test_changes_legacy_single_day_format(client, auth, data_dir):
  write_board_data(data_dir, {"data_iso": "2026-03-30", "entrate": [], "uscite": [],
                              "cambi_aula": [{"unit_id": "x", "classe": "2B", "aula": "AULA D205", "orario": "08:10 - 09:00"}]})
  r = client.get("/changes?classe=2b", headers=auth).json()
  assert r == [{"id": "aula-2026-03-30-x", "data": "2026-03-30", "ora": 1, "ore": [1], "tipo": "cambio_aula",
                "testo": "Aula cambiata: AULA D205", "nuova_aula": "AULA D205", "orario": "08:10 - 09:00"}]


def test_changes_errors(client, auth, data_dir):
  r = client.get("/changes?classe=1A", headers=auth)
  assert r.status_code == 503 and r.json()["code"] == "changes_unavailable"  # file non ancora prodotto
  write_board_data(data_dir, BOARD_DAYS)
  assert client.get("/changes?classe=1A;DROP", headers=auth).status_code == 422
  assert client.get("/changes?classe=1A").status_code == 401
