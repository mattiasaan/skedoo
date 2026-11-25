# Skedoo sul Raspberry Pi

Tutto gira con Docker, configurato da un solo `compose.yaml` e da un file `.env` per ogni Raspberry.

```
                    internet (HTTPS)
                          │
              ┌───────────┴───────────┐   profilo https (Caddy) oppure tunnel (Cloudflare)
              │        api :8000      │   FastAPI, una sola istanza
              └──┬─────────────────┬──┘
     rete "db"   │                 │  volume app-data (sola lettura per l'API)
     (interna)   │                 │
              ┌──┴──┐        ┌─────┴─────┐  ogni 15 min: bacheca ClasseViva -> immagini
              │ db  │        │  worker   │  -> OCR -> data/dati-bacheca/data.json
              └─────┘        └─────┬─────┘
                                   │ POST /ocr  (Authorization: Bearer OCR_TOKEN)
                                   │ stesso Pi: rete Docker · altro Pi: LAN o Tailscale
                        ┌──────────┴──────────┐
                        │  ocr-gemini :8090   │  service.py (helper/OCR/V5-Gemini), nome in rete "ocr"
                        └──────────┬──────────┘
                                   │ HTTPS, GEMINI_API_KEY
                                   ▼
                        API Gemini (Google AI Studio)
```

