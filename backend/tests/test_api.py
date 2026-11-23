"""Gli endpoint: login, orari, voti, agenda."""
import json
import asyncio
from datetime import date

from app.classeviva import store
from app.classeviva import CvSession
from app.schedules import load_json
from classeviva import eccezioni
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


def test_refresh_keeps_the_same_session(client, auth):
  r = client.post("/auth/refresh", headers=auth)
  body = r.json()
  assert r.status_code == 200 and body["token_type"] == "bearer" and body["expires_in"] > 0
  new = {"Authorization": f"Bearer {body['access_token']}"}
  assert client.get("/grades", headers=new).status_code == 200  # la chiave della password è la stessa
  assert client.get("/auth/me", headers=auth).status_code == 200  # il vecchio token vale fino alla scadenza
  assert client.post("/auth/logout", headers=new).status_code == 204  # stessa sessione: il logout chiude entrambi
  assert client.get("/auth/me", headers=auth).json()["code"] == "session_expired"


def test_refresh_after_logout_fails(client, auth):
  client.post("/auth/logout", headers=auth)
  r = client.post("/auth/refresh", headers=auth)
  assert r.status_code == 401 and r.json()["code"] == "session_expired"


def test_session_used_without_classeviva_calls_stays_alive(client, auth, settings, monkeypatch):
  # gli orari non chiamano ClasseViva, ma usarli deve evitare che la sessione venga eliminata come inattiva
  session = next(iter(store._sessions.values()))
  session.last_used -= settings.jwt_ttl_hours * 3600 + 1
  client.get("/schedules/classes", headers=auth)
  login(client, "ALTRO")  # ogni login elimina le sessioni inattive
  assert client.get("/auth/me", headers=auth).status_code == 200


def test_password_changed_on_classeviva_closes_the_session(client, auth):
  # al ricollegamento ClasseViva rifiuta la password (cambiata dopo il login): niente errori a ripetizione
  session = next(iter(store._sessions.values()))
  session.utente.inizio = None
  original = FakeUtente.voti

  async def rejected(self, anno):
    raise eccezioni.PasswordNonValida("no")
  FakeUtente.voti = rejected
  try:
    r = client.get("/grades", headers=auth)
  finally:
    FakeUtente.voti = original
  assert r.status_code == 401 and r.json()["code"] == "credentials_changed"
  assert client.get("/auth/me", headers=auth).json()["code"] == "session_expired"


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
  assert mat["MATEMATICA"]["media"] == 7.0  # (7*1 + 5.5*2 + 10*1) / 4, media pesata; il 2 "non fa media" è escluso
  assert [g["id"] for g in mat["MATEMATICA"]["voti"]] == [5, 6, 2, 1]  # dal più recente
  assert [g["fa_media"] for g in mat["MATEMATICA"]["voti"]] == [True, False, True, True]
  assert mat["MATEMATICA"]["voti"][2]["voto"] == "5½" and mat["MATEMATICA"]["voti"][2]["colore"] == "red"
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
  assert [g["periodo_pos"] for g in mat["MATEMATICA"]["voti"]] == [2, 1, 1, 1]


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
  assert by_id["entrate-e1"]["ore"] == [1, 2]
  assert by_id["aula-a1"]["ore"] == [3, 4]  # la 5ª inizia alle 11:45, quando il cambio finisce and by_id["aula-a1"]["nuova_aula"] == "AULA B108"
  assert by_id["aula-a2"]["ore"] == [4]  # orario fuori griglia: solo le ore che si sovrappongono (4ª: 10:55-11:45)
  assert by_id["pomeriggio-p1"]["tipo"] == "senza_lezioni_pomeridiane" and by_id["pomeriggio-p1"]["ora"] == 8
  assert by_id["pomeriggio-p1"]["ore"] == [8, 9, 10, 11]
  only_day = client.get("/changes?classe=1A&data=2026-11-18", headers=auth).json()
  assert [c["nuova_aula"] for c in only_day] == ["AULA B1"]


def test_entrance_and_exit_lost_hours():
  from app.changes import hours_lost_entrance, hours_lost_exit
  assert hours_lost_entrance("09:50") == [1, 2]
  assert hours_lost_entrance("14:30") == [1, 2, 3, 4, 5, 6, 7]  # entra per il pomeriggio: salta la mattina
  assert hours_lost_entrance("15:20") == [8]  # mattina fatta tutta, salta solo la prima pomeridiana
  assert hours_lost_exit("11:45") == [5, 6, 7]  # il pomeriggio resta
  assert hours_lost_exit("14:30") == [8, 9, 10, 11]
  assert hours_lost_exit("16:10") == [10, 11]
  assert hours_lost_entrance("boh") == [] and hours_lost_exit(None) == []


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


# ---------- revisione: controlli e dati esposti ----------
def test_absences_range_checks(client, auth):
  r = client.get("/assenze?da=2026-10-10&a=2026-10-01", headers=auth)
  assert r.status_code == 422 and r.json()["code"] == "invalid_range"
  r = client.get("/assenze?da=2025-01-01&a=2026-10-01", headers=auth)
  assert r.status_code == 422 and r.json()["code"] == "range_too_large"


def test_board_detail_does_not_expose_raw_classeviva_data(client, auth):
  r = client.get("/bacheca/CF/12", headers=auth)
  assert r.status_code == 200
  assert r.json() == {"titolo": "Circolare 1", "testo": "Testo"}
  assert "interno" not in r.text


def test_validation_errors_do_not_echo_input(client):
  secret = "segreta-" + "x" * 300  # oltre i 256 caratteri ammessi
  r = client.post("/auth/login", json={"username": "S123X", "password": secret})
  assert r.status_code == 422 and r.json()["code"] == "validation_error"
  assert r.json()["detail"][0]["loc"] == ["body", "password"]
  assert "segreta" not in r.text


def test_session_cache_drops_expired_entries(client, auth, settings, monkeypatch):
  from app import classeviva
  session = next(iter(classeviva.store._sessions.values()))
  monkeypatch.setattr(settings, "cache_ttl_seconds", 0)  # ogni risposta è subito scaduta
  client.get("/agenda?da=2026-10-01&a=2026-10-05", headers=auth)
  client.get("/agenda?da=2026-10-06&a=2026-10-10", headers=auth)
  assert len(session._cache) == 1  # restano solo le risposte ancora valide


def test_grid_with_breaks():
  from app.schedules import make_lesson
  def hour(start):
    l = make_lesson(start, "X", None, [], None)
    return l.ora, l.inizio, l.fine
  assert hour("09:50") == (3, "09:50", "10:40")
  assert hour("10:55") == (4, "10:55", "11:45")  # dopo la pausa 10:40-10:55
  assert hour("10:40") == (4, "10:55", "11:45")  # inizio della griglia vecchia, ancora nei dati
  assert hour("15:20") == (9, "15:20", "16:10")
  assert hour("16:20") == (10, "16:20", "17:10")  # dopo la pausa 16:10-16:20
  assert hour("16:10") == (10, "16:20", "17:10")
  assert hour("17:10") == (11, "17:10", "18:00")
  assert hour("10:00") == (None, "10:00", "10:50")  # fuori griglia: 50 minuti
