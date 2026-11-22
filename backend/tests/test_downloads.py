"""Download di allegati (bacheca) e materiali (didattica): streaming, limiti, nuovo login, link."""
import json

import pytest
from classeviva.collegamenti.collegamenti import Collegamenti
from requests.structures import CaseInsensitiveDict

from app import downloads
from app.classeviva import Connection, CvSession


class FakeResponse:
  is_redirect = False

  def __init__(self, status=200, chunks=(b"%PDF-1.7 ciao",), headers=None):
    self.status_code = status
    self.headers = CaseInsensitiveDict(headers or {"content-type": "application/pdf"})
    self._chunks = list(chunks)
    self.closed = False

  def iter_content(self, _size):
    yield from self._chunks

  def close(self):
    self.closed = True


class FakeHttp:
  def close(self):
    pass


@pytest.fixture
def upstream(monkeypatch):
  """Le risposte di ClasseViva, in ordine; registra gli URL chiesti e i login forzati."""
  state = {"responses": [], "urls": [], "relogins": 0, "opened": []}

  def connect(self, key, relogin):
    state["relogins"] += relogin
    return Connection("4242", {"User-Agent": "test"}, {})

  def open_(conn, url):
    state["urls"].append(url)
    response = state["responses"].pop(0)
    state["opened"].append(response)
    return FakeHttp(), response

  monkeypatch.setattr(CvSession, "_connect", connect)
  monkeypatch.setattr(downloads, "_open", open_)
  downloads.slots.clear()
  yield state
  downloads.slots.clear()


def test_board_attachment_is_streamed(client, auth, upstream):
  upstream["responses"].append(FakeResponse(chunks=[b"%PDF", b"-1.7"], headers={
    "content-type": "application/pdf; charset=binary", "content-length": "8",
    "content-disposition": "attachment; filename*=UTF-8''Circolare%20n.%2012%20%E2%80%93%20gita.pdf",
  }))
  r = client.get("/bacheca/CF/12/allegati/2", headers=auth)
  assert r.status_code == 200 and r.content == b"%PDF-1.7"
  assert r.headers["content-type"] == "application/pdf"
  assert r.headers["content-length"] == "8"
  assert "filename*=UTF-8''Circolare%20n.%2012%20%E2%80%93%20gita.pdf" in r.headers["content-disposition"]
  assert upstream["urls"] == [Collegamenti.bacheca_allega.format("4242", "CF", 12, 2)]
  assert upstream["opened"][0].closed  # connessione verso ClasseViva chiusa a fine trasferimento
  assert downloads.slots._active == {}


def test_material_file_and_bad_params(client, auth, upstream):
  upstream["responses"].append(FakeResponse(headers={"content-type": "weird type!"}))
  r = client.get("/didattica/77", headers=auth)
  assert r.status_code == 200 and r.headers["content-type"] == "application/octet-stream"
  assert r.headers["content-disposition"] == "attachment"  # ClasseViva non ha dato il nome: lo sceglie il frontend
  assert upstream["urls"] == [Collegamenti.didattica_elemento.format("4242", 77)]
  assert client.get("/didattica/0", headers=auth).status_code == 422
  assert client.get("/bacheca/C%2FF/12/allegati/1", headers=auth).status_code in (404, 422)
  assert client.get("/didattica/77").status_code == 401  # serve il login


def test_too_large_is_refused_before_streaming(client, auth, upstream, settings, monkeypatch):
  monkeypatch.setattr(settings, "max_download_mb", 1)
  upstream["responses"].append(FakeResponse(headers={"content-type": "video/mp4", "content-length": str(2 * 1024 * 1024)}))
  r = client.get("/didattica/5", headers=auth)
  assert r.status_code == 413 and r.json()["code"] == "file_too_large"
  assert "1 MB" in r.json()["message"]
  assert upstream["opened"][0].closed and downloads.slots._active == {}


