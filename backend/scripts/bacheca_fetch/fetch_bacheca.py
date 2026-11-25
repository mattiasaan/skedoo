"""Scarica e filtra le comunicazioni della bacheca ClasseViva.

Le credenziali vengono lette da ``backend/.env``. Il file prodotto contiene
solo gli avvisi trovati e non contiene credenziali.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dotenv import dotenv_values

DEFAULT_PATTERN = (
  r"\b(?:comunicazioni?|aggiornamento\s+comunicazione)\s+"
  r"(?:per|del|di)\b.*\b(?:lun|mar|mer|gio|ven|sab|dom)"
)
BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BACKEND_DIR / ".env"

log = logging.getLogger("skedoo.bacheca_fetch")


def _text(value: Any) -> str:
  """Rende ricercabili anche le bacheche con campi annidati."""
  if isinstance(value, Mapping):
    return " ".join(_text(v) for v in value.values())
  if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
    return " ".join(_text(v) for v in value)
  return "" if value is None else str(value)


def filter_board(entries: Sequence[Mapping[str, Any]], pattern: str) -> list[dict[str, Any]]:
  """Filtra gli avvisi senza distinguere tra maiuscole e minuscole."""
  # IGNORECASE vale anche per le regex personalizzate passate da CLI o .env.
  matcher = re.compile(pattern, re.IGNORECASE | re.UNICODE)
  return [dict(entry) for entry in entries if matcher.search(_text(entry))]


def save_matches(
  path: Path, matches: Sequence[Mapping[str, Any]], pattern: str = DEFAULT_PATTERN,
) -> None:
  """Scrive JSON in modo atomico per non lasciare un file parziale."""
  path.parent.mkdir(parents=True, exist_ok=True)
  temporary = path.with_suffix(path.suffix + ".tmp")
  payload = {
    "saved_at": datetime.now(UTC).isoformat(),
    "pattern": pattern,
    "count": len(matches),
    "matches": list(matches),
  }
  temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
  temporary.replace(path)


async def fetch_board(username: str, password: str) -> tuple[Any, list[dict[str, Any]]]:
  """Effettua il login e scarica la bacheca tramite Classeviva.py."""
  try:
    from classeviva import Utente
  except ImportError as exc:
    raise RuntimeError("Dipendenza Classeviva.py non installata") from exc

  user = Utente(username, password)
  try:
    await user.accedi()
    board = await user.bacheca()
  except (RuntimeError, OSError):
    raise
  except Exception as exc:  # eccezioni di Classeviva.py (password errata, errori HTTP...): mai le credenziali nel messaggio
    raise RuntimeError(f"ClasseViva ha rifiutato la richiesta ({exc.__class__.__name__})") from exc
  if not isinstance(board, list) or not all(isinstance(entry, Mapping) for entry in board):
    raise RuntimeError("La risposta della bacheca ClasseViva non ha il formato atteso")
  return user, [dict(entry) for entry in board]


def _safe_filename(name: Any, fallback: str) -> str:
  filename = Path(str(name or "")).name
  return filename if filename not in {"", ".", ".."} else fallback


def _destination(output_dir: Path, match: Mapping[str, Any], position: int, attachment: Mapping[str, Any]) -> Path:
  attachment_number = attachment.get("attachNum") or position
  filename = _safe_filename(attachment.get("fileName"), f"allegato_{attachment_number}")
  # anche cntId e attachNum arrivano da ClasseViva: il nome intero non deve poter uscire dalla cartella
  return output_dir / _safe_filename(f"{match.get('cntId')}_{attachment_number}_{filename}", filename)


async def download_attachments(
  user: Any, matches: list[dict[str, Any]], output_dir: Path,
) -> int:
  """Scarica gli allegati dei match e aggiunge i percorsi locali al JSON.

  Gli allegati già presenti sul disco non si riscaricano (il fetch gira ogni 15 minuti).
  Una comunicazione che non si riesce a scaricare viene registrata e saltata: non blocca le altre.
  Restituisce il numero di file scaricati in questo giro."""
  downloaded = 0
  output_dir.mkdir(parents=True, exist_ok=True)
  for match in matches:
    attachments = [a for a in match.get("attachments") or [] if isinstance(a, Mapping)]
    targets = [(position, attachment, _destination(output_dir, match, position, attachment))
               for position, attachment in enumerate(attachments, start=1)]
    missing = [target for target in targets if not (target[2].is_file() and target[2].stat().st_size > 0)]
    try:
      if missing:
        downloaded += await _download_match(user, match, missing)
    except RuntimeError as exc:
      log.error("%s", exc)
    match["downloaded_attachments"] = [str(path) for _, _, path in targets if path.is_file()]
  return downloaded


async def _download_match(user: Any, match: Mapping[str, Any], targets: list[tuple[int, Mapping, Path]]) -> int:
  try:
    from classeviva import eccezioni
  except ImportError as exc:
    raise RuntimeError("Dipendenza Classeviva.py non installata") from exc
  codice, content_id, publication_id = match.get("evtCode"), match.get("cntId"), match.get("pubId")
  if not codice or not publication_id:
    raise RuntimeError(f"Comunicazione senza evtCode o pubId ({match.get('cntTitle') or 'senza titolo'}): allegati saltati")
  try:
    await user.bacheca_leggi(str(codice), int(publication_id))  # apre la comunicazione: serve per scaricare
  except eccezioni.ErroreHTTP as exc:
    raise RuntimeError(f"Impossibile aprire la comunicazione {publication_id}: {exc.__class__.__name__}") from exc
  count = 0
  for position, attachment, destination in targets:
    attachment_number = attachment.get("attachNum") or position
    try:
      content = await _download_attachment(user, codice, content_id, publication_id, attachment_number, destination.name)
    except RuntimeError as exc:
      log.error("%s", exc)
      continue
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_bytes(content)
    temporary.replace(destination)
    count += 1
  return count


async def _download_attachment(
  user: Any,
  codice: Any,
  content_id: Any,
  publication_id: Any,
  attachment_number: Any,
  filename: str,
) -> bytes:
  """Prova gli identificativi REST usati dalle diverse versioni di ClasseViva.py."""
  try:
    from classeviva import eccezioni
  except ImportError as exc:
    raise RuntimeError("Dipendenza Classeviva.py non installata") from exc

  candidates = []
  if codice and content_id:
    candidates.append((str(codice), content_id))
  if codice and publication_id and publication_id != content_id:
    candidates.append((str(codice), publication_id))
  errors = []
  for candidate_code, candidate_id in candidates:
    try:
      return await user.bacheca_allega_(
        candidate_code, int(candidate_id), int(attachment_number),
      )
    except eccezioni.ErroreHTTP as exc:
      errors.append(f"{candidate_code}/{candidate_id}: {exc.__class__.__name__}")

  detail = ", ".join(errors) or "identificativi mancanti"
  raise RuntimeError(f"Impossibile scaricare l'allegato {filename} ({detail})")


def parse_args(
  argv: Sequence[str] | None = None, env: Mapping[str, str | None] | None = None,
) -> argparse.Namespace:
  env = env or {}
  parser = argparse.ArgumentParser(description="Filtra comunicazioni dalla bacheca ClasseViva")
  parser.add_argument(
    "--pattern", default=env.get("CLASSVIVA_BOARD_PATTERN") or DEFAULT_PATTERN,
    help="Regex case-insensitive applicata a tutti i campi dell'avviso",
  )
  parser.add_argument(
    "--output", type=Path,
    default=Path(env.get("CLASSVIVA_BOARD_OUTPUT") or "data/board_matches.json"),
    help="File JSON locale di destinazione",
  )
  parser.add_argument(
    "--attachments-dir", type=Path,
    default=Path(env.get("CLASSVIVA_BOARD_ATTACHMENTS") or "data/board_attachments"),
    help="Cartella locale dove salvare gli allegati",
  )
  return parser.parse_args(argv)


def _environment() -> dict[str, str | None]:
  """Unisce .env e ambiente reale; le variabili d'ambiente hanno precedenza."""
  values = {key: value for key, value in dotenv_values(ENV_FILE).items()}
  values.update({
    key: os.environ[key] for key in (
      "CLASSVIVA_USERNAME", "CLASSVIVA_PASSWORD", "CLASSVIVA_BOARD_PATTERN",
      "CLASSVIVA_BOARD_OUTPUT", "CLASSVIVA_BOARD_ATTACHMENTS",
    ) if key in os.environ
  })
  return values


