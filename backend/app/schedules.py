"""Orari delle classi: da file JSON (sviluppo) o da PostgreSQL (produzione), con le stesse risposte."""
import json
import logging
import unicodedata
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Path as PathParam
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .db import Class, Lesson, get_engine
from .errors import AppError
from .security import current_session

log = logging.getLogger("skedoo")

GIORNI = ["lunedi", "martedi", "mercoledi", "giovedi", "venerdi", "sabato", "domenica"]  # come weekday() di Python
ETICHETTE = {"lunedi": "Lunedì", "martedi": "Martedì", "mercoledi": "Mercoledì", "giovedi": "Giovedì",
             "venerdi": "Venerdì", "sabato": "Sabato", "domenica": "Domenica"}
# Griglia oraria della scuola: inizio di ogni ora di lezione e durata (modificala se cambiano le campanelle)
SLOT_STARTS = ["08:10", "09:00", "09:50", "10:40", "11:45", "12:35", "13:25", "14:30", "15:20", "16:10", "17:10"]
SLOT_MINUTES = 50


# ---------- modelli delle risposte ----------
class LessonOut(BaseModel):
  ora: int | None  # numero d'ora (1 = 08:10); None se l'orario non è nella griglia
  inizio: str  # "08:10"
  fine: str  # "09:00"
  materia: str
  materia_completa: str | None = None
  docenti: list[str] = []
  aula: str | None = None


class DayOut(BaseModel):
  giorno: str  # "lunedi"
  etichetta: str  # "Lunedì"
  lezioni: list[LessonOut]


class ClassInfo(BaseModel):
  id: str
  nome: str
  docente_coordinatore: str | None = None
  pomeriggio: bool = False


class ClassOut(ClassInfo):
  giorni: list[DayOut]  # solo i giorni in cui la classe ha lezione


class TodayOut(DayOut):
  data: str  # YYYY-MM-DD, fuso Europe/Rome
  attivo: bool  # False se la classe oggi non ha lezione (es. domenica): `lezioni` è vuoto


# ---------- costruzione dei dati (usata sia dai JSON sia dal database) ----------
def normalize_day(value: str) -> str:
  """'Lunedì ' -> 'lunedi'"""
  s = unicodedata.normalize("NFD", value.strip().lower())
  return "".join(c for c in s if unicodedata.category(c) != "Mn")


def class_key(class_id: str) -> str:
  """'5 j' -> '5J': maiuscole/minuscole e spazi non contano."""
  return class_id.strip().upper().replace(" ", "")


def make_lesson(inizio: str, materia: str, materia_completa, docenti, aula) -> LessonOut:
  """Calcola numero d'ora e fine dalla griglia. Solleva ValueError se `inizio` non è "HH:MM"."""
  fine = (datetime.strptime(inizio, "%H:%M") + timedelta(minutes=SLOT_MINUTES)).strftime("%H:%M")
  ora = SLOT_STARTS.index(inizio) + 1 if inizio in SLOT_STARTS else None
  return LessonOut(ora=ora, inizio=inizio, fine=fine, materia=materia, materia_completa=materia_completa,
                 docenti=docenti, aula=aula)


def make_class(info: dict, active_days: list[str], lessons: dict[str, list[LessonOut]]) -> ClassOut:
  days = [DayOut(giorno=d, etichetta=ETICHETTE[d], lezioni=lessons.get(d, [])) for d in active_days]
  return ClassOut(giorni=days, **info)


# ---------- sorgente 1: file JSON ----------
def parse_class(item: dict) -> ClassOut:
  """Una classe dal formato dei file JSON. `orario` è facoltativo (classi_index.json non ce l'ha)."""
  orario = {normalize_day(d): slots for d, slots in (item.get("orario") or {}).items()}
  active = [normalize_day(d) for d in item.get("giorni_attivi") or orario]
  active = [d for d in dict.fromkeys(active) if d in ETICHETTE]
  lessons: dict[str, list[LessonOut]] = {}
  for day in active:
    for start, l in sorted(orario.get(day, {}).items()):
      if not l.get("materia"):  # righe senza materia: rumore dell'OCR
        continue
      docenti = list(dict.fromkeys(d.strip() for d in l.get("docenti") or [] if d and d.strip()))  # niente doppioni
      try:
        lessons.setdefault(day, []).append(make_lesson(start, l["materia"], l.get("materia_completa"), docenti, l.get("aula")))
      except ValueError:
        log.warning("Classe %s: orario non valido %r, lezione ignorata", item.get("id"), start)
  info = {"id": class_key(item["id"]), "nome": item["nome"], "docente_coordinatore": item.get("docente_coordinatore"),
          "pomeriggio": bool(item.get("pomeriggio"))}
  return make_class(info, active, lessons)


