"""Manda una notifica push di prova ai dispositivi iscritti di una classe.

Sul Raspberry (da deploy/):

    docker compose exec api python -m scripts.send_test_push 5J            # solo l'ultimo dispositivo iscritto
    docker compose exec api python -m scripts.send_test_push 5J --tutti    # tutti i dispositivi della classe
    docker compose exec api python -m scripts.send_test_push --elenco      # classi con dispositivi iscritti

Senza --tutti la prova arriva solo al dispositivo che si è iscritto per ultimo (di solito il tuo):
i compagni della stessa classe non ricevono un messaggio finto. Non tocca `push_sent`, quindi le
variazioni vere partono comunque. Le iscrizioni scadute (404/410) vengono cancellate come nell'invio normale.
"""
import argparse
import json
import sys
from collections.abc import Callable

from py_vapid import Vapid
from pywebpush import webpush
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import db as appdb
from app.changes import validate_class
from app.config import get_settings
from app.errors import AppError
from app.push_sender import GONE, _deliver

TITLE = "Variazioni {classe} (prova)"
BODY = "Notifica di prova da Skedoo: se la vedi, le notifiche funzionano"


def list_classes() -> list[tuple[str, int]]:
  with Session(appdb.get_engine()) as db:
    rows = db.execute(select(appdb.PushSubscription.class_id, func.count())
                      .group_by(appdb.PushSubscription.class_id).order_by(appdb.PushSubscription.class_id))
    return [(class_id, count) for class_id, count in rows]


def send_test(class_id: str, everyone: bool = False, body: str = BODY, send: Callable = webpush) -> list[int | None]:
  """Stato di ogni invio: None = consegnata al servizio push, altrimenti il codice HTTP (0 = rete)."""
  s = get_settings()
  message = {"title": TITLE.format(classe=class_id), "body": body, "tag": "prova", "url": "./#home"}
  data = json.dumps(message, ensure_ascii=False)
  vapid = Vapid.from_string(private_key=s.vapid_private_key)
  with Session(appdb.get_engine()) as db, db.begin():
    query = (select(appdb.PushSubscription).where(appdb.PushSubscription.class_id == class_id)
             .order_by(appdb.PushSubscription.created_at.desc(), appdb.PushSubscription.id.desc()))
    subs = list(db.scalars(query if everyone else query.limit(1)))
    statuses = [_deliver(send, vapid, s.vapid_subject, sub.endpoint, sub.p256dh, sub.auth, data) for sub in subs]
    for sub, status in zip(subs, statuses):
      if status in GONE:
        db.delete(sub)
  return statuses


def describe(status: int | None) -> str:
  if status is None:
    return "consegnata al servizio push"
  if status in GONE:
    return f"iscrizione scaduta ({status}): cancellata, riattiva le notifiche dal Profilo"
  if status == 403:
    return "403: chiavi VAPID diverse da quelle dell'iscrizione, spegni e riaccendi le notifiche dal Profilo"
  if status == 0:
    return "errore di rete o di cifratura: dettagli in docker compose logs api"
  return f"il servizio push ha risposto {status}"


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(description="Notifica push di prova")
  parser.add_argument("classe", nargs="?", help="classe, es. 5J")
  parser.add_argument("--tutti", action="store_true", help="tutti i dispositivi della classe, non solo l'ultimo")
  parser.add_argument("--testo", default=BODY, help="testo della notifica")
  parser.add_argument("--elenco", action="store_true", help="mostra le classi con dispositivi iscritti")
  args = parser.parse_args(argv)

  if not get_settings().push_enabled:
    print("Notifiche push spente: mancano VAPID_PUBLIC_KEY / VAPID_PRIVATE_KEY o DATABASE_URL", file=sys.stderr)
    return 1
  if args.elenco or not args.classe:
    classes = list_classes()
    print("\n".join(f"{class_id}: {count} dispositivi" for class_id, count in classes) or "Nessun dispositivo iscritto")
    return 0
  try:
    class_id = validate_class(args.classe)
  except AppError:
    print(f"Classe non valida: {args.classe}", file=sys.stderr)
    return 1

  statuses = send_test(class_id, args.tutti, args.testo)
  if not statuses:
    print(f"Nessun dispositivo iscritto per la {class_id} (vedi --elenco)", file=sys.stderr)
    return 1
  for index, status in enumerate(statuses, 1):
    print(f"dispositivo {index}: {describe(status)}")
  return 0 if any(status is None for status in statuses) else 1


if __name__ == "__main__":
  raise SystemExit(main())
