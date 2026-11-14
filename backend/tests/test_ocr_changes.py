import json
from datetime import date

import pytest

from scripts.bacheca_fetch import ocr_changes as oc


def ocr_result(source, data_iso="2026-11-17", titolo="alta", **sections):
  result = {"schema_versione": 2, "_source": source, "data_iso": data_iso, "titolo_affidabilita": titolo,
            "entrate": [], "uscite": [], "senza_lezioni_pomeridiane": [], "cambi_aula": []}
  result.update(sections)
  return result


ROOM_OK = {"unit_id": "r1", "classe": "4A", "orario": "10:40 - 11:30", "aula": "LAB. B201", "affidabilita": "alta",
           "motivi": [], "verifica": "ok"}
ROOM_DOUBT = {"unit_id": "r2", "classe": "4B", "orario": "08:10 - 09:00", "aula": "AULA B1", "affidabilita": "media",
              "motivi": ["aula_fuori_elenco"], "verifica": "da_verificare"}
EXIT_OK = {"unit_id": "u1", "ora": "12:35", "classi": ["4A"], "note": "", "affidabilita": "alta", "motivi": []}


def test_day_from_result_keeps_only_reliable_entries():
  day = oc.day_from_result(ocr_result("a.png", cambi_aula=[ROOM_OK, ROOM_DOUBT], uscite=[EXIT_OK]), "alta")
  assert day["data_iso"] == "2026-11-17"
  assert day["cambi_aula"] == [{"unit_id": "r1", "classe": "4A", "orario": "10:40 - 11:30", "aula": "LAB. B201", "affidabilita": "alta"}]
  assert day["uscite"][0]["classi"] == ["4A"]
  assert len(oc.day_from_result(ocr_result("a.png", cambi_aula=[ROOM_OK, ROOM_DOUBT]), "media")["cambi_aula"]) == 2


def test_day_from_result_skips_unsure_date():
  assert oc.day_from_result(ocr_result("a.png", data_iso=None), "alta") is None
  assert oc.day_from_result(ocr_result("a.png", titolo="bassa"), "alta") is None
  # titolo incerto ma data coerente con la pubblicazione della comunicazione: si usa
  assert oc.day_from_result(ocr_result("a.png", titolo="media"), "alta", "2026-11-16T14:00:00+01:00")["data_iso"] == "2026-11-17"
  # data lontana dalla pubblicazione: probabilmente letta male
  assert oc.day_from_result(ocr_result("a.png", titolo="media"), "alta", "2026-05-01T14:00:00+02:00") is None


def test_build_days_latest_publication_wins_and_past_days_are_dropped():
  first = {"data_iso": "2026-11-17", "entrate": [], "uscite": [], "senza_lezioni_pomeridiane": [], "cambi_aula": [ROOM_OK]}
  update = {"data_iso": "2026-11-17", "entrate": [], "uscite": [EXIT_OK], "senza_lezioni_pomeridiane": [], "cambi_aula": []}
  second_image = {"data_iso": "2026-11-17", "entrate": [], "uscite": [], "senza_lezioni_pomeridiane": [], "cambi_aula": [ROOM_DOUBT]}
  old = {"data_iso": "2026-11-10", "entrate": [], "uscite": [], "senza_lezioni_pomeridiane": [], "cambi_aula": [ROOM_OK]}
  days = oc.build_days(
    [("2026-11-16T12:00:00", [first]), ("2026-11-16T15:00:00", [update, second_image]), ("2026-11-09T12:00:00", [old])],
    today=date(2026, 11, 17),
  )
  assert [day["data_iso"] for day in days] == ["2026-11-17"]
  assert days[0]["uscite"] == [EXIT_OK] and days[0]["cambi_aula"] == [ROOM_DOUBT]  # l'aggiornamento sostituisce, le sue immagini si uniscono


@pytest.fixture
def board(tmp_path):
  image = tmp_path / "allegati" / "cartellone.png"
  image.parent.mkdir()
  image.write_bytes(b"png finto")
  pdf = tmp_path / "allegati" / "circolare.pdf"
  pdf.write_bytes(b"pdf")
  matches = tmp_path / "board_matches.json"
  matches.write_text(json.dumps({"matches": [{"pubDT": "2026-11-16T12:00:00", "evtCode": "CF", "pubId": 1,
                                              "downloaded_attachments": [str(image), str(pdf)]}]}))
  return tmp_path, matches


def make_args(tmp_path, matches, **extra):
  args = oc.parse_args(["--matches", str(matches), "--output", str(tmp_path / "out" / "data.json"),
                        "--cache-dir", str(tmp_path / "cache")], {})
  for key, value in extra.items():
    setattr(args, key, value)
  return args


def test_run_writes_changes_and_uses_cache(board):
  tmp_path, matches = board
  calls = []

  def fake_ocr(image):
    calls.append(image.name)
    return ocr_result(image.name, cambi_aula=[ROOM_OK, ROOM_DOUBT])

  args = make_args(tmp_path, matches)
  assert oc.run(args, fake_ocr, today=date(2026, 11, 17)) == 0
  payload = json.loads((tmp_path / "out" / "data.json").read_text(encoding="utf-8"))
  assert payload["affidabilita_minima"] == "alta"
  assert [entry["classe"] for entry in payload["giorni"][0]["cambi_aula"]] == ["4A"]
  assert calls == ["cartellone.png"]  # il PDF non va all'OCR

  assert oc.run(args, fake_ocr, today=date(2026, 11, 17)) == 0
  assert calls == ["cartellone.png"]  # seconda volta: risultato dalla cache


def test_run_keeps_previous_file_when_every_image_fails(board):
  tmp_path, matches = board
  output = tmp_path / "out" / "data.json"
  output.parent.mkdir()
  output.write_text('{"giorni": ["precedente"]}')

  def broken_ocr(image):
    raise oc.OcrError("Ollama non risponde")

  assert oc.run(make_args(tmp_path, matches), broken_ocr, today=date(2026, 11, 17)) == 1
  assert json.loads(output.read_text()) == {"giorni": ["precedente"]}


def test_run_rejects_unknown_ocr_format(board):
  tmp_path, matches = board
  assert oc.run(make_args(tmp_path, matches), lambda image: {"schema_versione": 1}, today=date(2026, 11, 17)) == 1


def test_run_reports_missing_matches_file(tmp_path):
  assert oc.run(make_args(tmp_path, tmp_path / "manca.json"), lambda image: {}, today=date(2026, 11, 17)) == 2
