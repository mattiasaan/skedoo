"""Database degli orari (PostgreSQL): 2 tabelle, `classes` 1 ── N `lessons`. Schema in docs/db-schema.md."""
from functools import lru_cache

from sqlalchemy import JSON, Boolean, ForeignKey, String, UniqueConstraint, create_engine
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .config import get_settings


class Base(DeclarativeBase):
  pass


class Class(Base):
  """Una classe (es. 1A)."""
  __tablename__ = "classes"

  id: Mapped[str] = mapped_column(String(16), primary_key=True)  # "1A" (maiuscolo, senza spazi)
  nome: Mapped[str] = mapped_column(String(32))  # "1 A"
  docente_coordinatore: Mapped[str | None] = mapped_column(String(160))
  pomeriggio: Mapped[bool] = mapped_column(Boolean, default=False)
  giorni_attivi: Mapped[list] = mapped_column(JSON, default=list)  # ["lunedi", "martedi", ...] in ordine


class Lesson(Base):
  """Un'ora di lezione di una classe. L'ora di fine e il numero d'ora si calcolano dalla griglia della scuola."""
  __tablename__ = "lessons"
  __table_args__ = (UniqueConstraint("class_id", "giorno", "inizio"),)

  id: Mapped[int] = mapped_column(primary_key=True)
  class_id: Mapped[str] = mapped_column(ForeignKey("classes.id", ondelete="CASCADE"))
  giorno: Mapped[str] = mapped_column(String(10))  # "lunedi"
  inizio: Mapped[str] = mapped_column(String(5))  # "08:10"
  materia: Mapped[str] = mapped_column(String(200))
  materia_completa: Mapped[str | None] = mapped_column(String(300))
  docenti: Mapped[list] = mapped_column(JSON, default=list)  # ["ROSSI Mario", ...]
  aula: Mapped[str | None] = mapped_column(String(200))


def make_engine(url: str) -> Engine:
  u = make_url(url)
  if u.drivername in ("postgres", "postgresql"):  # driver psycopg 3
    u = u.set(drivername="postgresql+psycopg")
  return create_engine(u, pool_pre_ping=True)


@lru_cache
def get_engine() -> Engine:
  url = get_settings().database_url
  if not url:
    raise RuntimeError("DATABASE_URL non impostato")
  return make_engine(url)
