"""Healthcheck del container API: GET /health in locale.

L'API accetta solo gli host di ALLOWED_HOSTS (TrustedHostMiddleware), quindi la richiesta usa il primo
host senza caratteri jolly. Codice di uscita 0 = sano.
"""
import os
import sys
import urllib.request


def main() -> int:
  hosts = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip() and "*" not in h]
  request = urllib.request.Request("http://127.0.0.1:8000/health", headers={"Host": hosts[0] if hosts else "localhost"})
  try:
    with urllib.request.urlopen(request, timeout=4) as response:  # noqa: S310 - URL fisso
      return 0 if response.status == 200 else 1
  except OSError as exc:
    print(f"healthcheck fallito: {exc}", file=sys.stderr)
    return 1


if __name__ == "__main__":
  raise SystemExit(main())
