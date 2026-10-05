from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class Lesson(BaseModel):
  materia: Optional[str] = None
  materia_completa: Optional[str] = None
  docenti: List[str] = Field(default_factory=list)
  aula: Optional[str] = None


class ClassSchedule(BaseModel):
  id: str
  nome: str
  docente_coordinatore: str
  pomeriggio: bool
  giorni_attivi: List[str]
  orario: Dict[str, Dict[str, Lesson]] = Field(default_factory=dict)