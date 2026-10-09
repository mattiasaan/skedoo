"""JWT su tutti gli endpoint, rate limit, blocchi anti-abuso, header, configurazione di produzione."""
import base64
import json
from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt
from pydantic import ValidationError

from app.classeviva import store
from app.config import Settings
from app.main import app
from conftest import login

OPEN = {("POST", "/auth/login"), ("GET", "/health")}  # gli unici senza JWT


def all_routes():
  """(metodo, path) di tutti gli endpoint, letti da OpenAPI (non dipende da come FastAPI organizza i router)."""
  return [(m.upper(), p) for p, item in app.openapi()["paths"].items() for m in item]


def url(path):
  return path.replace("{class_id}", "1A")


# ---------- JWT obbligatorio ----------
def test_endpoint_discovery_is_not_empty():
  assert len(all_routes()) >= 8 and OPEN <= set(all_routes())  # se fosse vuoto i test qui sotto non controllerebbero niente


@pytest.mark.parametrize("method,path", [r for r in all_routes() if r not in OPEN])
def test_endpoint_rejects_missing_and_garbage_token(client, method, path):
  r = client.request(method, url(path))
  assert r.status_code == 401 and r.json()["code"] == "not_authenticated" and r.headers["www-authenticate"] == "Bearer"
  r = client.request(method, url(path), headers={"Authorization": "Bearer abc.def.ghi"})
  assert r.status_code == 401 and r.json()["code"] == "invalid_token"


def test_only_login_and_health_are_open(client):
  """Un endpoint nuovo senza JWT fa fallire questo test."""
  open_ = {(m, p) for m, p in all_routes() if client.request(m, url(p)).status_code != 401}
  assert open_ == OPEN


def make_token(settings, key=None, **over):
  now = datetime.now(timezone.utc)
  claims = {"sub": "S123X", "sid": "x", "iss": "skedoo", "aud": "skedoo", "iat": now, "exp": now + timedelta(hours=1), **over}
  return jwt.encode({k: v for k, v in claims.items() if v is not None}, key or settings.jwt_secret, algorithm="HS256")


@pytest.mark.parametrize("over", [
  {"exp": datetime.now(timezone.utc) - timedelta(minutes=1)},  # scaduto
  {"aud": "altra-app"}, {"iss": "altri"},
  {"aud": None}, {"iss": None}, {"iat": None}, {"sub": None}, {"sid": None},  # claim mancanti
])
def test_bad_token_claims_rejected(client, settings, over):
  r = client.get("/auth/me", headers={"Authorization": f"Bearer {make_token(settings, **over)}"})
  assert r.status_code == 401 and r.json()["code"] == "invalid_token"


def test_forged_tokens_rejected(client, settings):
  def bearer(t):
    return {"Authorization": f"Bearer {t}"}
  assert client.get("/auth/me", headers=bearer(make_token(settings, key="altro-segreto"))).json()["code"] == "invalid_token"
  b64 = lambda d: base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()
  now = int(datetime.now(timezone.utc).timestamp())
  claims = {"sub": "S123X", "sid": "x", "iss": "skedoo", "aud": "skedoo", "iat": now, "exp": now + 3600}
  alg_none = f'{b64({"alg": "none", "typ": "JWT"})}.{b64(claims)}.'
  assert client.get("/auth/me", headers=bearer(alg_none)).json()["code"] == "invalid_token"


def test_valid_signature_needs_a_live_session(client, settings):
  # firma corretta ma sessione sconosciuta (es. server riavviato): si deve rifare il login
  assert client.get("/auth/me", headers={"Authorization": f"Bearer {make_token(settings)}"}).json()["code"] == "session_expired"
  # sid di un altro utente + sub diverso: non deve funzionare
  login(client, "S1X")
  sid = next(iter(store._sessions))
  other = make_token(settings, sub="S2X", sid=sid)
  assert client.get("/auth/me", headers={"Authorization": f"Bearer {other}"}).json()["code"] == "session_expired"


# ---------- rate limit ----------
def test_user_rate_limit_is_per_user(client, settings, monkeypatch):
  monkeypatch.setattr(settings, "rate_limit_user", 3)
  a, b = login(client, "S1X"), login(client, "S2X")
  assert [client.get("/schedules/classes", headers=a).status_code for _ in range(4)] == [200, 200, 200, 429]
  r = client.get("/schedules/classes", headers=a)
  assert r.json()["code"] == "rate_limited" and int(r.headers["retry-after"]) >= 1
  assert client.get("/schedules/classes", headers=b).status_code == 200  # un altro utente non è toccato


def test_upstream_limit_is_stricter_than_user_limit(client, auth, settings, monkeypatch):
  monkeypatch.setattr(settings, "rate_limit_upstream", 2)
  assert [client.get(p, headers=auth).status_code for p in ("/grades", "/agenda", "/grades")] == [200, 200, 429]
  assert client.get("/schedules/classes", headers=auth).status_code == 200  # gli orari non chiamano ClasseViva


