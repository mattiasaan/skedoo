"""Esegue periodicamente il fetch della bacheca ClasseViva.

Avvio dalla directory ``backend``:

    python -m scripts.bacheca_fetch.run_periodic

Ogni ciclo: scarica la bacheca (fetch_bacheca) e, se va a buon fine, legge con l'OCR le immagini
dei cartelloni e aggiorna data/dati-bacheca/data.json (ocr_changes).

Configurazione tramite ambiente/.env:
``CLASSVIVA_USERNAME``, ``CLASSVIVA_PASSWORD``,
``BACHECA_FETCH_INTERVAL_SECONDS`` (default 900) e ``BACHECA_OCR_ENABLED`` (default true);
per l'OCR vedi le variabili in ocr_changes.py.
"""
from __future__ import annotations

import asyncio
import logging
import os
import signal
from pathlib import Path

from . import fetch_bacheca, ocr_changes

BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = BACKEND_DIR / "data" / "bacheca_fetch" / "board_matches.json"
DEFAULT_ATTACHMENTS = BACKEND_DIR / "data" / "bacheca_fetch" / "attachments"

log = logging.getLogger("skedoo.bacheca_fetch")


def _positive_seconds(name: str, default: int) -> int:
  raw = os.getenv(name)
  if raw is None:
    return default
  try:
    value = int(raw)
  except ValueError as exc:
    raise ValueError(f"{name} deve essere un numero intero") from exc
  if value < 1:
    raise ValueError(f"{name} deve essere maggiore di zero")
  return value


def _stop_event() -> asyncio.Event:
  event = asyncio.Event()
  loop = asyncio.get_running_loop()

  def stop() -> None:
    log.info("Arresto richiesto")
    loop.call_soon_threadsafe(event.set)

  for signum in (signal.SIGINT, signal.SIGTERM):
    try:
      loop.add_signal_handler(signum, stop)
    except (NotImplementedError, RuntimeError):
      # Windows e alcuni event loop non espongono signal handler asincroni.
      signal.signal(signum, lambda *_: event.set())
  return event


def _enabled(name: str, default: str = "true") -> bool:
  return os.getenv(name, default).lower() not in {"0", "false", "no"}


def _fetch_args() -> list[str]:
  output = Path(os.getenv("CLASSVIVA_BOARD_OUTPUT", str(DEFAULT_OUTPUT)))
  attachments = Path(os.getenv("CLASSVIVA_BOARD_ATTACHMENTS", str(DEFAULT_ATTACHMENTS)))
  return ["--output", str(output), "--attachments-dir", str(attachments)]


async def cycle(args: list[str], with_ocr: bool) -> None:
  """Un giro completo: fetch della bacheca e, se riuscito, OCR dei cartelloni."""
  result = await fetch_bacheca.main(args)
  if result:
    log.error("Fetch fallito con codice %s; riprovo al prossimo ciclo", result)
    return
  if with_ocr:
    matches = args[args.index("--output") + 1]
    # l'OCR è lento (minuti per immagine) e sincrono: gira in un thread per non bloccare l'arresto
    code = await asyncio.to_thread(ocr_changes.main, ["--matches", matches])
    if code:
      log.error("Aggiornamento delle variazioni terminato con codice %s", code)


async def run() -> None:
  interval = _positive_seconds("BACHECA_FETCH_INTERVAL_SECONDS", 15 * 60)
  stop = _stop_event()
  args = _fetch_args()
  with_ocr = _enabled("BACHECA_OCR_ENABLED")

  if _enabled("BACHECA_FETCH_RUN_ON_START"):
    await cycle(args, with_ocr)

  while True:
    try:
      await asyncio.wait_for(stop.wait(), timeout=interval)
      return
    except asyncio.TimeoutError:
      await cycle(args, with_ocr)


def main() -> int:
  logging.basicConfig(
    level=os.getenv("BACHECA_FETCH_LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
  )
  try:
    asyncio.run(run())
  except ValueError as exc:
    log.error("%s", exc)
    return 2
  except KeyboardInterrupt:
    return 0
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
