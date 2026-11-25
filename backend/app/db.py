"""Database (PostgreSQL). Orari: `classes` 1 ── N `lessons`. Notifiche push: `push_subscriptions` e `push_sent`.
Schema in docs/db-schema.md."""
from datetime import datetime
from functools import lru_cache

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, UniqueConstraint, create_engine
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


class PushSubscription(Base):
  """Un dispositivo iscritto alle notifiche push delle variazioni di una classe.
  Solo i dati che servono a inviare: nessun username, la classe è l'unico legame con lo studente."""
  __tablename__ = "push_subscriptions"

  id: Mapped[int] = mapped_column(primary_key=True)
  endpoint: Mapped[str] = mapped_column(String(1024), unique=True)  # URL del servizio push del browser
  p256dh: Mapped[str] = mapped_column(String(128))  # chiave pubblica del browser (cifra il contenuto)
  auth: Mapped[str] = mapped_column(String(64))  # segreto condiviso con il browser
  class_id: Mapped[str] = mapped_column(String(16), index=True)  # "4A" (come in /changes?classe=)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
  last_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PushSent(Base):
  """Variazione già notificata a una classe: la stessa non parte due volte (riavvii, file riscritto dall'OCR).
  `change_key` cambia anche se cambia il testo: una variazione corretta dalla bacheca si notifica di nuovo."""
  __tablename__ = "push_sent"

  class_id: Mapped[str] = mapped_column(String(16), primary_key=True)
  change_key: Mapped[str] = mapped_column(String(64), primary_key=True)  # sha256 di id + contenuto
  data: Mapped[str] = mapped_column(String(10), index=True)  # giorno della variazione: le righe passate si cancellano
  sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


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
