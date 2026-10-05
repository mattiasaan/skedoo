from typing import Dict
from pydantic import BaseModel
from .models import Lesson


class ScheduleResponse(BaseModel):
  id: str
  nome: str
  docente_coordinatore: str
  pomeriggio: bool
  giorni_attivi: list[str]
  orario: Dict[str, Dict[str, Lesson]]



class DayScheduleResponse(BaseModel):
  classe: str
  giorno: str
  orario: Dict[str, Lesson]