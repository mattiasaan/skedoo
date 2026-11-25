"""Variazioni d'orario (cambi aula, entrate posticipate, uscite anticipate) lette dal file locale
prodotto dal flusso bacheca -> OCR (scripts/bacheca_fetch/ocr_changes.py).

Formato del file `data/dati-bacheca/data.json`:

  {"aggiornato_il": "...", "giorni": [{"data_iso": "2026-11-17", "entrate": [...], "uscite": [...],
    "senza_lezioni_pomeridiane": [...], "cambi_aula": [...]}]}

È accettato anche il formato precedente con un solo giorno (le stesse chiavi al primo livello).
"""
import json
import re
from datetime import date
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from .config import get_settings
from .errors import AppError
from .schedules import SLOTS as GRID
from .school import require_galilei
from .security import current_session

router = APIRouter(prefix="/changes", tags=["Modifiche"], dependencies=[Depends(current_session), Depends(require_galilei)])

AFTERNOON_START = "14:30"  # prima ora pomeridiana: "senza lezioni pomeridiane" annulla da qui in poi


class ChangeOut(BaseModel):
  id: str
  data: str
  ora: int | None = None  # prima ora coinvolta (numero d'ora della griglia)
  # ore coinvolte: per un cambio aula quelle in cui vale, per entrate/uscite/pomeriggio quelle annullate
  ore: list[int] = Field(default_factory=list)
  tipo: str  # cambio_aula | entrata_posticipata | uscita_anticipata | senza_lezioni_pomeridiane
  testo: str
  nuova_aula: str | None = None
  orario: str | None = None


# ---------- lettura del file ----------
@lru_cache(maxsize=4)
def _load_data(path: str, modified_ns: int) -> dict:
  """Il timestamp fa parte della chiave: quando lo script riscrive il file la cache si rinnova da sola."""
  with Path(path).open(encoding="utf-8") as file:
    payload = json.load(file)
  if not isinstance(payload, dict):
    raise ValueError("Il file dati-bacheca deve contenere un oggetto JSON")
  return payload


def load_board_data() -> dict:
  path = get_settings().data_dir / "dati-bacheca" / "data.json"
  try:
    return _load_data(str(path), path.stat().st_mtime_ns)
  except (OSError, json.JSONDecodeError, ValueError) as exc:
    raise AppError(503, "changes_unavailable", "Dati delle modifiche temporaneamente non disponibili") from exc


def board_days(payload: dict) -> list[dict]:
  """Giorni presenti nel file, sia nel formato a più giorni sia in quello vecchio a giorno singolo."""
  days = payload.get("giorni")
  if isinstance(days, list):
    return [day for day in days if isinstance(day, dict)]
  return [payload]


# ---------- ore della griglia ----------
def _minutes(value: str | None) -> int | None:
  match = re.fullmatch(r"(\d{1,2})[:.](\d{2})", (value or "").strip())
  return int(match[1]) * 60 + int(match[2]) if match else None


SLOTS = [(_minutes(start), _minutes(end)) for start, end in GRID]


def hours_between(start: str | None, end: str | None) -> list[int]:
  """Ore della griglia che si sovrappongono all'intervallo, es. "09:50 - 11:45" -> [3, 4]."""
  begin, finish = _minutes(start), _minutes(end)
  if begin is None or finish is None or finish <= begin:
    return []
  return [index + 1 for index, (slot_start, slot_end) in enumerate(SLOTS) if slot_start < finish and begin < slot_end]


def first_hour_after_entrance(time_value: str | None) -> int | None:
  """Entrata alle 09:50: la prima ora seguita è la 3ª (le ore già finite sono saltate)."""
  minutes = _minutes(time_value)
  if minutes is None:
    return None
  return next((index + 1 for index, (_, slot_end) in enumerate(SLOTS) if slot_end > minutes), None)


def first_hour_after_exit(time_value: str | None) -> int | None:
  """Uscita alle 12:35: la prima ora persa è la 6ª (quella che inizia da quell'orario in poi)."""
  minutes = _minutes(time_value)
  if minutes is None:
    return None
  return next((index + 1 for index, (slot_start, _) in enumerate(SLOTS) if slot_start >= minutes), None)


FIRST_AFTERNOON_HOUR = first_hour_after_exit(AFTERNOON_START)  # 8ª
LAST_HOUR = len(SLOTS)


def hours_lost_entrance(time_value: str | None) -> list[int]:
  """Ore saltate con un'entrata posticipata. Al mattino si saltano le ore precedenti (09:50 -> [1, 2]);
  nel pomeriggio la mattina si fa tutta e si saltano solo le ore pomeridiane prima dell'entrata (15:20 -> [8])."""
  first = first_hour_after_entrance(time_value)
  if first is None:
    return []
  start = FIRST_AFTERNOON_HOUR if first > FIRST_AFTERNOON_HOUR else 1
  return list(range(start, first))


def hours_lost_exit(time_value: str | None) -> list[int]:
  """Ore perse con un'uscita anticipata. Uscendo al mattino si perdono solo le ore del mattino rimaste e il
  pomeriggio resta (11:45 -> [5, 6, 7]); uscendo nel pomeriggio si perde il resto della giornata."""
  first = first_hour_after_exit(time_value)
  if first is None:
    return []
  end = FIRST_AFTERNOON_HOUR - 1 if first < FIRST_AFTERNOON_HOUR else LAST_HOUR
  return list(range(first, end + 1))