L'OCR (codice in `helper/OCR/V5-Gemini`) divide il cartellone in ritagli con OpenCV (pochi secondi sul Pi) e li fa
leggere all'API Gemini: sul Pi non gira nessun modello. Il vecchio OCR locale (Qwen3-VL su Ollama, profilo `ocr`)
è archiviato in `history/OCR/V4-AI` e non fa più parte del deploy: se lo usavi vedi
[Passare dal vecchio profilo ocr](#passare-dal-vecchio-profilo-ocr).

| Profilo      | Container             | Dove                                         |
|--------------|-----------------------|----------------------------------------------|
| `backend`    | `db`, `api`, `worker` | Pi del backend                               |
| `ocr-gemini` | `ocr-gemini`          | Pi dell'OCR (di solito lo stesso Pi)         |
| `https`      | `caddy`               | Pi del backend, se hai porte 80/443 aperte   |
| `tunnel`     | `cloudflared`         | Pi del backend, se usi Cloudflare Tunnel     |

## Requisiti

- Raspberry Pi 4 o 5 con **Raspberry Pi OS 64 bit** (`uname -m` deve dire `aarch64`).
- RAM: il backend sta in circa 1 GB, l'OCR in 512 MB: basta un Pi da 2 GB.
- Spazio: circa 2 GB per le immagini Docker. Meglio un SSD che una microSD.
- Una chiave dell'API Gemini (piano gratuito), vedi [Chiave Gemini](#chiave-gemini).
- Per l'API su internet: un dominio (es. `api.miosito.it`). Puoi usare Cloudflare Tunnel, che non richiede porte aperte e
  funziona anche dietro CGNAT, oppure Caddy, con le porte 80 e 443 inoltrate dal router.
- Il frontend va su GitHub Pages (gratis), vedi il passo 3.

## 1. Preparazione (su ogni Raspberry)

```bash
sudo apt update && sudo apt full-upgrade -y
curl -fsSL https://get.docker.com | sudo sh        # Docker Engine + plugin compose
sudo usermod -aG docker $USER && newgrp docker     # docker senza sudo (poi rientra in SSH)

git clone <url-del-repo> ~/skedoo
cd ~/skedoo/deploy
sh init-env.sh                                     # crea .env (permessi 600) con i segreti generati

# log: al massimo 30 giorni (lo promette l'informativa privacy). Una volta sola
sudo mkdir -p /etc/systemd/journald.conf.d
sudo cp journald-skedoo.conf /etc/systemd/journald.conf.d/skedoo.conf
sudo systemctl restart systemd-journald
```

I container scrivono i log nel journal di sistema (driver `journald`), che con `journald-skedoo.conf` li cancella
dopo 30 giorni. `docker compose logs` funziona come prima. Senza quel file il journal li terrebbe molto più a lungo:
`init-env.sh` avvisa se manca. Per provare il compose su un computer senza journald (Docker Desktop) metti
`LOG_DRIVER=local` in `.env`.

Sicurezza di base del Pi: accesso SSH solo con chiave (`PasswordAuthentication no` in `/etc/ssh/sshd_config`),
aggiornamenti automatici (`sudo apt install unattended-upgrades`).

> **Docker scavalca ufw**: una porta pubblicata da un container è raggiungibile anche se ufw la blocca.
> Per questo il compose pubblica le porte solo sugli indirizzi indicati (`127.0.0.1` di default):
> non cambiare `OCR_BIND` e le porte se non serve.

## 2. Scegli la configurazione

### A) Tutto su un solo Raspberry

In `.env`:

```ini
COMPOSE_PROFILES=backend,ocr-gemini,tunnel   # oppure backend,ocr-gemini,https (un solo Pi: è la configurazione prevista)
API_DOMAIN=api.miosito.it
CORS_ORIGINS=https://<utente>.github.io      # solo l'origine, senza percorso
CLASSVIVA_USERNAME=...
CLASSVIVA_PASSWORD=...
GEMINI_API_KEY=...
OCR_URL=http://ocr:8090                      # rete interna di Docker
OCR_BIND=127.0.0.1                           # la porta dell'OCR non esce dal Pi
TUNNEL_TOKEN=...                             # solo con il profilo tunnel
```

```bash
docker compose up -d --build
```

### B) Due Raspberry nella stessa LAN

**Pi dell'OCR** (es. IP `192.168.1.51`, meglio fissarlo come IP statico/DHCP riservato sul router):

```bash
cd ~/skedoo/deploy && sh init-env.sh
grep OCR_TOKEN .env                       # copia il token: serve sull'altro Pi
```

In `.env`:

```ini
COMPOSE_PROFILES=ocr-gemini
GEMINI_API_KEY=...
OCR_BIND=0.0.0.0                          # oppure 192.168.1.51
```

```bash
docker compose up -d --build
```

**Pi del backend:**

```bash
cd ~/skedoo/deploy && sh init-env.sh --ocr-token <token-del-Pi-OCR>
```

In `.env`:

```ini
COMPOSE_PROFILES=backend,tunnel           # oppure backend,https
OCR_URL=http://192.168.1.51:8090
API_DOMAIN=...  CORS_ORIGINS=...  CLASSVIVA_USERNAME=...  CLASSVIVA_PASSWORD=...
```

```bash
docker compose up -d --build
```

Sulla LAN il traffico non è cifrato: il token protegge l'accesso all'OCR, ma chi è sulla stessa rete
potrebbe leggere token e immagini. Su una rete domestica fidata va bene. Altrimenti usa Tailscale anche in LAN
(configurazione C): il traffico resta diretto tra i due Pi, ma passa cifrato.

### C) Due Raspberry in reti diverse (consigliato: Tailscale)

Non aprire la porta dell'OCR sul router. Collega i due Pi con [Tailscale](https://tailscale.com),
una VPN WireGuard gratuita che non richiede porte aperte e funziona anche dietro CGNAT.

Su **entrambi** i Pi:

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up                         # apri il link e accedi con lo stesso account
tailscale ip -4                           # IP del Pi nella VPN, es. 100.101.102.103
```

Poi procedi come nella configurazione B. Cambia solo l'indirizzo dell'OCR:

- Pi dell'OCR: `COMPOSE_PROFILES=ocr-gemini`, `OCR_BIND=0.0.0.0`. Il Pi resta irraggiungibile da internet, perché il router
  non inoltra la porta: arrivano solo la sua LAN e la VPN.
- Pi del backend: `OCR_URL=http://100.101.102.103:8090` (IP Tailscale del Pi dell'OCR).

Con `OCR_BIND=<IP Tailscale>` l'OCR ascolta solo dalla VPN. Docker però deve partire dopo Tailscale,
altrimenti al riavvio non trova l'indirizzo:

```bash
sudo systemctl edit docker      # aggiungi:  [Unit]  After=tailscaled.service  Wants=tailscaled.service
```

Per restringere ancora, nelle ACL di Tailscale permetti al Pi del backend solo la porta `8090` del Pi dell'OCR.

### Chiave Gemini

1. Crea una chiave su <https://aistudio.google.com/apikey> (piano gratuito, senza carta).
2. Mettila in `GEMINI_API_KEY` nel `.env` del Pi dell'OCR. `GEMINI_MODELS` (facoltativo) sceglie i modelli in ordine
   di preferenza; vuoto = quelli di `helper/OCR/V5-Gemini/config.json`.

Il piano gratuito ha pochi messaggi al giorno per modello: ogni cartellone costa **una** richiesta, i risultati restano
in cache, e finita la quota del primo modello si passa al successivo. Se le quote sono finite tutte il worker riprova
al giro successivo.

Sul piano gratuito Google può usare i ritagli inviati (classi, aule, orari) per migliorare i suoi prodotti: i riquadri
informativi (docenti assenti, FSL, viaggi) non vengono letti né inviati.

### Passare dal vecchio profilo `ocr`

Il profilo `ocr` (Qwen3-VL su Ollama) non esiste più. Se il `.env` del Pi ha ancora `ocr` in `COMPOSE_PROFILES`:

1. In `.env`: sostituisci `ocr` con `ocr-gemini` in `COMPOSE_PROFILES` e aggiungi `GEMINI_API_KEY`
   (`OCR_URL=http://ocr:8090` resta uguale: il container risponde anche al nome `ocr`). `OCR_MODEL` non serve più.
2. Aggiorna e togli i vecchi container `ocr` e `ollama`, che altrimenti terrebbero occupati la porta 8090 e il nome `ocr`:

   ```bash
   git pull && docker compose up -d --build --remove-orphans
   ```

3. Facoltativo, per liberare i ~2 GB del modello e le vecchie immagini:

   ```bash
   docker volume rm skedoo_ollama-models
   docker image rm skedoo-ocr:latest ollama/ollama:0.40.16
   ```

## 3. Esporre l'API e pubblicare il frontend

### API: Cloudflare Tunnel (profilo `tunnel`)

Serve un dominio sul piano gratuito di Cloudflare. Non si aprono porte sul router.

1. Aggiungi il dominio a Cloudflare (Add a site) e imposta i nameserver indicati presso chi te l'ha venduto.
2. Zero Trust -> Networks -> Tunnels -> *Create a tunnel* (tipo Cloudflared). Copia il token in `TUNNEL_TOKEN`.
3. Nello stesso tunnel aggiungi un *Public hostname*: `api.miosito.it` -> servizio `HTTP` `api:8000`.
4. In `.env`: `COMPOSE_PROFILES=backend,ocr-gemini,tunnel`, `API_DOMAIN=api.miosito.it`.

In alternativa **Caddy** (`https`): record DNS `A` `api.miosito.it` verso l'IP pubblico di casa e porte 80/443 del router
inoltrate al Pi. Caddy ottiene e rinnova il certificato da solo.

`API_DOMAIN` deve essere esattamente il nome pubblico: l'API rifiuta gli altri host.

### Frontend: GitHub Pages

Il workflow [.github/workflows/frontend-pages.yml](../.github/workflows/frontend-pages.yml) compila e pubblica il frontend
a ogni push su `main` che tocca `frontend/`. Una volta sola, su GitHub:

1. *Settings -> Pages -> Source*: **GitHub Actions**.
2. *Settings -> Secrets and variables -> Actions -> Variables*: crea `API_URL` = `https://api.miosito.it`.

Il sito sarà su `https://<utente>.github.io/skedoo/`. Nel `.env` del Pi il CORS vuole solo l'**origine**, senza percorso
e senza `/` finale:

```ini
CORS_ORIGINS=https://<utente>.github.io
```

Poi `docker compose up -d` per applicarlo. Il routing usa l'hash (`#home`), quindi non servono regole di fallback sul server.

### Notifiche push

L'API invia le variazioni d'orario (entrate, uscite, cambi aula) ai dispositivi iscritti dal Profilo dell'app. Servono
solo le chiavi VAPID, che `./init-env.sh` genera da solo (anche su un `.env` già esistente: rilancialo dopo `git pull`).
In alternativa:

```bash
docker compose run --rm api python -m scripts.generate_vapid   # stampa le due righe da copiare in .env
```

- `VAPID_SUBJECT` vuoto vale `https://API_DOMAIN`; puoi mettere `mailto:tuo@indirizzo.it`. I servizi push lo usano
  per contattarti in caso di problemi.
- Senza chiavi le notifiche sono spente: `GET /push/public-key` risponde 503 e l'interruttore nel Profilo lo dice.
- Tra `PUSH_QUIET_START` e `PUSH_QUIET_END` (default 22:00-06:30) non parte niente: le variazioni trovate di notte
  arrivano alla fine del silenzio.
- **Non cambiare le chiavi** se non serve: le iscrizioni vecchie smettono di funzionare e ogni dispositivo si reiscrive
  solo alla prossima apertura dell'app.
- Su iPhone e iPad le notifiche arrivano solo se Skedoo è aggiunto alla schermata Home (iOS 16.4 o successivo).

## 4. Importa gli orari (una volta, e a ogni cambio d'orario)

I JSON degli orari non sono nel repo. Dal PC copiali sul Pi del backend:

```bash
# dal PC, nella cartella del progetto
scp -r backend/data/classi backend/data/classi_index.json pi@<ip-del-pi>:~/skedoo/deploy/orari/
```

Sul Pi:

```bash
cd ~/skedoo/deploy
docker compose run --rm -v "$PWD/orari:/import:ro" api python -m scripts.import_schedules --data-dir /import
```

Puoi rilanciarlo quando vuoi: sostituisce l'orario delle classi presenti nei file.

## 5. Verifica

```bash
docker compose ps                                     # tutti "running", api e ocr-gemini "healthy"
curl -H "Host: $(grep ^API_DOMAIN .env | cut -d= -f2)" http://127.0.0.1:8000/health   # {"status":"ok"}
curl https://api.miosito.it/health                    # da fuori, dopo il passo 3
docker compose logs -f worker                         # bacheca scaricata, immagini inviate all'OCR
docker compose logs api | grep -i push                # "notifiche push attive", poi "notifiche push consegnate: N"
```

Sul Pi dell'OCR:

```bash
docker compose logs -f ocr-gemini # "OCR pronto: Gemini ..." (oppure "... controlla GEMINI_API_KEY")
curl http://127.0.0.1:8090/health # {"status":"ok"} con la chiave verificata ("starting" prima)
```

Dal Pi del backend, per verificare che l'OCR sia raggiungibile e che il token sia giusto:

```bash
docker compose exec worker python -c "import os,urllib.request as u; print(u.urlopen(os.environ['OCR_URL']+'/health').read())"
```

Il worker gira subito all'avvio e poi ogni `BACHECA_FETCH_INTERVAL_SECONDS` (15 minuti di default).
Se l'OCR non è ancora pronto, le immagini vengono rilette al giro successivo. Quelle già lette restano in cache.

## Manutenzione

Per log, notifica di prova, OCR e database vedi [DEBUG.md](DEBUG.md).

```bash
git pull && docker compose up -d --build     # aggiornare
docker compose logs --tail 100 api           # log (nel journal, cancellati dopo 30 giorni)
docker compose down                          # fermare (i dati restano nei volumi)

# backup del database
docker compose exec -T db pg_dump -U skedoo skedoo | gzip > skedoo-$(date +%F).sql.gz
# ripristino
gunzip -c skedoo-AAAA-MM-GG.sql.gz | docker compose exec -T db psql -U skedoo skedoo
```

Il contenuto del database si ricrea in ogni momento reimportando gli orari. Il volume `app-data` (bacheca e cache
dell'OCR) si rigenera da solo: il worker legge solo le comunicazioni degli ultimi 14 giorni e cancella immagini e
letture OCR più vecchie di 30 giorni (contengono cognomi di docenti). Per cambiare un segreto modifica `.env` e rilancia `docker compose up -d`.
Unica eccezione è `POSTGRES_PASSWORD`, che vale solo alla prima creazione del database: per cambiarla dopo,
`docker compose exec db psql -U skedoo -c "ALTER USER skedoo PASSWORD '...'"`.

## Cosa protegge cosa

- **Segreti** solo in `deploy/.env` (permessi 600, ignorato da git, mai copiato nelle immagini). Ogni container riceve
  soltanto le variabili che gli servono: il worker non ha il JWT né la password del database, l'OCR ha solo il suo token.
- **Notifiche push**: la chiave VAPID privata sta solo in `.env` e nell'API. Il server salva endpoint, chiavi del
  browser e classe, nessun dato dell'utente; il contenuto delle notifiche è cifrato per il dispositivo (i servizi push
  di Google, Mozilla, Microsoft e Apple non lo leggono). Endpoint accettati solo verso quei servizi, in `https`.
- **Database** su una rete Docker interna: nessuna porta, nessun accesso a internet, lo raggiunge solo l'API.
- **API** pubblicata solo su `127.0.0.1`: da fuori si arriva solo da Caddy o dal tunnel. In produzione l'API non parte
  se mancano `JWT_SECRET`, `CORS_ORIGINS` o `ALLOWED_HOSTS`. Restano attivi rate limit, header di sicurezza e
  documentazione spenta.
- **OCR**: token obbligatorio (almeno 32 caratteri, confronto a tempo costante), solo immagini fino a 20 MB, una lettura
  alla volta, nessuna documentazione. La chiave Gemini sta solo nel container `ocr-gemini`, viaggia nell'header
  (mai nell'URL o nei log) e i dettagli degli errori di Google restano nei log.
- **Container**: utente non root, filesystem in sola lettura, nessuna capability Linux, `no-new-privileges`,
  limiti di memoria. Le versioni delle immagini esterne sono fissate.
- **Log e privacy**: log nel journal di sistema, cancellati dopo 30 giorni (`journald-skedoo.conf`); nessun access log
  su Caddy; nei login falliti l'API scrive l'IP e uno pseudonimo dello username, mai il codice personale.
