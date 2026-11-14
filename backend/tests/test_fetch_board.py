import json

import asyncio

from scripts.bacheca_fetch.fetch_bacheca import DEFAULT_PATTERN, download_attachments, filter_board, save_matches


def test_filter_board_matches_communication_for_day():
  entries = [
    {"titolo": "B: COMUNICAZIONI PER LUN. 12 OTT. (STU)", "id": 1},
    {"titolo": "Aggiornamento comunicazione per mar. 13 ott.", "id": 2},
    {"titolo": "Riunione docenti", "id": 3},
  ]

  matches = filter_board(entries, DEFAULT_PATTERN)

  assert [entry["id"] for entry in matches] == [1, 2]


def test_filter_board_searches_nested_fields():
  entries = [{"id": 1, "contenuto": {"oggetto": "Comunicazioni", "giorno": "ven 16 ott."}}]

  assert filter_board(entries, DEFAULT_PATTERN) == []
  assert filter_board(entries, r"COMUNICAZIONI.*VEN") == entries


def test_save_matches_writes_local_json(tmp_path, monkeypatch):
  monkeypatch.setenv("CLASSVIVA_BOARD_PATTERN", DEFAULT_PATTERN)
  output = tmp_path / "data" / "matches.json"

  save_matches(output, [{"id": 7, "titolo": "Comunicazioni per lun. 12 ott."}], DEFAULT_PATTERN)

  payload = json.loads(output.read_text(encoding="utf-8"))
  assert payload["count"] == 1
  assert payload["pattern"] == DEFAULT_PATTERN
  assert payload["matches"][0]["id"] == 7
  assert not output.with_suffix(".json.tmp").exists()


def test_download_attachments_saves_files_and_paths(tmp_path):
  class FakeUser:
    async def bacheca_leggi(self, codice, publication_id):
      assert (codice, publication_id) == ("CF", 37798175)

    async def bacheca_allega_(self, codice, content_id, attachment_number):
      assert (codice, content_id, attachment_number) == ("CF", 13409352, 1)
      return b"file-content"

  matches = [{
    "evtCode": "CF",
    "cntId": 13409352,
    "pubId": 37798175,
    "attachments": [{"fileName": "avviso.png", "attachNum": 1}],
  }]

  count = asyncio.run(download_attachments(FakeUser(), matches, tmp_path / "attachments"))

  assert count == 1
  saved = tmp_path / "attachments" / "13409352_1_avviso.png"
  assert saved.read_bytes() == b"file-content"
  assert matches[0]["downloaded_attachments"] == [str(saved)]


def test_download_attachments_skips_existing_files_and_failed_matches(tmp_path):
  from scripts.bacheca_fetch import fetch_bacheca

  class FakeUser:
    calls = []

    async def bacheca_leggi(self, codice, publication_id):
      self.calls.append(("leggi", publication_id))

    async def bacheca_allega_(self, codice, content_id, attachment_number):
      self.calls.append(("allega", content_id))
      return b"nuovo"

  output = tmp_path / "attachments"
  output.mkdir()
  (output / "1_1_vecchio.png").write_bytes(b"gia scaricato")
  matches = [
    {"evtCode": "CF", "cntId": 1, "pubId": 10, "attachments": [{"fileName": "vecchio.png", "attachNum": 1}]},
    {"evtCode": None, "cntId": 2, "pubId": None, "attachments": [{"fileName": "rotto.png", "attachNum": 1}]},
    {"evtCode": "CF", "cntId": 3, "pubId": 30, "attachments": [{"fileName": "nuovo.png", "attachNum": 1}]},
  ]
  user = FakeUser()
  count = asyncio.run(fetch_bacheca.download_attachments(user, matches, output))

  assert count == 1
  assert user.calls == [("leggi", 30), ("allega", 3)]  # il file già presente non si riscarica
  assert matches[0]["downloaded_attachments"] == [str(output / "1_1_vecchio.png")]
  assert matches[1]["downloaded_attachments"] == []  # comunicazione incompleta: saltata senza bloccare le altre
  assert (output / "3_1_nuovo.png").read_bytes() == b"nuovo"


def test_fetch_board_wraps_classeviva_errors(monkeypatch):
  import classeviva
  from classeviva import eccezioni
  from scripts.bacheca_fetch import fetch_bacheca

  class WrongPassword:
    def __init__(self, username, password):
      pass

    async def accedi(self):
      raise eccezioni.PasswordNonValida("password errata per S123X")

  monkeypatch.setattr(classeviva, "Utente", WrongPassword)
  try:
    asyncio.run(fetch_bacheca.fetch_board("S123X", "segreta"))
  except RuntimeError as exc:
    assert "PasswordNonValida" in str(exc) and "segreta" not in str(exc)
  else:
    raise AssertionError("doveva sollevare RuntimeError")


def test_periodic_cycle_survives_unexpected_errors(monkeypatch, caplog):
  from scripts.bacheca_fetch import run_periodic

  async def boom(args):
    raise KeyError("imprevisto")

  monkeypatch.setattr(run_periodic.fetch_bacheca, "main", boom)
  asyncio.run(run_periodic.cycle(["--output", "x.json"], with_ocr=False))  # non deve sollevare
  assert "Errore inatteso" in caplog.text