def load_json(data_dir: Path) -> dict[str, ClassOut]:
  """Legge classi_index.json, tutte_le_classi.json e classi/*.json (in quest'ordine: l'ultimo vince).
  Usata anche dallo script di importazione nel database."""
  files = [data_dir / "classi_index.json", data_dir / "tutte_le_classi.json", *sorted((data_dir / "classi").glob("*.json"))]
  classes: dict[str, ClassOut] = {}
  for f in files:
    if not f.is_file():
      continue
    try:
      data = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
      log.warning("File %s non leggibile: %s", f.name, e)
      continue
    items = [data] if isinstance(data, dict) and "id" in data else data.values() if isinstance(data, dict) else data
    for item in items:
      try:
        c = parse_class(item)
        classes[c.id] = c
      except (KeyError, TypeError, AttributeError) as e:
        log.warning("File %s: classe ignorata, formato non valido (%s)", f.name, e)
  return classes


class JsonStore:
  def __init__(self, data_dir: Path):
    self.classes = load_json(data_dir)

  def list(self) -> list[ClassInfo]:
    return [ClassInfo(**c.model_dump(exclude={"giorni"})) for _, c in sorted(self.classes.items())]

  def get(self, class_id: str) -> ClassOut | None:
    return self.classes.get(class_key(class_id))


# ---------- sorgente 2: PostgreSQL ----------
class DbStore:
  def list(self) -> list[ClassInfo]:
    with Session(get_engine()) as db:
      rows = db.scalars(select(Class).order_by(Class.id))
      return [ClassInfo(id=c.id, nome=c.nome, docente_coordinatore=c.docente_coordinatore, pomeriggio=c.pomeriggio)
              for c in rows]

  def get(self, class_id: str) -> ClassOut | None:
    with Session(get_engine()) as db:
      c = db.get(Class, class_key(class_id))
      if c is None:
        return None
      lessons: dict[str, list[LessonOut]] = {}
      for l in db.scalars(select(Lesson).where(Lesson.class_id == c.id).order_by(Lesson.inizio)):
        lessons.setdefault(l.giorno, []).append(make_lesson(l.inizio, l.materia, l.materia_completa, l.docenti, l.aula))
      info = {"id": c.id, "nome": c.nome, "docente_coordinatore": c.docente_coordinatore, "pomeriggio": c.pomeriggio}
      return make_class(info, c.giorni_attivi, lessons)


@lru_cache
def get_store() -> JsonStore | DbStore:
  s = get_settings()
  return DbStore() if s.schedule_source == "db" else JsonStore(s.data_dir)


# ---------- endpoint ----------
router = APIRouter(prefix="/schedules", tags=["Orario"], dependencies=[Depends(current_session)])

# Il parametro arriva dall'utente: formato stretto
ClassId = PathParam(pattern=r"^[A-Za-z0-9 ]{1,16}$", description="Id della classe, es. 1A (maiuscole e spazi non contano)")


def _get_or_404(class_id: str) -> ClassOut:
  c = get_store().get(class_id)
  if c is None:
    raise AppError(404, "class_not_found", "Classe non trovata")
  return c


@router.get("/classes", response_model=list[ClassInfo])
def list_classes():
  """Elenco delle classi, per il selettore del frontend."""
  return get_store().list()


@router.get("/{class_id}", response_model=ClassOut)
def get_schedule(class_id: str = ClassId):
  """Orario settimanale completo della classe."""
  return _get_or_404(class_id)


@router.get("/{class_id}/today", response_model=TodayOut)
def get_today(class_id: str = ClassId):
  """Orario di oggi (fuso Europe/Rome). Nei giorni senza lezione: `attivo=false` e `lezioni=[]`."""
  c = _get_or_404(class_id)
  now = datetime.now(ZoneInfo(get_settings().timezone))
  key = GIORNI[now.weekday()]
  day = next((d for d in c.giorni if d.giorno == key), None)
  return TodayOut(giorno=key, etichetta=ETICHETTE[key], lezioni=day.lezioni if day else [],
               data=now.date().isoformat(), attivo=day is not None)
