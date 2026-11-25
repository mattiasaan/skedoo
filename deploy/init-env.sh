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
# ---------------------------------------------------------------- chiavi VAPID (notifiche push)
# Un .env creato prima delle notifiche non ha le righe: si aggiungono vuote. Se il file non finisce con un a capo,
# prima si va a capo (altrimenti la riga nuova finirebbe attaccata all'ultima)
[ -z "$(tail -c1 .env)" ] || echo >> .env
# riparazione di un .env già rovinato da una versione precedente di questo script ("ALTRO=xVAPID_PUBLIC_KEY=")
sed -i 's/^\(..*\)\(VAPID_P[A-Z]*_KEY=\)$/\1\n\2/' .env
for name in VAPID_PUBLIC_KEY VAPID_PRIVATE_KEY; do
  grep -q "^$name=" .env || printf '%s=\n' "$name" >> .env
done

b64url() { openssl base64 -A | tr '+/' '-_' | tr -d '='; }
set_value() {  # set_value NOME valore: sostituisce il valore, qualunque fosse
  sed -i "s|^$1=.*|$1=$2|" .env
  echo "  $1 generato"
}

# le due chiavi valgono solo in coppia: se ne manca una si rigenerano tutte e due
if ! grep -q "^VAPID_PRIVATE_KEY=." .env || ! grep -q "^VAPID_PUBLIC_KEY=." .env; then
  if command -v openssl >/dev/null 2>&1; then
    key=$(mktemp)
    openssl ecparam -name prime256v1 -genkey -noout -out "$key"
    private=$(openssl ec -in "$key" -outform DER 2>/dev/null | tail -c +8 | head -c 32 | b64url)
    public=$(openssl ec -in "$key" -pubout -outform DER 2>/dev/null | tail -c 65 | b64url)
    rm -f "$key"
    if [ "${#private}" -ne 43 ] || [ "${#public}" -ne 87 ]; then  # 32 e 65 byte in base64url
      echo "Chiavi VAPID non generate (openssl: $(openssl version)). Generale con:" >&2
      echo "  docker compose run --rm api python -m scripts.generate_vapid" >&2
      exit 1
    fi
    set_value VAPID_PRIVATE_KEY "$private"
    set_value VAPID_PUBLIC_KEY "$public"
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

# i log dei container vanno nel journal: l'informativa promette che non restano più di 30 giorni
if [ ! -f /etc/systemd/journald.conf.d/skedoo.conf ] && ! grep -q "^LOG_DRIVER=" .env; then
  echo
  echo "ATTENZIONE: manca la conservazione dei log a 30 giorni (informativa privacy). Esegui una volta:"
  echo "  sudo mkdir -p /etc/systemd/journald.conf.d"
  echo "  sudo cp journald-skedoo.conf /etc/systemd/journald.conf.d/skedoo.conf"
  echo "  sudo systemctl restart systemd-journald"
fi
