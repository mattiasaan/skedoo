"""Importa gli orari dai file JSON nel database PostgreSQL.

  python -m scripts.import_schedules                      # importa (crea le tabelle se mancano)
  python -m scripts.import_schedules --data-dir ../altri  # altra cartella di JSON
  python -m scripts.import_schedules --database-url postgresql://user:pass@host/skedoo

Legge classi_index.json, tutte_le_classi.json e classi/*.json (come la modalità json dell'API).
Si può rilanciare quante volte vuoi: per ogni classe nei file l'orario viene sostituito (nessun duplicato),
e tutto avviene in una transazione (se qualcosa fallisce non cambia niente).
Una classe senza orario (presente solo in classi_index.json) aggiorna nome e coordinatore ma NON cancella
le lezioni già nel database. Le classi che non sono nei file non vengono toccate.
"""
import argparse
import sys
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import Base, Class, Lesson, make_engine
from app.schedules import ClassOut, load_json


def import_classes(db: Session, classes: dict[str, ClassOut]) -> int:
  """Scrive le classi nel database (senza fare commit). Restituisce il numero di lezioni scritte."""
  written = 0
  for c in classes.values():
    row = db.get(Class, c.id) or Class(id=c.id)
    row.nome, row.docente_coordinatore, row.pomeriggio = c.nome, c.docente_coordinatore, c.pomeriggio
    row.giorni_attivi = [d.giorno for d in c.giorni]
    db.add(row)
    lessons = [(d.giorno, l) for d in c.giorni for l in d.lezioni]
    if lessons:  # solo se c'è un orario: altrimenti si tengono le lezioni già presenti
      db.flush()
      db.execute(delete(Lesson).where(Lesson.class_id == c.id))
      db.add_all(Lesson(class_id=c.id, giorno=g, inizio=l.inizio, materia=l.materia,
                        materia_completa=l.materia_completa, docenti=l.docenti, aula=l.aula) for g, l in lessons)
      written += len(lessons)
  return written


def main(argv: list[str] | None = None) -> int:
  p = argparse.ArgumentParser(description="Importa gli orari dai JSON nel database.")
  p.add_argument("--data-dir", type=Path, help="cartella dei JSON (default: DATA_DIR)")
  p.add_argument("--database-url", help="default: variabile DATABASE_URL")
  args = p.parse_args(argv)

  url = args.database_url or get_settings().database_url
  if not url:
    print("Errore: manca DATABASE_URL (variabile d'ambiente, .env o --database-url)", file=sys.stderr)
    return 2
  classes = load_json(args.data_dir or get_settings().data_dir)
  if not classes:
    print("Errore: nessuna classe trovata nei file JSON", file=sys.stderr)
    return 1

  engine = make_engine(url)
  Base.metadata.create_all(engine)
  with Session(engine) as db, db.begin():  # transazione unica: commit alla fine, rollback se c'è un errore
    lessons = import_classes(db, classes)
  print(f"Importate {len(classes)} classi e {lessons} lezioni.")
  return 0


if __name__ == "__main__":
  sys.exit(main())
