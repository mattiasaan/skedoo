"""Prova tutti gli endpoint di un'API Skedoo già avviata.

  python scripts/smoke_test.py --username S123X                 (chiede la password)
  python scripts/smoke_test.py --username S123X --classe 1A --url http://localhost:8000
  python scripts/smoke_test.py --username S123X --rate-limit    (prova anche il rate limit: poi aspetta 1 minuto)

Variabili d'ambiente alternative: SKEDOO_URL, SKEDOO_USER, SKEDOO_PASSWORD.
Usa solo `requests` (già installato con Classeviva.py). Esce con codice 1 se qualcosa fallisce.
"""
import argparse
import getpass
import os
import sys
from datetime import date, timedelta

import requests

results = []


def check(name, ok, detail=""):
  results.append(ok)
  print(f"  {'OK  ' if ok else 'FAIL'} {name}" + (f"  -> {detail}" if detail and not ok else ""))
  return ok


def code(r):
  try:
    return r.json().get("code")
  except Exception:
    return None


def main():
  p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  p.add_argument("--url", default=os.getenv("SKEDOO_URL", "http://localhost:8000"))
  p.add_argument("--username", default=os.getenv("SKEDOO_USER"))
  p.add_argument("--password", default=os.getenv("SKEDOO_PASSWORD"))
  p.add_argument("--classe", help="classe da provare (default: la prima dell'elenco)")
  p.add_argument("--rate-limit", action="store_true", help="prova anche il rate limit (blocca l'utente per ~1 minuto)")
  a = p.parse_args()
  if not a.username:
    p.error("serve --username")
  password = a.password or getpass.getpass(f"Password di {a.username}: ")
  base = a.url.rstrip("/")
  s = requests.Session()

  def get(path, token=None, **kw):
    return s.get(base + path, headers={"Authorization": f"Bearer {token}"} if token else {}, timeout=60, **kw)

  def login():
    return s.post(base + "/auth/login", json={"username": a.username, "password": password}, timeout=60)

  print(f"Test su {base}\n\n[pubblico]")
  r = get("/health")
  check("GET /health -> 200", r.status_code == 200 and r.json().get("status") == "ok", r.text)

  print("\n[senza token: tutto deve dare 401]")
  for path in ["/auth/me", "/schedules/classes", "/schedules/1A", "/schedules/1A/today", "/grades", "/agenda"]:
    r = get(path)
    check(f"GET {path} -> 401", r.status_code == 401 and code(r) == "not_authenticated", f"{r.status_code} {r.text[:80]}")
  r = s.post(base + "/auth/logout", timeout=30)
  check("POST /auth/logout -> 401", r.status_code == 401, r.status_code)
  r = get("/auth/me", "token.finto.123")
  check("token falso -> 401 invalid_token", r.status_code == 401 and code(r) == "invalid_token", f"{r.status_code} {r.text[:80]}")

  print("\n[login]")
  r = s.post(base + "/auth/login", json={"username": a.username, "password": password + "_sbagliata"}, timeout=60)
  check("password sbagliata -> 401 invalid_credentials", r.status_code == 401 and code(r) == "invalid_credentials", f"{r.status_code} {r.text[:80]}")
  r = s.post(base + "/auth/login", json={"username": a.username}, timeout=30)
  check("body incompleto -> 422", r.status_code == 422, r.status_code)
  r = login()
  if not check("login corretto -> 200 con token", r.status_code == 200 and "access_token" in r.json(), f"{r.status_code} {r.text[:120]}"):
    print("\nSenza login non posso continuare."); return 1
  body = r.json()
  token = body["access_token"]
  check("risposta login: token_type, expires_in, utente", body.get("token_type") == "bearer" and body.get("expires_in", 0) > 0
        and {"id", "nome", "cognome"} <= set(body.get("utente", {})), body)

  print("\n[utente]")
  r = get("/auth/me", token)
  check("GET /auth/me -> 200 con id/nome/cognome", r.status_code == 200 and {"id", "nome", "cognome"} <= set(r.json()), r.text[:100])

  print("\n[orari]")
  r = get("/schedules/classes", token)
  classes = r.json() if r.status_code == 200 else []
  check("GET /schedules/classes -> lista non vuota", r.status_code == 200 and len(classes) > 0 and {"id", "nome"} <= set(classes[0]), r.text[:100])
  cid = a.classe or (classes[0]["id"] if classes else "1A")
  r = get(f"/schedules/{cid}", token)
  ok = r.status_code == 200 and r.json().get("id") == cid.upper() and isinstance(r.json().get("giorni"), list)
  check(f"GET /schedules/{cid} -> orario con giorni", ok, f"{r.status_code} {r.text[:100]}")
  if ok and r.json()["giorni"]:
    l = r.json()["giorni"][0]["lezioni"][0]
    check("lezione con inizio, fine, materia", {"inizio", "fine", "materia"} <= set(l), l)
  r = get(f"/schedules/{cid.lower()}", token)
  check(f"GET /schedules/{cid.lower()} (minuscolo) -> 200", r.status_code == 200, r.status_code)
  r = get(f"/schedules/{cid}/today", token)
  check(f"GET /schedules/{cid}/today -> 200", r.status_code == 200 and {"data", "attivo", "lezioni"} <= set(r.json()), r.text[:100])
  r = get("/schedules/ZZZ9", token)
  check("classe inesistente -> 404 class_not_found", r.status_code == 404 and code(r) == "class_not_found", f"{r.status_code} {r.text[:80]}")
  r = get("/schedules/1A;DROP", token)
  check("id classe con caratteri strani -> 422/404", r.status_code in (404, 422), r.status_code)

  print("\n[voti] (chiamano ClasseViva)")
  r = get("/grades", token)
  ok = r.status_code == 200 and {"anno", "materie", "media_generale"} <= set(r.json())
  check("GET /grades -> 200 con materie e media", ok, f"{r.status_code} {r.text[:120]}")
  if ok:
    print(f"       anno {r.json()['anno']}, {len(r.json()['materie'])} materie, media generale {r.json()['media_generale']}")
  r = get("/grades?periodo=1", token)
  check("GET /grades?periodo=1 -> 200", r.status_code == 200 and r.json().get("periodo") == 1, f"{r.status_code} {r.text[:80]}")
  r = get("/grades?anno=abc", token)
  check("GET /grades?anno=abc -> 422", r.status_code == 422, r.status_code)

  print("\n[agenda] (chiama ClasseViva)")
  r = get("/agenda", token)
  ok = r.status_code == 200 and isinstance(r.json().get("giorni"), list)
  check("GET /agenda (default) -> 200", ok, f"{r.status_code} {r.text[:120]}")
  if ok:
    print(f"       {len(r.json()['giorni'])} giorni con eventi nei prossimi 14")
  t = date.today()
  r = get(f"/agenda?da={t}&a={t}", token)
  check("GET /agenda di un solo giorno -> 200", r.status_code == 200, f"{r.status_code} {r.text[:80]}")
  r = get(f"/agenda?da={t + timedelta(days=5)}&a={t}", token)
  check("intervallo invertito -> 422 invalid_range", r.status_code == 422 and code(r) == "invalid_range", f"{r.status_code} {r.text[:80]}")
  r = get(f"/agenda?da={t}&a={t + timedelta(days=400)}", token)
  check("intervallo > 366 giorni -> 422 range_too_large", r.status_code == 422 and code(r) == "range_too_large", f"{r.status_code} {r.text[:80]}")
  r = get("/agenda?da=ieri", token)
  check("data non valida -> 422", r.status_code == 422, r.status_code)

  print("\n[logout]")
  r = s.post(base + "/auth/logout", headers={"Authorization": f"Bearer {token}"}, timeout=30)
  check("POST /auth/logout -> 204", r.status_code == 204, r.status_code)
  r = get("/auth/me", token)
  check("dopo il logout il token non vale più (401 session_expired)", r.status_code == 401 and code(r) == "session_expired", f"{r.status_code} {r.text[:80]}")

  if a.rate_limit:
    print("\n[rate limit] (80 richieste veloci)")
    token = login().json().get("access_token")
    codes = [get("/auth/me", token).status_code for _ in range(80)]
    r = get("/auth/me", token)
    check("superato il limite -> 429 con Retry-After", 429 in codes and r.status_code == 429 and "Retry-After" in r.headers, f"{set(codes)}")

  failed = results.count(False)
  print(f"\n{len(results) - failed}/{len(results)} controlli superati" + (f", {failed} FALLITI" if failed else " ✔"))
  return 1 if failed else 0


if __name__ == "__main__":
  try:
    sys.exit(main())
  except requests.ConnectionError:
    print("Impossibile contattare l'API: è avviata? (uvicorn app.main:app)")
    sys.exit(2)
