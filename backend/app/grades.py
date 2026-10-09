from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from .classeviva import CvSession
from .config import get_settings
from .security import current_session, upstream_limit

router = APIRouter(prefix="/grades", tags=["Voti"], dependencies=[Depends(upstream_limit)])


class GradeOut(BaseModel):
  id: int
  data: str  # YYYY-MM-DD
  voto: str  # come lo mostra la scuola: "7+", "8½", "Ottimo". È quello da visualizzare
  valore: float | None  # numerico per i calcoli; None per i giudizi non numerici
  tipo: str | None  # Scritto / Orale / Pratico...
  periodo: str | None
  peso: float | None
  note: str | None
  colore: str | None  # green / red / blue, come ClasseViva
  annullato: bool


class SubjectOut(BaseModel):
  materia_id: int | None
  materia: str
  media: float | None  # None se non ci sono ancora voti numerici
  voti: list[GradeOut]  # dal più recente


class GradesOut(BaseModel):
  anno: str
  periodo: int | None
  media_generale: float | None
  materie: list[SubjectOut]  # in ordine alfabetico


def _num(v):
  return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _current_year() -> str:
  """Anno scolastico corrente come lo vuole classeviva.py: l'anno di inizio (settembre), "26" = 2026/27."""
  now = datetime.now(ZoneInfo(get_settings().timezone))
  return f"{(now.year if now.month >= 9 else now.year - 1) % 100:02d}"


def average(grades: list[GradeOut]) -> float | None:
  """Media pesata. Non fanno media i voti annullati, con peso 0 o non numerici ("Ottimo")."""
  counted = [g for g in grades if not g.annullato and g.valore is not None and g.peso != 0]
  total = sum(g.peso or 1 for g in counted)
  return round(sum(g.valore * (g.peso or 1) for g in counted) / total, 2) if counted else None


def build_grades(raw: list[dict], anno: str, periodo: int | None) -> GradesOut:
  """Dal formato grezzo di ClasseViva a voti raggruppati per materia, con le medie."""
  by_subject: dict[tuple, list[GradeOut]] = defaultdict(list)
  for r in raw:
    if periodo is not None and r.get("periodPos") != periodo:
      continue
    by_subject[(r.get("subjectId"), r.get("subjectDesc") or r.get("subjectCode") or "—")].append(GradeOut(
      id=r.get("evtId") or 0, data=r.get("evtDate") or "", voto=str(r.get("displayValue") or ""),
      valore=_num(r.get("decimalValue")), tipo=r.get("componentDesc") or None, periodo=r.get("periodDesc") or None,
      peso=_num(r.get("weightFactor")), note=r.get("notesForFamily") or None, colore=r.get("color") or None,
      annullato=bool(r.get("canceled")),
    ))
  materie = []
  for (subject_id, name), grades in sorted(by_subject.items(), key=lambda kv: kv[0][1]):
    grades.sort(key=lambda g: (g.data, g.id), reverse=True)
    materie.append(SubjectOut(materia_id=subject_id, materia=name, media=average(grades), voti=grades))
  medie = [m.media for m in materie if m.media is not None]
  generale = round(sum(medie) / len(medie), 2) if medie else None
  return GradesOut(anno=anno, periodo=periodo, media_generale=generale, materie=materie)


@router.get("", response_model=GradesOut)
async def get_grades(
  anno: str | None = Query(None, pattern=r"^\d{2}$", description="Anno di inizio, es. 26 = 2026/27 (default: quello corrente)"),
  periodo: int | None = Query(None, ge=1, description="Solo un periodo (1 = primo, ...)"),
  session: CvSession = Depends(current_session),
):
  """Voti raggruppati per materia, con la media di ogni materia e quella generale."""
  anno = anno or _current_year()
  return build_grades(await session.call("voti", anno), anno, periodo)
