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
if [ -n "$OCR_TOKEN_ARG" ]; then
  sed -i "s|^OCR_TOKEN=.*|OCR_TOKEN=$OCR_TOKEN_ARG|" .env
  echo "  OCR_TOKEN impostato"
else
  fill OCR_TOKEN "$(secret)"
fi

echo "Pronto: deploy/.env (permessi 600). Completa i campi vuoti con: nano .env"
