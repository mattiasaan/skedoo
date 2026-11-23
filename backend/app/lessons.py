"""Registro di classe: le lezioni firmate in un giorno, con l'argomento scritto dal docente."""
import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from .classeviva import ActiveSession
from .config import get_settings
from .security import current_session, upstream_limit

router = APIRouter(prefix="/lezioni", tags=["Lezioni"], dependencies=[Depends(upstream_limit)])

# LSF0 lezione, LSC0/LSS0 compresenza (es. sostegno): stessa ora di un'altra lezione
COMPRESENZA = {"LSC0", "LSS0"}
# c'è chi scrive un poema: il testo arriva intero al frontend, che lo accorcia; il limite è solo una protezione
MAX_TOPIC_CHARS = 5000


class LessonOut(BaseModel):
  id: int | str | None
  ora: int | None  # posizione nella giornata (1 = prima ora), come la registra la scuola
  durata: int  # ore consecutive coperte da questa firma
  materia: str | None
  docente: str | None
  tipo: str | None  # "Lezione", "Orientamento", "Compresenza"...
  compresenza: bool = False
  argomento: str | None  # None se il docente non l'ha scritto


class LessonsOut(BaseModel):
  data: str  # YYYY-MM-DD
  lezioni: list[LessonOut]  # per ora, poi lezioni prima delle compresenze


def clean_topic(text) -> str | None:
  """Spazi e righe vuote ripuliti, a capo mantenuti; None se non c'è testo."""
  if not isinstance(text, str):
    return None
  text = text.replace("\r\n", "\n").replace("\r", "\n")
  text = re.sub(r"[ \t ]+", " ", text)
  text = re.sub(r" *\n *", "\n", text)
  text = re.sub(r"\n{3,}", "\n\n", text).strip()
  if len(text) > MAX_TOPIC_CHARS:
    text = text[:MAX_TOPIC_CHARS].rstrip() + "…"
  return text or None


def build_lessons(day: date, raw) -> LessonsOut:
  items = raw.get("lessons", []) if isinstance(raw, dict) else (raw or [])
  result = []
  for item in items:
    if not isinstance(item, dict):
      continue
    hour, duration = item.get("evtHPos"), item.get("evtDuration")
    result.append(LessonOut(
      id=item.get("evtId"),
      ora=hour if isinstance(hour, int) and not isinstance(hour, bool) else None,
      durata=duration if isinstance(duration, int) and not isinstance(duration, bool) and duration > 0 else 1,
      materia=item.get("subjectDesc") or None,
      docente=item.get("authorName") or None,
      tipo=item.get("lessonType") or None,
      compresenza=item.get("evtCode") in COMPRESENZA,
      argomento=clean_topic(item.get("lessonArg")),
    ))
  result.sort(key=lambda e: (e.ora if e.ora is not None else 99, e.compresenza))
  return LessonsOut(data=day.isoformat(), lezioni=result)


@router.get("", response_model=LessonsOut)
async def get_lessons(
  data: date | None = Query(None, description="YYYY-MM-DD (default: oggi, fuso Europe/Rome)"),
  session: ActiveSession = Depends(current_session),
):
  """Lezioni firmate nel giorno: compaiono solo dopo che il docente firma, l'argomento può mancare."""
  day = data or datetime.now(ZoneInfo(get_settings().timezone)).date()
  return build_lessons(day, await session.call("lezioni_giorno", day.isoformat()))
