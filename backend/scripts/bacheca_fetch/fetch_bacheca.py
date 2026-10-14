"""Scarica e filtra le comunicazioni della bacheca ClasseViva.

Le credenziali vengono lette da ``backend/.env``. Il file prodotto contiene
solo gli avvisi trovati e non contiene credenziali.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

DEFAULT_PATTERN = (
  r"\b(?:comunicazioni?|aggiornamento\s+comunicazione)\s+"
  r"(?:per|del|di)\b.*\b(?:lun|mar|mer|gio|ven|sab|dom)"
)
BACKEND_DIR = Path(__file__).resolve().parent.parent


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
  await user.accedi()
  board = await user.bacheca()
  if not isinstance(board, list) or not all(isinstance(entry, Mapping) for entry in board):
    raise RuntimeError("La risposta della bacheca ClasseViva non ha il formato atteso")
  return user, [dict(entry) for entry in board]


def _safe_filename(name: Any, fallback: str) -> str:
  filename = Path(str(name or "")).name
  return filename if filename not in {"", ".", ".."} else fallback


async def download_attachments(
  user: Any, matches: list[dict[str, Any]], output_dir: Path,
) -> int:
  """Scarica gli allegati dei match e aggiunge i percorsi locali al JSON."""
  downloaded = 0
  output_dir.mkdir(parents=True, exist_ok=True)
  try:
    from classeviva import eccezioni
  except ImportError as exc:
    raise RuntimeError("Dipendenza Classeviva.py non installata") from exc
  for match in matches:
    codice = match.get("evtCode")
    content_id = match.get("cntId")
    publication_id = match.get("pubId")
    attachments = match.get("attachments") or []
    if not isinstance(attachments, list):
      continue

    local_files: list[str] = []
    if not codice or not publication_id:
      raise RuntimeError("Match senza evtCode o pubId: impossibile scaricare gli allegati")
    try:
      await user.bacheca_leggi(str(codice), int(publication_id))
    except eccezioni.ErroreHTTP as exc:
      raise RuntimeError(
        f"Impossibile aprire la comunicazione {publication_id}: {exc.__class__.__name__}"
      ) from exc
    for position, attachment in enumerate(attachments, start=1):
      if not isinstance(attachment, Mapping):
        continue
      attachment_number = attachment.get("attachNum") or position
      filename = _safe_filename(attachment.get("fileName"), f"allegato_{attachment_number}")
      destination = output_dir / f"{content_id}_{attachment_number}_{filename}"
      temporary = destination.with_suffix(destination.suffix + ".tmp")
      content = await _download_attachment(
        user, codice, content_id, publication_id, attachment_number, filename,
      )
      temporary.write_bytes(content)
      temporary.replace(destination)
      local_files.append(str(destination))
      downloaded += 1
    match["downloaded_attachments"] = local_files
  return downloaded


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


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
  parser = argparse.ArgumentParser(description="Filtra comunicazioni dalla bacheca ClasseViva")
  parser.add_argument(
    "--pattern", default=os.environ.get("CLASSVIVA_BOARD_PATTERN", DEFAULT_PATTERN),
    help="Regex case-insensitive applicata a tutti i campi dell'avviso",
  )
  parser.add_argument(
    "--output", type=Path,
    default=Path(os.environ.get("CLASSVIVA_BOARD_OUTPUT", "data/board_matches.json")),
    help="File JSON locale di destinazione",
  )
  parser.add_argument(
    "--attachments-dir", type=Path,
    default=Path(os.environ.get("CLASSVIVA_BOARD_ATTACHMENTS", "data/board_attachments")),
    help="Cartella locale dove salvare gli allegati",
  )
  return parser.parse_args(argv)


async def main(argv: Sequence[str] | None = None) -> int:
  load_dotenv(BACKEND_DIR / ".env")
  args = parse_args(argv)
  username = os.environ.get("CLASSVIVA_USERNAME")
  password = os.environ.get("CLASSVIVA_PASSWORD")
  if not username or not password:
    print("Imposta CLASSVIVA_USERNAME e CLASSVIVA_PASSWORD nell'ambiente.", file=sys.stderr)
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
