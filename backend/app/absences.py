from datetime import date

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from .classeviva import ActiveSession
from .errors import AppError
from .security import current_session, upstream_limit
from .validation import check_date_range

router = APIRouter(prefix="/assenze", tags=["Assenze"], dependencies=[Depends(upstream_limit)])


# Codici evento di ClasseViva
TIPI = {"ABA0": "assenza", "ABR0": "ritardo", "ABR1": "ritardo", "ABU0": "uscita"}


class AbsenceOut(BaseModel):
  id: int | str | None
  data: str | None
  tipo: str  # assenza | ritardo | uscita | altro
  codice: str | None = None  # codice ClasseViva originale (ABA0, ABR0, ABR1, ABU0...)
  ora: int | None = None
  giustificata: bool = False
  motivo: str | None = None
  ore: list[dict] = Field(default_factory=list)


class SummaryOut(BaseModel):
  assenze: int = 0
  ritardi: int = 0
  uscite: int = 0
  da_giustificare: int = 0


class AbsencesOut(BaseModel):
  eventi: list[AbsenceOut]  # dal più recente
  riepilogo: SummaryOut


def _events(raw) -> list[dict]:
  return raw.get("events", []) if isinstance(raw, dict) else (raw or [])


def build_absences(raw) -> AbsencesOut:
  result = []
  for item in _events(raw):
    if not isinstance(item, dict):
      continue
    code = item.get("evtCode")
    result.append(AbsenceOut(
      id=item.get("evtId"), data=item.get("evtDate"), tipo=TIPI.get(code, "altro"), codice=code,
      ora=item.get("evtHPos"), giustificata=bool(item.get("isJustified")),
      motivo=item.get("justifReasonDesc"), ore=item.get("hoursAbsence") or [],
    ))
  result.sort(key=lambda e: e.data or "", reverse=True)
  summary = SummaryOut(
    assenze=sum(e.tipo == "assenza" for e in result),
    ritardi=sum(e.tipo == "ritardo" for e in result),
    uscite=sum(e.tipo == "uscita" for e in result),
    da_giustificare=sum(e.tipo != "altro" and not e.giustificata for e in result),
  )
  return AbsencesOut(eventi=result, riepilogo=summary)


@router.get("", response_model=AbsencesOut)
async def get_absences(
  da: date | None = Query(None, description="YYYY-MM-DD"),
  a: date | None = Query(None, description="YYYY-MM-DD"),
  session: ActiveSession = Depends(current_session),
):
  if (da is None) != (a is None):
    raise AppError(422, "invalid_range", "Specificare entrambe le date da e a")
  if da and a:
    check_date_range(da, a)
  raw = await session.call("assenze_da_a", da.isoformat(), a.isoformat()) if da and a else await session.call("assenze")
  return build_absences(raw)
