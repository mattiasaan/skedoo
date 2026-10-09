import secrets
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
  """Tutte le impostazioni si possono cambiare da .env o variabili d'ambiente (es. JWT_SECRET=...)."""
  model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

  # production = l'app non parte se la configurazione non è sicura (vedi _check_production)
  environment: Literal["development", "production"] = "development"

  # --- JWT ---
  jwt_secret: str = Field(default_factory=lambda: secrets.token_urlsafe(48))  # casuale a ogni avvio se non impostato
  jwt_ttl_hours: int = 24 * 7

  # --- rete ---
  cors_origins: str = "http://localhost:5173,http://localhost:3000"  # indirizzi del frontend, separati da virgola
  allowed_hosts: str = "*"  # domini dell'API accettati (header Host)
  trust_proxy_headers: bool = False  # true solo dietro a un reverse proxy fidato: l'IP si legge da X-Forwarded-For

  # --- rate limit (richieste al minuto) ---
  rate_limit_ip: int = 300  # per IP, tutte le richieste (largo: a scuola molti studenti condividono l'IP)
  rate_limit_user: int = 60  # per utente, tutti gli endpoint
  rate_limit_upstream: int = 20  # per utente, in più, su voti e agenda (chiamano ClasseViva)
  login_attempts: int = 5  # tentativi di login al minuto per (IP, username)
  login_failures: int = 10  # password sbagliate in 15 minuti per (IP, username), poi blocco

  # --- orari ---
  schedule_source: Literal["json", "db"] = "json"  # json = file in data_dir (sviluppo), db = PostgreSQL
  data_dir: Path = BASE_DIR / "data"
  database_url: str | None = None  # es. postgresql://user:pass@localhost:5432/skedoo

  cache_ttl_seconds: int = 60  # per quanto si riusa una risposta di ClasseViva (per utente)
  timezone: str = "Europe/Rome"

  @property
  def origins(self) -> list[str]:
    return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

  @property
  def hosts(self) -> list[str]:
    return [h.strip() for h in self.allowed_hosts.split(",") if h.strip()] or ["*"]

  @property
  def is_production(self) -> bool:
    return self.environment == "production"

  @model_validator(mode="after")
  def _check_production(self):
    if not self.is_production:
      return self
    problems = []
    if "jwt_secret" not in self.model_fields_set or len(self.jwt_secret) < 32:
      problems.append("JWT_SECRET deve essere impostato (almeno 32 caratteri)")
    if self.schedule_source != "db" or not self.database_url:
      problems.append("SCHEDULE_SOURCE=db e DATABASE_URL sono obbligatori")
    if "cors_origins" not in self.model_fields_set or "*" in self.origins:
      problems.append("CORS_ORIGINS deve elencare le origini del frontend (niente '*')")
    if "*" in self.hosts:
      problems.append("ALLOWED_HOSTS deve elencare i domini dell'API (niente '*')")
    if problems:
      raise ValueError("Configurazione non valida per ENVIRONMENT=production:\n  - " + "\n  - ".join(problems))
    return self


@lru_cache
def get_settings() -> Settings:
  return Settings()
