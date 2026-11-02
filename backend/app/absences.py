from datetime import date

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from .classeviva import CvSession
from .errors import AppError
from .security import current_session, upstream_limit

router = APIRouter(prefix="/assenze", tags=["Assenze"], dependencies=[Depends(upstream_limit)])


class AbsenceOut(BaseModel):
  id: int | str | None
  data: str | None
  tipo: str
  ora: int | None = None
  giustificata: bool = False
  motivo: str | None = None
  ore: list[dict] = Field(default_factory=list)


class AbsencesOut(BaseModel):
  eventi: list[AbsenceOut]


def _events(raw) -> list[dict]:
  return raw.get("events", []) if isinstance(raw, dict) else (raw or [])


def build_absences(raw) -> AbsencesOut:
  result = []
  for item in _events(raw):
    code = item.get("evtCode")
    if code == "ABA0":
      kind = "assenza"
    elif code == "ABU0":
      kind = "ritardo_uscita"
    else:
      kind = "altro"
    result.append(AbsenceOut(
      id=item.get("evtId"), data=item.get("evtDate"), tipo=kind,
      ora=item.get("evtHPos"), giustificata=bool(item.get("isJustified")),
      motivo=item.get("justifReasonDesc"), ore=item.get("hoursAbsence") or [],
    ))
  return AbsencesOut(eventi=result)


@router.get("", response_model=AbsencesOut)
async def get_absences(
  da: date | None = Query(None, description="YYYY-MM-DD"),
  a: date | None = Query(None, description="YYYY-MM-DD"),
  session: CvSession = Depends(current_session),
):
  if (da is None) != (a is None):
    raise AppError(422, "invalid_range", "Specificare entrambe le date da e a")
  raw = await session.call("assenze_da_a", da.isoformat(), a.isoformat()) if da and a else await session.call("assenze")
  return build_absences(raw)
