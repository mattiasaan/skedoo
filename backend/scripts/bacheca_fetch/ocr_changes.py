"""Dagli allegati della bacheca al file delle variazioni letto da GET /changes.

Flusso:
  1. fetch_bacheca.py salva le comunicazioni "Comunicazioni per <giorno>" e i loro allegati
     (immagini del cartellone) in board_matches.json;
  2. questo script passa ogni immagine all'OCR (helper/OCR/V4-AI, Qwen3-VL via Ollama);
  3. tiene solo le voci abbastanza affidabili e scrive data/dati-bacheca/data.json.

L'OCR gira in un processo separato (di default con lo stesso Python del backend, che ha opencv-python
e numpy in requirements.txt) e i risultati sono messi in cache per contenuto: un'immagine già letta
non si rilegge.

Avvio dalla directory ``backend``:

    python -m scripts.bacheca_fetch.ocr_changes

Variabili (ambiente o backend/.env):
  OCR_DIR                       cartella dell'OCR (default: ../helper/OCR/V4-AI)
  OCR_PYTHON                    interprete per l'OCR (default: quello corrente, cioè il venv del backend)
  OCR_TIMEOUT_SECONDS           tempo massimo per immagine (default 1800)
  BACHECA_OCR_MIN_AFFIDABILITA  alta (default) | media | bassa: voci meno affidabili vengono scartate
  CLASSVIVA_BOARD_OUTPUT        board_matches.json prodotto da fetch_bacheca.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import subprocess
import sys
import tempfile
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
DEFAULT_OCR_DIR = REPO_DIR / "helper" / "OCR" / "V4-AI"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
SCHEMA_VERSION = 2
LEVELS = {"bassa": 0, "media": 1, "alta": 2, "verificata": 3}
SECTIONS = ("entrate", "uscite", "senza_lezioni_pomeridiane", "cambi_aula")

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
  parser.add_argument("--ocr-dir", type=Path, default=Path(env.get("OCR_DIR") or DEFAULT_OCR_DIR))
  parser.add_argument("--ocr-python", default=env.get("OCR_PYTHON") or sys.executable)
  parser.add_argument("--timeout", type=int, default=int(env.get("OCR_TIMEOUT_SECONDS") or 1800))
  parser.add_argument("--min-affidabilita", choices=["alta", "media", "bassa"],
                      default=env.get("BACHECA_OCR_MIN_AFFIDABILITA") or "alta")
  parser.add_argument("--keep-past", action="store_true", help="non scartare i giorni già passati")
  return parser.parse_args(argv)


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


def subprocess_runner(ocr_dir: Path, python: str, timeout: int) -> OcrRunner:
  """Esegue `python main.py <immagine> --out <tmp>` nella cartella dell'OCR e restituisce il JSON prodotto."""
  main_script = ocr_dir / "main.py"
  if not main_script.is_file():
    raise OcrError(f"OCR non trovato: {main_script} (imposta OCR_DIR)")

  def run(image: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="skedoo-ocr-") as workdir:
      command = [python, str(main_script), str(image.resolve()), "--out", workdir]
      try:
        completed = subprocess.run(  # noqa: S603 - comando fisso, nessun input dall'utente
          command, cwd=ocr_dir, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
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
    runner = runner or subprocess_runner(args.ocr_dir, args.ocr_python, args.timeout)
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