def test_ip_rate_limit_applies_to_everything_and_keeps_cors(client, settings, monkeypatch):
  monkeypatch.setattr(settings, "rate_limit_ip", 3)
  for _ in range(3):
    client.get("/health")
  r = client.get("/health", headers={"Origin": "http://localhost:5173"})
  assert r.status_code == 429 and "retry-after" in r.headers
  assert r.headers["access-control-allow-origin"] == "http://localhost:5173"  # il frontend riesce a leggere l'errore


def test_x_forwarded_for_is_ignored_unless_behind_trusted_proxy(client, settings, monkeypatch):
  monkeypatch.setattr(settings, "rate_limit_ip", 2)
  fake = lambda i: {"X-Forwarded-For": f"9.9.9.{i}"}
  assert [client.get("/health", headers=fake(i)).status_code for i in range(3)] == [200, 200, 429]  # non aggira il limite

  store._sessions.clear()
  from app.security import limiter
  limiter.clear()
  monkeypatch.setattr(settings, "trust_proxy_headers", True)
  hdr = lambda real: {"X-Forwarded-For": f"6.6.6.6, {real}"}  # la prima voce la scrive il client, l'ultima il proxy
  assert [client.get("/health", headers=hdr("1.1.1.1")).status_code for _ in range(3)] == [200, 200, 429]
  assert client.get("/health", headers=hdr("2.2.2.2")).status_code == 200  # un altro client reale


def test_login_attempts_limit(client, settings, monkeypatch):
  monkeypatch.setattr(settings, "login_attempts", 3)
  codes = [client.post("/auth/login", json={"username": "S1X", "password": "bad"}).status_code for _ in range(4)]
  assert codes == [401, 401, 401, 429]


def test_login_lock_after_too_many_wrong_passwords(client, settings, monkeypatch):
  monkeypatch.setattr(settings, "login_attempts", 100)
  monkeypatch.setattr(settings, "login_failures", 3)
  for _ in range(3):
    assert client.post("/auth/login", json={"username": "S1X", "password": "bad"}).status_code == 401
  r = client.post("/auth/login", json={"username": "S1X", "password": "good"})
  assert r.status_code == 429 and r.json()["code"] == "too_many_attempts"  # bloccato anche con la password giusta
  assert client.post("/auth/login", json={"username": "S2X", "password": "good"}).status_code == 200  # altro utente ok


def test_successful_login_resets_failures(client, settings, monkeypatch):
  monkeypatch.setattr(settings, "login_attempts", 100)
  monkeypatch.setattr(settings, "login_failures", 3)
  for _ in range(2):
    client.post("/auth/login", json={"username": "S1X", "password": "bad"})
  login(client, "S1X")
  for _ in range(2):
    assert client.post("/auth/login", json={"username": "S1X", "password": "bad"}).status_code == 401


# ---------- input, dimensioni, header ----------
def test_login_input_limits(client):
  bad = [{"username": "a" * 65, "password": "x"}, {"username": "a b", "password": "x"}, {"username": "a\nb", "password": "x"},
         {"username": "", "password": "x"}, {"username": "a", "password": "x" * 257}]
  assert all(client.post("/auth/login", json=b).status_code == 422 for b in bad)


def test_body_too_large(client):
  r = client.post("/auth/login", content=b"x" * 20000, headers={"Content-Type": "application/json"})
  assert r.status_code == 413 and r.json()["code"] == "payload_too_large"
  r = client.post("/auth/login", content=(b"x" * 100 for _ in range(3)), headers={"Content-Type": "application/json"})
  assert r.status_code == 413  # body "a pezzi" senza Content-Length: rifiutato


def test_security_headers_and_no_store(client, auth):
  r = client.get("/auth/me", headers=auth)
  assert r.headers["x-content-type-options"] == "nosniff" and r.headers["x-frame-options"] == "DENY"
  assert r.headers["cache-control"] == "no-store"  # dati personali: mai in cache condivise


def test_cors_only_for_configured_origins(client):
  assert client.get("/health", headers={"Origin": "http://localhost:5173"}).headers["access-control-allow-origin"] == "http://localhost:5173"
  assert "access-control-allow-origin" not in client.get("/health", headers={"Origin": "https://evil.example"}).headers


# ---------- configurazione ----------
GOOD = dict(environment="production", jwt_secret="x" * 48, schedule_source="db", database_url="postgresql://u:p@db/skedoo",
            cors_origins="https://app.example.com", allowed_hosts="api.example.com")


def prod(**over):
  return Settings(_env_file=None, **{**GOOD, **over})


def test_valid_production_config():
  assert prod().is_production


@pytest.mark.parametrize("over,msg", [
  ({"jwt_secret": "corto"}, "JWT_SECRET"), ({"schedule_source": "json"}, "SCHEDULE_SOURCE"),
  ({"database_url": None}, "DATABASE_URL"), ({"cors_origins": "*"}, "CORS_ORIGINS"), ({"allowed_hosts": "*"}, "ALLOWED_HOSTS"),
])
def test_production_refuses_unsafe_config(over, msg):
  with pytest.raises(ValidationError, match=msg):
    prod(**over)


def test_production_requires_explicit_secret_and_origins():
  for missing, msg in (("jwt_secret", "JWT_SECRET"), ("cors_origins", "CORS_ORIGINS")):
    with pytest.raises(ValidationError, match=msg):
      Settings(_env_file=None, **{k: v for k, v in GOOD.items() if k != missing})