def test_stream_without_length_is_cut_at_the_limit(client, auth, upstream, settings, monkeypatch):
  monkeypatch.setattr(settings, "max_download_mb", 1)
  upstream["responses"].append(FakeResponse(chunks=[b"x" * 600_000, b"x" * 600_000], headers={"content-type": "video/mp4"}))
  with pytest.raises(RuntimeError, match="limite"):  # connessione interrotta, non un file troncato "completo"
    client.get("/didattica/5", headers=auth)
  assert upstream["opened"][0].closed and downloads.slots._active == {}


def test_expired_classeviva_session_logs_in_again(client, auth, upstream):
  upstream["responses"] += [FakeResponse(status=401), FakeResponse()]
  r = client.get("/bacheca/CF/12/allegati/1", headers=auth)
  assert r.status_code == 200 and upstream["relogins"] == 1 and len(upstream["urls"]) == 2


def test_upstream_errors(client, auth, upstream):
  upstream["responses"] += [FakeResponse(status=404), FakeResponse(status=500)]
  assert client.get("/didattica/5", headers=auth).json()["code"] == "file_not_found"
  r = client.get("/didattica/5", headers=auth)
  assert r.status_code == 502 and r.json()["code"] == "classeviva_error"
  assert downloads.slots._active == {}


def test_material_link_text_and_listing(client, auth, upstream):
  def as_json(payload):
    return FakeResponse(chunks=[json.dumps(payload).encode()], headers={"content-type": "application/json"})

  upstream["responses"] += [
    as_json({"item": {"link": "https://example.org/esercizi"}}),
    as_json({"item": {"text": "Leggere pag. 12"}}),
    as_json({"item": {"link": "javascript:alert(1)"}}),
    as_json({"didacticts": []}),  # l'elenco intero al posto del file: non scaricabile
  ]
  assert client.get("/didattica/1", headers=auth).json() == {"tipo": "link", "url": "https://example.org/esercizi"}
  assert client.get("/didattica/2", headers=auth).json() == {"tipo": "testo", "testo": "Leggere pag. 12"}
  for _ in range(2):
    r = client.get("/didattica/3", headers=auth)
    assert r.status_code == 502 and r.json()["code"] == "not_downloadable"
  assert downloads.slots._active == {}


def test_parallel_downloads_are_limited(client, auth, upstream, settings):
  busy = [downloads.slots.take("s123x", settings.max_parallel_downloads) for _ in range(settings.max_parallel_downloads)]
  r = client.get("/didattica/5", headers=auth)
  assert r.status_code == 429 and r.json()["code"] == "too_many_downloads"
  downloads.slots.release("s123x", busy[0])
  upstream["responses"].append(FakeResponse())
  assert client.get("/didattica/5", headers=auth).status_code == 200


def test_stale_slots_expire(monkeypatch):
  slots = downloads._Slots()
  now = [1000.0]
  monkeypatch.setattr(downloads.time, "monotonic", lambda: now[0])
  slots.take("u", 1)
  with pytest.raises(Exception):
    slots.take("u", 1)
  now[0] += downloads._Slots.STALE_SECONDS + 1  # client sparito senza chiudere: lo slot si libera da solo
  slots.take("u", 1)


def test_redirects_only_to_classeviva():
  assert downloads._trusted("https://cdndoc.spaggiari.eu/file.pdf")
  assert downloads._trusted("https://web.spaggiari.eu/x")
  assert not downloads._trusted("http://cdndoc.spaggiari.eu/file.pdf")
  assert not downloads._trusted("https://spaggiari.eu.evil.com/file.pdf")
  assert not downloads._trusted("https://evilspaggiari.eu/file.pdf")


def test_filenames():
  assert downloads.safe_filename("../../etc/passwd") == "etcpasswd"
  assert downloads.safe_filename("a\x00b\nc.pdf") == "abc.pdf"
  assert downloads.safe_filename("  ") is None
  header = downloads.content_disposition('verifica "finale" è.pdf')
  assert header.startswith('attachment; filename="verifica finale .pdf"')
  assert "filename*=UTF-8''verifica%20%22finale%22%20%C3%A8.pdf" in header
