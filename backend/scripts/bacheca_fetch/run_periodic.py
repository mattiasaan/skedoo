"""Esegue periodicamente il fetch della bacheca ClasseViva.

Avvio dalla directory ``backend``:

    python -m scripts.bacheca_fetch.run_periodic

Configurazione tramite ambiente/.env:
``CLASSVIVA_USERNAME``, ``CLASSVIVA_PASSWORD`` e
``BACHECA_FETCH_INTERVAL_SECONDS`` (default 900).
"""
from __future__ import annotations

import asyncio
import logging
import os
import signal
from pathlib import Path

from . import fetch_bacheca

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


def _fetch_args() -> list[str]:
  output = Path(os.getenv("CLASSVIVA_BOARD_OUTPUT", str(DEFAULT_OUTPUT)))
  attachments = Path(os.getenv("CLASSVIVA_BOARD_ATTACHMENTS", str(DEFAULT_ATTACHMENTS)))
  return ["--output", str(output), "--attachments-dir", str(attachments)]


async def run() -> None:
  interval = _positive_seconds("BACHECA_FETCH_INTERVAL_SECONDS", 15 * 60)
  stop = _stop_event()
  run_on_start = os.getenv("BACHECA_FETCH_RUN_ON_START", "true").lower() not in {"0", "false", "no"}
  args = _fetch_args()

  if run_on_start:
    result = await fetch_bacheca.main(args)
    if result:
      log.error("Fetch iniziale fallito con codice %s; riprovo al prossimo ciclo", result)

  while True:
    try:
      await asyncio.wait_for(stop.wait(), timeout=interval)
      return
    except asyncio.TimeoutError:
      result = await fetch_bacheca.main(args)
      if result:
        log.error("Fetch fallito con codice %s; riprovo tra %s secondi", result, interval)


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
