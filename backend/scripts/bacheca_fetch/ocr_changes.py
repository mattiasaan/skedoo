"""Dagli allegati della bacheca al file delle variazioni letto da GET /changes.

Flusso:
  1. fetch_bacheca.py salva le comunicazioni "Comunicazioni per <giorno>" e i loro allegati
     (immagini del cartellone) in board_matches.json;
  2. questo script passa ogni immagine all'OCR (helper/OCR/V5-Gemini, API Gemini);
  3. tiene solo le voci abbastanza affidabili e scrive data/dati-bacheca/data.json.

L'OCR gira in due modi:
  - servizio HTTP (container `ocr`, anche su un altro Raspberry): con OCR_URL impostato ogni immagine
    viene inviata a POST <OCR_URL>/ocr con il token OCR_TOKEN;
  - processo locale (sviluppo): senza OCR_URL si lancia helper/OCR/V5-Gemini/main.py con OCR_PYTHON
    (GEMINI_API_KEY e GEMINI_MODELS di backend/.env vengono passate al processo).
I risultati sono messi in cache per contenuto: un'immagine già letta non si rilegge.

Avvio dalla directory ``backend``:

    python -m scripts.bacheca_fetch.ocr_changes

Variabili (ambiente o backend/.env):
  OCR_URL                       servizio OCR, es. http://ocr:8090 (vuoto = processo locale)
  OCR_TOKEN                     token condiviso con il servizio OCR (obbligatorio con OCR_URL)
  OCR_DIR                       cartella dell'OCR (default: ../helper/OCR/V5-Gemini)
  GEMINI_API_KEY, GEMINI_MODELS chiave e modelli Gemini per il processo locale
  OCR_PYTHON                    interprete per l'OCR (default: quello corrente, cioè il venv del backend)
  OCR_TIMEOUT_SECONDS           tempo massimo per immagine (default 1800)
  BACHECA_OCR_MIN_AFFIDABILITA  alta (default) | media | bassa: voci meno affidabili vengono scartate
  CLASSVIVA_BOARD_OUTPUT        board_matches.json prodotto da fetch_bacheca.py
"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import logging
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Iterable, Mapping, Sequence
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from dotenv import dotenv_values

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = BACKEND_DIR.parent
ENV_FILE = BACKEND_DIR / ".env"
DEFAULT_MATCHES = BACKEND_DIR / "data" / "bacheca_fetch" / "board_matches.json"
DEFAULT_CACHE = BACKEND_DIR / "data" / "bacheca_fetch" / "ocr"
DEFAULT_OCR_DIR = REPO_DIR / "helper" / "OCR" / "V5-Gemini"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
SCHEMA_VERSION = 2
LEVELS = {"bassa": 0, "media": 1, "alta": 2, "verificata": 3}
SECTIONS = ("entrate", "uscite", "senza_lezioni_pomeridiane", "cambi_aula")
OCR_PROCESS_ENV = ("GEMINI_API_KEY", "GEMINI_MODELS")

log = logging.getLogger("skedoo.ocr_changes")

OcrRunner = Callable[[Path], dict]


class OcrError(RuntimeError):
  """Lettura di un'immagine fallita: si registra e si passa all'immagine successiva."""


# ---------- configurazione ----------
def environment() -> dict[str, str]:
  """backend/.env + variabili d'ambiente (queste hanno la precedenza)."""
  values = {key: value for key, value in dotenv_values(ENV_FILE).items() if value is not None}
  values.update(os.environ)
  return values


