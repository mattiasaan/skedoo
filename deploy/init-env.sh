#!/bin/sh
# Crea deploy/.env da .env.example generando i segreti mancanti. Non sovrascrive mai un valore già impostato.
#   ./init-env.sh                      genera tutto
#   ./init-env.sh --ocr-token <token>  usa il token dell'altro Pi (installazione su due Raspberry)
set -eu
cd "$(dirname "$0")"

OCR_TOKEN_ARG=""
if [ "${1:-}" = "--ocr-token" ]; then
  OCR_TOKEN_ARG="${2:?manca il token dopo --ocr-token}"
  if [ "${#OCR_TOKEN_ARG}" -lt 32 ] || printf %s "$OCR_TOKEN_ARG" | grep -q '[^A-Za-z0-9_-]'; then
    echo "Token non valido: almeno 32 caratteri tra lettere, cifre, - e _" >&2
    exit 1
  fi
fi

umask 077
[ -f .env ] || cp .env.example .env
chmod 600 .env

secret() { od -An -N32 -tx1 /dev/urandom | tr -d ' \n'; }  # 64 caratteri esadecimali (sicuri negli URL)

fill() {  # fill NOME valore: imposta solo se vuoto
  if grep -q "^$1=$" .env; then
    sed -i "s|^$1=$|$1=$2|" .env
    echo "  $1 generato"
  fi
}

fill POSTGRES_PASSWORD "$(secret)"
fill JWT_SECRET "$(secret)"
# chiavi VAPID delle notifiche push (P-256, base64url): la coppia si genera solo se mancano tutte e due.
# Un .env creato prima delle notifiche non ha le righe: si aggiungono vuote
b64url() { openssl base64 -A | tr '+/' '-_' | tr -d '='; }
for name in VAPID_PUBLIC_KEY VAPID_PRIVATE_KEY; do
  grep -q "^$name=" .env || printf '%s=\n' "$name" >> .env
done
if grep -q "^VAPID_PRIVATE_KEY=$" .env && grep -q "^VAPID_PUBLIC_KEY=$" .env; then
  if command -v openssl >/dev/null 2>&1; then
    key=$(mktemp)
    openssl ecparam -name prime256v1 -genkey -noout -out "$key"
    fill VAPID_PRIVATE_KEY "$(openssl ec -in "$key" -outform DER 2>/dev/null | tail -c +8 | head -c 32 | b64url)"
    fill VAPID_PUBLIC_KEY "$(openssl ec -in "$key" -pubout -outform DER 2>/dev/null | tail -c 65 | b64url)"
    rm -f "$key"
  else
    echo "  openssl non trovato: genera le chiavi VAPID con"
    echo "    docker compose run --rm api python -m scripts.generate_vapid"
  fi
fi
if [ -n "$OCR_TOKEN_ARG" ]; then
  sed -i "s|^OCR_TOKEN=.*|OCR_TOKEN=$OCR_TOKEN_ARG|" .env
  echo "  OCR_TOKEN impostato"
else
  fill OCR_TOKEN "$(secret)"
fi

echo "Pronto: deploy/.env (permessi 600). Completa i campi vuoti con: nano .env"