# ---------- classi ----------
def _class_key(value: str) -> str:
  return re.sub(r"\s+", "", str(value or "")).upper()


def validate_class(classe: str) -> str:
  normalized = _class_key(classe)
  if not re.fullmatch(r"[A-Z0-9]+(?:/[A-Z0-9]+)?", normalized) or len(normalized) > 16:
    raise AppError(422, "invalid_class", "Classe non valida")
  return normalized


def class_aliases(value: str) -> set[str]:
  """Classe articolata del cartellone: '3C/T' vale per 3C, 3T (e per '3C/T' stessa)."""
  key = _class_key(value)
  match = re.fullmatch(r"(\d+)([A-Z]+(?:/[A-Z]+)+)", key)
  if not match:
    return {key}
  return {key} | {match[1] + section for section in match[2].split("/")}


def _class_matches(classes, selected: str) -> bool:
  return isinstance(classes, list) and any(selected in class_aliases(item) for item in classes)


# ---------- costruzione delle modifiche ----------
def _entrances_and_exits(day: dict, classe: str) -> list[ChangeOut]:
  result = []
  data = day.get("data_iso") or ""
  # `ora`: prima ora seguita (entrata) o prima ora persa (uscita); `ore`: tutte le ore annullate
  for key, change_type, label, hour_of, lost_of in (
    ("entrate", "entrata_posticipata", "Entrata", first_hour_after_entrance, hours_lost_entrance),
    ("uscite", "uscita_anticipata", "Uscita", first_hour_after_exit, hours_lost_exit),
  ):
    for index, entry in enumerate(day.get(key) or []):
      if not isinstance(entry, dict) or not _class_matches(entry.get("classi"), classe):
        continue
      time_value = entry.get("ora")
      note = (entry.get("note") or "").strip()
      result.append(ChangeOut(
        id=f"{key}-{data}-{entry.get('unit_id', index)}", data=data, ora=hour_of(time_value), ore=lost_of(time_value),
        tipo=change_type, testo=f"{label} alle {time_value}" + (f". {note}" if note else ""),
      ))
  for index, entry in enumerate(day.get("senza_lezioni_pomeridiane") or []):
    if not isinstance(entry, dict) or not _class_matches(entry.get("classi"), classe):
      continue
    hour = FIRST_AFTERNOON_HOUR
    note = (entry.get("note") or "").strip()
    result.append(ChangeOut(
      id=f"pomeriggio-{data}-{entry.get('unit_id', index)}", data=data, ora=hour,
      ore=list(range(hour, LAST_HOUR + 1)) if hour else [],
      tipo="senza_lezioni_pomeridiane", testo="Nessuna lezione pomeridiana" + (f". {note}" if note else ""),
    ))
  return result


def _room_changes(day: dict, classe: str) -> list[ChangeOut]:
  result = []
  data = day.get("data_iso") or ""
  for index, entry in enumerate(day.get("cambi_aula") or []):
    if not isinstance(entry, dict):
      continue
    # nelle righe successive del pannello la classe non è stampata: l'OCR la deduce dalla riga precedente
    if classe not in class_aliases(entry.get("classe") or entry.get("classe_dedotta") or ""):
      continue
    room = entry.get("aula") or next(iter(entry.get("aule") or []), None)
    schedule = (entry.get("orario") or "").strip()
    start, _, end = schedule.partition("-")
    hours = hours_between(start, end)
    result.append(ChangeOut(
      id=f"aula-{data}-{entry.get('unit_id', index)}", data=data, ora=hours[0] if hours else None, ore=hours,
      tipo="cambio_aula", testo=f"Aula cambiata: {room}" if room else "Cambio aula",
      nuova_aula=room, orario=schedule or None,
    ))
  return result


def _sorted(items: list[ChangeOut]) -> list[ChangeOut]:
  return sorted(items, key=lambda item: (item.data, item.ora is None, item.ora or 0, item.id))


def build_changes(classe: str, requested: date | None = None, kinds: tuple[str, ...] = ("orari", "aule")) -> list[ChangeOut]:
  selected = validate_class(classe)
  items: list[ChangeOut] = []
  for day in board_days(load_board_data()):
    if requested is not None and day.get("data_iso") != requested.isoformat():
      continue
    if "orari" in kinds:
      items += _entrances_and_exits(day, selected)
    if "aule" in kinds:
      items += _room_changes(day, selected)
  return _sorted(items)


ClassQuery = Query(..., min_length=1, max_length=16)
DateQuery = Query(None, description="YYYY-MM-DD")


@router.get("", response_model=list[ChangeOut])
def get_changes(classe: str = ClassQuery, data: date | None = DateQuery):
  """Tutte le modifiche della classe (tutti i giorni presenti nel file, o solo `data`)."""
  return build_changes(classe, data)


@router.get("/entrate-uscite", response_model=list[ChangeOut])
def get_entrances_and_exits(classe: str = ClassQuery, data: date | None = DateQuery):
  return build_changes(classe, data, ("orari",))


@router.get("/cambi-aula", response_model=list[ChangeOut])
def get_room_changes(classe: str = ClassQuery, data: date | None = DateQuery):
  return build_changes(classe, data, ("aule",))