def parse_args(argv: Sequence[str] | None, env: Mapping[str, str]) -> argparse.Namespace:
  parser = argparse.ArgumentParser(description="Legge con l'OCR gli allegati della bacheca e aggiorna le variazioni")
  parser.add_argument("--matches", type=Path, default=Path(env.get("CLASSVIVA_BOARD_OUTPUT") or DEFAULT_MATCHES),
                      help="board_matches.json prodotto da fetch_bacheca.py")
  parser.add_argument("--output", type=Path, default=None,
                      help="file delle variazioni (default: DATA_DIR/dati-bacheca/data.json)")
  parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE, help="cache dei risultati OCR")
  parser.add_argument("--ocr-url", default=env.get("OCR_URL") or None, help="servizio OCR (default: OCR_URL)")
  parser.add_argument("--ocr-dir", type=Path, default=Path(env.get("OCR_DIR") or DEFAULT_OCR_DIR))
  parser.add_argument("--ocr-python", default=env.get("OCR_PYTHON") or sys.executable)
  parser.add_argument("--timeout", type=int, default=int(env.get("OCR_TIMEOUT_SECONDS") or 1800))
  parser.add_argument("--min-affidabilita", choices=["alta", "media", "bassa"],
                      default=env.get("BACHECA_OCR_MIN_AFFIDABILITA") or "alta")
  parser.add_argument("--keep-past", action="store_true", help="non scartare i giorni già passati")
  args = parser.parse_args(argv)
  args.ocr_token = env.get("OCR_TOKEN") or ""  # solo da ambiente: sulla riga di comando sarebbe visibile in `ps`
  # al processo locale dell'OCR: backend/.env non è nell'ambiente, quindi la chiave va passata esplicitamente
  args.ocr_env = {name: env[name] for name in OCR_PROCESS_ENV if env.get(name)}
  return args


def default_output() -> Path:
  # import qui: lo script resta usabile (e testabile) anche senza le variabili obbligatorie del backend
  from app.config import get_settings
  return get_settings().data_dir / "dati-bacheca" / "data.json"


# ---------- OCR ----------
def file_digest(path: Path) -> str:
  digest = hashlib.sha256()
  with path.open("rb") as file:
    for chunk in iter(lambda: file.read(1 << 20), b""):
      digest.update(chunk)
  return digest.hexdigest()


def write_json_atomic(path: Path, payload: Any) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  temporary = path.with_suffix(path.suffix + ".tmp")
  temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
  temporary.replace(path)


def subprocess_runner(ocr_dir: Path, python: str, timeout: int, extra_env: Mapping[str, str] | None = None) -> OcrRunner:
  """Esegue `python main.py <immagine> --out <tmp>` nella cartella dell'OCR e restituisce il JSON prodotto.
  `extra_env` si aggiunge all'ambiente del processo (es. GEMINI_API_KEY letta da backend/.env)."""
  main_script = ocr_dir / "main.py"
  process_env = {**os.environ, **(extra_env or {})}
  if not main_script.is_file():
    raise OcrError(f"OCR non trovato: {main_script} (imposta OCR_DIR)")

  def run(image: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="skedoo-ocr-") as workdir:
      command = [python, str(main_script), str(image.resolve()), "--out", workdir]
      try:
        completed = subprocess.run(  # noqa: S603 - comando fisso, nessun input dall'utente
          command, cwd=ocr_dir, env=process_env, capture_output=True, text=True, encoding="utf-8", errors="replace",
          timeout=timeout,
        )
      except subprocess.TimeoutExpired as exc:
        raise OcrError(f"OCR oltre il tempo massimo ({timeout}s) per {image.name}") from exc
      except OSError as exc:
        raise OcrError(f"Impossibile avviare l'OCR con {python}: {exc}") from exc
      result_file = Path(workdir) / f"{image.stem}.json"
      if completed.returncode != 0 or not result_file.is_file():
        tail = (completed.stdout + completed.stderr).strip().splitlines()[-3:]
        raise OcrError(f"OCR fallito per {image.name} (codice {completed.returncode}): {' | '.join(tail)}")
      return json.loads(result_file.read_text(encoding="utf-8"))

  return run