async def main(argv: Sequence[str] | None = None) -> int:
  env = _environment()
  if not ENV_FILE.is_file() and not (env.get("CLASSVIVA_USERNAME") and env.get("CLASSVIVA_PASSWORD")):
    print(f"File .env non trovato: {ENV_FILE}", file=sys.stderr)
    return 2
  args = parse_args(argv, env)
  username = env.get("CLASSVIVA_USERNAME")
  password = env.get("CLASSVIVA_PASSWORD")
  if not username or not password:
    print(f"Imposta CLASSVIVA_USERNAME e CLASSVIVA_PASSWORD in {ENV_FILE}.", file=sys.stderr)
    return 2

  try:
    user, board = await fetch_board(username, password)
    matches = filter_board(board, args.pattern)
    attachments = await download_attachments(user, matches, args.attachments_dir)
    save_matches(args.output, matches, args.pattern)
  except (RuntimeError, OSError, TypeError, ValueError) as exc:
    print(f"Errore nel recupero della bacheca: {exc}", file=sys.stderr)
    return 1

  print(
    f"Scaricati {len(board)} avvisi; trovati {len(matches)}; "
    f"allegati scaricati {attachments}; salvati in {args.output}"
  )
  return 0


if __name__ == "__main__":
  raise SystemExit(asyncio.run(main()))