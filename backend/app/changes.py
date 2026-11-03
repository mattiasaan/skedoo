import json
import re
from datetime import date
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from .config import get_settings
from .errors import AppError
from .security import current_session

router = APIRouter(prefix="/changes", tags=["Modifiche"], dependencies=[Depends(current_session)])


class ChangeOut(BaseModel):
  id: str
  data: str
  ora: int | None = None
  tipo: str
  testo: str
  nuova_aula: str | None = None
  orario: str | None = None


class ChangesOut(BaseModel):
  modifiche: list[ChangeOut]


@lru_cache
def _load_data(path: str, modified_ns: int) -> dict:
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


def _class_key(value: str) -> str:
  return re.sub(r"\s+", "", value).upper()


def _validate_class(classe: str) -> str:
  normalized = _class_key(classe)
  if not re.fullmatch(r"[A-Z0-9]+(?:/[A-Z0-9]+)?", normalized) or len(normalized) > 16:
    raise AppError(422, "invalid_class", "Classe non valida")
  return normalized


def _class_matches(classes: list[str], selected: str) -> bool:
  return any(_class_key(item) == selected for item in classes)


def _hour_number(time_value: str | None) -> int | None:
  starts = {"08:10": 1, "09:00": 2, "09:50": 3, "10:40": 4, "11:45": 5,
            "12:35": 6, "13:25": 7, "14:30": 8, "15:20": 9, "16:10": 10, "17:10": 11}
  return starts.get((time_value or "").strip())


def _date(payload: dict) -> str:
  return payload.get("data_iso") or ""


def _entrances_and_exits(payload: dict, classe: str) -> list[ChangeOut]:
  result = []
  for kind, entries, change_type, label in (
    ("entrate", payload.get("entrate", []), "entrata_posticipata", "Entrata"),
    ("uscite", payload.get("uscite", []), "uscita_anticipata", "Uscita"),
  ):
    for index, entry in enumerate(entries):
      if not _class_matches(entry.get("classi", []), classe):
        continue
      ora = entry.get("ora")
      note = entry.get("note") or ""
      testo = f"{label} alle {ora}" + (f". {note}" if note else "")
      result.append(ChangeOut(
        id=f"{kind}-{entry.get('unit_id', index)}", data=_date(payload),
        ora=_hour_number(ora), tipo=change_type, testo=testo,
      ))
  return result


def _room_changes(payload: dict, classe: str) -> list[ChangeOut]:
  result = []
  for index, entry in enumerate(payload.get("cambi_aula", [])):
    if _class_key(entry.get("classe", "")) != classe:
      continue
    room = entry.get("aula") or ((entry.get("aule") or [None])[0])
    schedule = entry.get("orario") or ""
    text = f"Aula cambiata: {room}" if room else "Cambio aula"
    result.append(ChangeOut(
      id=f"aula-{entry.get('unit_id', index)}", data=_date(payload),
      ora=_hour_number(schedule[:5]), tipo="cambio_aula", testo=text,
      nuova_aula=room, orario=schedule,
    ))
  return result


def _date_filter(items: list[ChangeOut], requested: date | None) -> list[ChangeOut]:
  return [item for item in items if requested is None or item.data == requested.isoformat()]


def build_changes(classe: str, requested: date | None = None) -> list[ChangeOut]:
  selected = _validate_class(classe)
  payload = load_board_data()
  return _date_filter(_entrances_and_exits(payload, selected) + _room_changes(payload, selected), requested)


def _response(items: list[ChangeOut]) -> ChangesOut:
  return ChangesOut(modifiche=sorted(items, key=lambda item: (item.data, item.ora is not None, item.ora or 0, item.id)))


@router.get("", response_model=list[ChangeOut])
def get_changes(
  classe: str = Query(..., min_length=1, max_length=16),
  data: date | None = Query(None, description="YYYY-MM-DD"),
):
  """Tutte le modifiche della classe, nel formato già consumato dal frontend."""
  return _response(build_changes(classe, data)).modifiche


@router.get("/entrate-uscite", response_model=list[ChangeOut])
def get_entrances_and_exits(
  classe: str = Query(..., min_length=1, max_length=16),
  data: date | None = Query(None, description="YYYY-MM-DD"),
):
  return _response(_date_filter(
    _entrances_and_exits(load_board_data(), _validate_class(classe)), data,
  )).modifiche


@router.get("/cambi-aula", response_model=list[ChangeOut])
def get_room_changes(
  classe: str = Query(..., min_length=1, max_length=16),
  data: date | None = Query(None, description="YYYY-MM-DD"),
):
  return _response(_date_filter(
    _room_changes(load_board_data(), _validate_class(classe)), data,
  )).modifiche