def http_runner(url: str, token: str, timeout: int) -> OcrRunner:
  """Invia l'immagine al servizio OCR (POST <url>/ocr) e restituisce il JSON prodotto.
  Il servizio può stare nello stesso compose, su un altro Raspberry in LAN o in un'altra rete (via VPN)."""
  parsed = urllib.parse.urlsplit(url)
  if parsed.scheme not in ("http", "https") or not parsed.hostname:
    raise OcrError(f"OCR_URL non valido: {url!r} (es. http://ocr:8090)")
  if len(token) < 32:
    raise OcrError("OCR_TOKEN mancante o troppo corto (almeno 32 caratteri, lo stesso del servizio OCR)")
  try:
    if parsed.scheme == "http" and ipaddress.ip_address(parsed.hostname).is_global:
      log.warning("OCR_URL punta a un IP pubblico in chiaro: usa una VPN (Tailscale) o https")
  except ValueError:
    pass  # nome host (es. "ocr" nel compose): niente da controllare
  endpoint = url.rstrip("/") + "/ocr"

  def run(image: Path) -> dict:
    request = urllib.request.Request(
      f"{endpoint}?{urllib.parse.urlencode({'nome': image.name})}", data=image.read_bytes(), method="POST",
      headers={"Authorization": f"Bearer {token}", "Content-Type": "application/octet-stream"},
    )
    try:
      with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - schema controllato sopra
        return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
      detail = exc.read(300).decode("utf-8", "replace").strip()
      raise OcrError(f"Servizio OCR: errore {exc.code} per {image.name}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
      raise OcrError(f"Servizio OCR non raggiungibile su {url}: {exc}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
      raise OcrError(f"Servizio OCR: risposta non valida per {image.name}") from exc

  return run


def make_runner(args: argparse.Namespace) -> OcrRunner:
  if args.ocr_url:
    return http_runner(args.ocr_url, args.ocr_token, args.timeout)
  return subprocess_runner(args.ocr_dir, args.ocr_python, args.timeout, getattr(args, "ocr_env", None))


def read_image(image: Path, runner: OcrRunner, cache_dir: Path) -> dict:
  """Risultato OCR dell'immagine, dalla cache se la stessa immagine è già stata letta."""
  cached = cache_dir / f"{file_digest(image)}.json"
  if cached.is_file():
    try:
      return json.loads(cached.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
      log.warning("Cache OCR illeggibile, rileggo %s", image.name)
  result = runner(image)
  if not isinstance(result, dict) or result.get("schema_versione") != SCHEMA_VERSION:
    raise OcrError(f"Risultato OCR di {image.name} in un formato non supportato")
  write_json_atomic(cached, result)
  return result


# ---------- dal risultato OCR al giorno di variazioni ----------
def _reliable(item: Mapping[str, Any], minimum: int) -> bool:
  return LEVELS.get(str(item.get("affidabilita")), -1) >= minimum


def _clean(item: Mapping[str, Any]) -> dict:
  """Solo i campi che servono al backend (niente ritagli, motivi, ecc.)."""
  keep = ("unit_id", "ora", "classi", "note", "classe", "classe_dedotta", "orario", "aula", "aule", "affidabilita")
  return {key: item[key] for key in keep if key in item and item[key] not in (None, "", [])}


def plausible_date(data_iso: str, published_at: str | None) -> bool:
  """Il cartellone riguarda i giorni vicini alla pubblicazione della comunicazione:
  una data lontana è quasi certamente letta male."""
  try:
    day = date.fromisoformat(data_iso)
    published = datetime.fromisoformat(str(published_at)).date()
  except (TypeError, ValueError):
    return False
  return published - timedelta(days=3) <= day <= published + timedelta(days=10)


def day_from_result(result: Mapping[str, Any], min_level: str, published_at: str | None = None) -> dict | None:
  """Voci affidabili di un'immagine. None se la data del cartellone non è sicura.

  La data vale se il titolo è abbastanza affidabile oppure se è coerente con la data di pubblicazione
  (l'OCR abbassa l'affidabilità del titolo, per esempio, quando non riesce a stabilire l'anno)."""
  minimum = LEVELS[min_level]
  source = result.get("_source")
  data_iso = result.get("data_iso")
  if not data_iso:
    log.warning("%s: data del cartellone non letta, immagine ignorata", source)
    return None
  title_ok = LEVELS.get(str(result.get("titolo_affidabilita")), -1) >= minimum
  if not title_ok and not plausible_date(data_iso, published_at):
    log.warning("%s: data %s incerta (titolo %s) e lontana dalla pubblicazione, immagine ignorata",
                source, data_iso, result.get("titolo_affidabilita"))
    return None
  day: dict[str, Any] = {"data_iso": data_iso}
  discarded = 0
  for section in SECTIONS:
    items = [item for item in result.get(section) or [] if isinstance(item, Mapping)]
    kept = [_clean(item) for item in items if _reliable(item, minimum)]
    discarded += len(items) - len(kept)
    day[section] = kept
  if discarded:
    log.info("%s: %s voci scartate perché sotto l'affidabilità %s", source, discarded, min_level)
  return day


def _merge_days(days: Iterable[dict]) -> dict:
  merged: dict[str, Any] = {}
  for day in days:
    merged.setdefault("data_iso", day["data_iso"])
    for section in SECTIONS:
      merged.setdefault(section, []).extend(day.get(section, []))
  return merged


def build_days(publications: Iterable[tuple[str, list[dict]]], today: date | None = None) -> list[dict]:
  """Un giorno per data. Se più comunicazioni riguardano la stessa data vale la più recente
  ("Aggiornamento comunicazione..." sostituisce la precedente); le immagini della stessa comunicazione si uniscono."""
  latest: dict[str, tuple[str, list[dict]]] = {}
  for published_at, days in publications:
    by_date: dict[str, list[dict]] = {}
    for day in days:
      by_date.setdefault(day["data_iso"], []).append(day)
    for data_iso, same_date in by_date.items():
      if data_iso not in latest or published_at >= latest[data_iso][0]:
        latest[data_iso] = (published_at, same_date)
  result = [_merge_days(days) for _, days in latest.values()]
  if today is not None:
    result = [day for day in result if day["data_iso"] >= today.isoformat()]
  return sorted(result, key=lambda day: day["data_iso"])


# ---------- comunicazioni scaricate ----------
def load_matches(path: Path) -> list[dict]:
  payload = json.loads(path.read_text(encoding="utf-8"))
  matches = payload.get("matches") if isinstance(payload, dict) else None
  if not isinstance(matches, list):
    raise ValueError(f"{path} non è un file prodotto da fetch_bacheca.py")
  return [match for match in matches if isinstance(match, dict)]


def images_of(match: Mapping[str, Any]) -> list[Path]:
  files = match.get("downloaded_attachments") or []
  images = []
  for name in files if isinstance(files, list) else []:
    path = Path(str(name))
    if path.suffix.lower() not in IMAGE_SUFFIXES:
      log.info("Allegato %s ignorato: l'OCR legge solo immagini", path.name)
    elif not path.is_file():
      log.warning("Allegato %s non trovato sul disco", path)
    else:
      images.append(path)
  return images


def collect(matches: Sequence[Mapping[str, Any]], runner: OcrRunner, cache_dir: Path, min_level: str) -> tuple[list, int]:
  """(comunicazioni con i giorni letti, numero di immagini fallite)."""
  publications = []
  failures = 0
  for match in matches:
    days = []
    published_at = str(match.get("pubDT") or "")
    for image in images_of(match):
      try:
        result = read_image(image, runner, cache_dir)
      except (OcrError, OSError, json.JSONDecodeError) as exc:
        failures += 1
        log.error("%s", exc)
        continue
      day = day_from_result(result, min_level, published_at)
      if day:
        days.append(day)
    if days:
      publications.append((published_at, days))
  return publications, failures


def run(args: argparse.Namespace, runner: OcrRunner | None = None, today: date | None = None) -> int:
  output = args.output or default_output()
  try:
    matches = load_matches(args.matches)
  except (OSError, ValueError, json.JSONDecodeError) as exc:
    log.error("Comunicazioni non leggibili: %s", exc)
    return 2
  try:
    runner = runner or make_runner(args)
  except OcrError as exc:
    log.error("%s", exc)
    return 2

  publications, failures = collect(matches, runner, args.cache_dir, args.min_affidabilita)
  days = build_days(publications, None if args.keep_past else today or date.today())
  if not days and failures:
    # nessuna lettura riuscita: meglio lasciare il file precedente che svuotarlo
    log.error("Nessuna immagine letta (%s errori): %s lasciato invariato", failures, output)
    return 1
  write_json_atomic(output, {
    "aggiornato_il": datetime.now(UTC).isoformat(timespec="seconds"),
    "affidabilita_minima": args.min_affidabilita,
    "giorni": days,
  })
  log.info("Variazioni salvate in %s: %s giorni (%s immagini non lette)", output, len(days), failures)
  return 1 if failures else 0


def main(argv: Sequence[str] | None = None) -> int:
  return run(parse_args(argv, environment()))


if __name__ == "__main__":
  logging.basicConfig(level=os.getenv("BACHECA_FETCH_LOG_LEVEL", "INFO").upper(),
                      format="%(asctime)s %(levelname)s %(name)s: %(message)s")
  raise SystemExit(main())
