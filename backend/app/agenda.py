from collections import defaultdict
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from .classeviva import CvSession
from .config import get_settings
from .errors import AppError
from .security import current_session, upstream_limit

router = APIRouter(prefix="/agenda", tags=["Agenda"], dependencies=[Depends(upstream_limit)])

MAX_DAYS = 366
TIPI = {"AGHW": "compito", "AGNT": "annotazione"}  # il resto è "evento"


class EventOut(BaseModel):
  id: int
  tipo: str  # compito | annotazione | evento
  ora_inizio: str | None  # "10:30"; None se dura tutto il giorno
  ora_fine: str | None
  tutto_il_giorno: bool
  materia: str | None
  autore: str | None
  testo: str | None


class DayOut(BaseModel):
  data: str  # YYYY-MM-DD
  eventi: list[EventOut]  # prima quelli di tutto il giorno, poi per ora


class AgendaOut(BaseModel):
  giorni: list[DayOut]  # solo i giorni che hanno eventi, in ordine


def build_agenda(raw: list[dict]) -> AgendaOut:
  """Dal formato grezzo di ClasseViva a eventi raggruppati per giorno."""
  by_day: dict[str, list[EventOut]] = defaultdict(list)
  for r in raw:
    begin, end = r.get("evtDatetimeBegin") or "", r.get("evtDatetimeEnd") or ""
    full_day = bool(r.get("isFullDay"))
    # "2026-10-06T10:30:00+02:00": data e ora così come le scrive la scuola
    by_day[begin[:10]].append(EventOut(
      id=r.get("evtId") or 0, tipo=TIPI.get(r.get("evtCode"), "evento"), tutto_il_giorno=full_day,
      ora_inizio=None if full_day else begin[11:16] or None, ora_fine=None if full_day else end[11:16] or None,
      materia=r.get("subjectDesc") or None, autore=r.get("authorName") or None, testo=r.get("notes") or None,
    ))
  return AgendaOut(giorni=[
    DayOut(data=d, eventi=sorted(evs, key=lambda e: (e.ora_inizio or "", e.id))) for d, evs in sorted(by_day.items())
  ])


@router.get("", response_model=AgendaOut)
async def get_agenda(
  da: date | None = Query(None, description="YYYY-MM-DD (default: oggi)"),
  a: date | None = Query(None, description="YYYY-MM-DD (default: da + 13 giorni; per un solo giorno metti a = da)"),
  session: CvSession = Depends(current_session),
):
  """Eventi dell'agenda (compiti, annotazioni, eventi) raggruppati per giorno."""
  da = da or datetime.now(ZoneInfo(get_settings().timezone)).date()
  a = a or da + timedelta(days=13)
  if a < da:
    raise AppError(422, "invalid_range", "La data 'a' è precedente a 'da'")
  if (a - da).days > MAX_DAYS:
    raise AppError(422, "range_too_large", f"Intervallo massimo: {MAX_DAYS} giorni")
  return build_agenda(await session.call("agenda_da_a", da.isoformat(), a.isoformat()))
