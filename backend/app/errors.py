from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError


class AppError(Exception):
  """Errore con codice leggibile dal frontend. La risposta è {"code": "...", "message": "..."}."""

  def __init__(self, status: int, code: str, message: str, headers: dict | None = None):
    self.status, self.code, self.message, self.headers = status, code, message, headers or {}


def error_response(status: int, code: str, message: str, headers: dict | None = None) -> JSONResponse:
  headers = dict(headers or {})
  if status == 401:
    headers["WWW-Authenticate"] = "Bearer"
  return JSONResponse({"code": code, "message": message}, status_code=status, headers=headers)


def register_error_handlers(app: FastAPI) -> None:
  @app.exception_handler(AppError)
  async def _app_error(_: Request, e: AppError):
    return error_response(e.status, e.code, e.message, e.headers)

  @app.exception_handler(SQLAlchemyError)
  async def _db_error(_: Request, e: SQLAlchemyError):
    # i dettagli (query, host) restano nel log: al client non vanno mai
    import logging
    logging.getLogger("skedoo").error("Errore database: %s", e.__class__.__name__, exc_info=e)
    return error_response(503, "database_unavailable", "Servizio temporaneamente non disponibile")
