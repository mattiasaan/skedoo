"""Orari, variazioni e notifiche push riguardano una sola scuola (ITT "G. Galilei" di Bolzano): contengono i nomi dei
docenti e il contenuto della bacheca interna della scuola, quindi li vede solo chi è di quella scuola.

La scuola arriva dalla carta ClasseViva al login (`CvSession._school`). Se ClasseViva non l'ha restituita la scuola
è sconosciuta e l'accesso resta aperto: chiudere bloccherebbe gli studenti del Galilei ogni volta che la carta non
risponde, e un utente non può scegliere la scuola che ClasseViva gli attribuisce. Stessa regola del frontend
(`isGalileiSchool` in frontend/src/lib/session.js).
"""
import logging
import re
import unicodedata

from fastapi import Depends

from .classeviva import ActiveSession
from .errors import AppError
from .security import current_session

log = logging.getLogger("skedoo")


def _normalize(value) -> str:
  text = unicodedata.normalize("NFD", str(value or ""))
  text = "".join(c for c in text if unicodedata.category(c) != "Mn")
  return re.sub(r"\s+", " ", re.sub(r"[^A-Za-z0-9 ]", " ", text)).strip().upper()


def is_galilei(school: dict | None) -> bool | None:
  """True/False se la scuola è nota, None se ClasseViva non l'ha restituita."""
  if not school:
    return None
  name = _normalize(f"{school.get('dedica') or ''} {school.get('nome') or ''}")
  return "GALILEI" in name and _normalize(school.get("citta")) == "BOLZANO"


def require_galilei(session: ActiveSession = Depends(current_session)) -> None:
  if is_galilei(session._school) is False:
    raise AppError(403, "school_not_supported", "Orari e variazioni sono disponibili solo per l'ITT Galilei di Bolzano")
