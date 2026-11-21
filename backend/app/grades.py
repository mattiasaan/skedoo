import logging
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from .classeviva import ActiveSession
from .config import get_settings
from .errors import AppError
from .security import current_session, upstream_limit

log = logging.getLogger("skedoo")

router = APIRouter(prefix="/grades", tags=["Voti"], dependencies=[Depends(upstream_limit)])


class GradeOut(BaseModel):
  id: int
  data: str  # YYYY-MM-DD
  voto: str  # come lo mostra la scuola: "7+", "8½", "Ottimo". È quello da visualizzare
  valore: float | None  # numerico per i calcoli; None per i giudizi non numerici
  tipo: str | None  # Scritto / Orale / Pratico...
  periodo: str | None  # descrizione del periodo, es. "Primo periodo"
  periodo_pos: int | None = None  # 1 = primo periodo, 2 = secondo...: serve al frontend per filtrare
  peso: float | None
  note: str | None
  colore: str | None  # green / red / blue, come ClasseViva
  annullato: bool
  fa_media: bool = True  # False se il docente l'ha segnato "non fa media" (noAverage di ClasseViva)


class SubjectOut(BaseModel):
  materia_id: int | None
  materia: str
  media: float | None  # None se non ci sono ancora voti numerici
  docenti: list[str] = Field(default_factory=list)  # da ClasseViva `materie`; vuota se non disponibile
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
  """Media pesata; ignora voti annullati, che non fanno media, non numerici e pesi non positivi."""
  counted = [g for g in grades if not g.annullato and g.fa_media and g.valore is not None and (g.peso is None or g.peso > 0)]
  total = sum(g.peso or 1 for g in counted)
  return round(sum(g.valore * (g.peso or 1) for g in counted) / total, 2) if counted else None


def _int(v):
  return v if isinstance(v, int) and not isinstance(v, bool) else None


def teachers_by_subject(raw) -> dict:
  """Da ClasseViva `materie` a {subjectId: ["NOME Docente", ...]}."""
  result = {}
  for subject in raw or []:
    if not isinstance(subject, dict):
      continue
    names = [t.get("teacherName") for t in subject.get("teachers") or [] if isinstance(t, dict) and t.get("teacherName")]
    result[subject.get("subjectId", subject.get("id"))] = list(dict.fromkeys(names))
  return result


def build_grades(raw: list[dict], anno: str, periodo: int | None, teachers: dict | None = None) -> GradesOut:
  """Dal formato grezzo di ClasseViva a voti raggruppati per materia, con le medie."""
  by_subject: dict[tuple, list[GradeOut]] = defaultdict(list)
  for r in raw:
    if periodo is not None and r.get("periodPos") != periodo:
      continue
    by_subject[(r.get("subjectId"), r.get("subjectDesc") or r.get("subjectCode") or "—")].append(GradeOut(
      id=r.get("evtId") or 0, data=r.get("evtDate") or "", voto=str(r.get("displayValue") or ""),
      valore=_num(r.get("decimalValue")), tipo=r.get("componentDesc") or None, periodo=r.get("periodDesc") or None,
      periodo_pos=_int(r.get("periodPos")), peso=_num(r.get("weightFactor")), note=r.get("notesForFamily") or None, colore=r.get("color") or None,
      annullato=bool(r.get("canceled")), fa_media=not r.get("noAverage"),
    ))
  materie = []
  for (subject_id, name), grades in sorted(by_subject.items(), key=lambda kv: kv[0][1]):
    grades.sort(key=lambda g: (g.data, g.id), reverse=True)
    materie.append(SubjectOut(materia_id=subject_id, materia=name, media=average(grades), voti=grades,
                              docenti=(teachers or {}).get(subject_id, [])))
  medie = [m.media for m in materie if m.media is not None]
  generale = round(sum(medie) / len(medie), 2) if medie else None
  return GradesOut(anno=anno, periodo=periodo, media_generale=generale, materie=materie)


@router.get("", response_model=GradesOut)
async def get_grades(
  anno: str | None = Query(None, pattern=r"^\d{2}$", description="Anno di inizio, es. 26 = 2026/27 (default: quello corrente)"),
  periodo: int | None = Query(None, ge=1, description="Solo un periodo (1 = primo, ...)"),
  session: ActiveSession = Depends(current_session),
):
  """Voti raggruppati per materia, con la media di ogni materia e quella generale."""
  anno = anno or _current_year()
  raw = await session.call("voti", anno)
  try:  # i docenti sono un "di più": se ClasseViva non li restituisce i voti arrivano comunque
    teachers = teachers_by_subject(await session.call("materie"))
  except AppError as e:
    log.info("Docenti delle materie non disponibili: %s", e.code)
    teachers = {}
  return build_grades(raw, anno, periodo, teachers)
