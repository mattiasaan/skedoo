"""Controlli comuni sui parametri delle richieste."""
from datetime import date

from .errors import AppError

MAX_RANGE_DAYS = 366


def check_date_range(da: date, a: date, max_days: int = MAX_RANGE_DAYS) -> None:
  """Intervallo di date valido: `a` non prima di `da` e al massimo `max_days` giorni."""
  if a < da:
    raise AppError(422, "invalid_range", "La data 'a' è precedente a 'da'")
  if (a - da).days > max_days:
    raise AppError(422, "range_too_large", f"Intervallo massimo: {max_days} giorni")
