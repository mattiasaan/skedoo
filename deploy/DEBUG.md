# Comandi utili per il debug

Tutti i comandi vanno lanciati **sul Raspberry, dalla cartella `~/skedoo/deploy`**. Installazione e configurazione
sono in [README.md](README.md).

## Stato generale

```bash
docker compose ps                     # container accesi: api e ocr-gemini devono essere "healthy"
docker stats --no-stream              # CPU e memoria di ogni container
docker system df                      # spazio occupato da immagini, volumi e cache di Docker
df -h /                               # spazio libero sulla scheda SD / sul disco
vcgencmd measure_temp                 # temperatura del Pi (sopra 80 °C rallenta da solo)
```

## Log

`-f` segue il log dal vivo (esci con Ctrl+C), `--tail 100` mostra le ultime 100 righe e `--since 1h` l'ultima ora.

```bash
docker compose logs -f api                  # API: richieste, errori, notifiche push
docker compose logs -f worker               # bacheca ClasseViva -> OCR -> variazioni
docker compose logs -f ocr-gemini           # OCR con Gemini (profilo ocr-gemini)
docker compose logs -f db                   # PostgreSQL
docker compose logs -f caddy                # HTTPS (profilo https)
docker compose logs -f cloudflared          # Cloudflare Tunnel (profilo tunnel)

docker compose logs --since 1h api worker   # più servizi insieme, ultima ora
docker compose logs --tail 200 api | grep -iE "error|warning|exception"   # solo i problemi
```

## API

```bash
curl -s -H "Host: $(grep ^API_DOMAIN .env | cut -d= -f2)" http://127.0.0.1:8000/health   # {"status":"ok"} dal Pi
curl -s https://$(grep ^API_DOMAIN .env | cut -d= -f2)/health                            # {"status":"ok"} da internet
docker compose restart api                  # riavvio (le sessioni sono in memoria: gli utenti rifanno il login)
```

## Notifiche push

```bash
# sono attive? deve comparire "notifiche push attive: controllo ogni 60s"
docker compose logs api | grep -i push

# notifiche consegnate e problemi dei servizi push
docker compose logs --since 24h api | grep -iE "notifiche push|servizio push|invio push"

# classi con dispositivi iscritti
docker compose exec api python -m scripts.send_test_push --elenco

# notifica di prova all'ultimo dispositivo iscritto della classe (di solito il tuo)
docker compose exec api python -m scripts.send_test_push 5J
# ... a tutti i dispositivi della classe, con un testo a scelta
docker compose exec api python -m scripts.send_test_push 5J --tutti --testo "Prova delle notifiche"
```

Esito della notifica di prova:

| Messaggio | Significato |
|---|---|
| `consegnata al servizio push` | Partita: se non arriva, controlla le impostazioni di notifica del telefono e il "Non disturbare" |
| `iscrizione scaduta (404/410)` | Il dispositivo ha revocato l'iscrizione: riattiva l'interruttore nel Profilo |
| `403` | Chiavi VAPID cambiate dopo l'iscrizione: spegni e riaccendi l'interruttore nel Profilo |
| `Notifiche push spente` | Mancano `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY` nel `.env`: `./init-env.sh`, poi `docker compose up -d` |

```bash
# le chiavi ci sono? (deve dare 2; non stampa le chiavi)
grep -cE "^VAPID_P(UBLIC|RIVATE)_KEY=.+" .env

# iscrizioni e variazioni già notificate, direttamente nel database
docker compose exec db psql -U skedoo -c "select id, class_id, created_at, last_sent_at from push_subscriptions order by created_at desc;"
docker compose exec db psql -U skedoo -c "select class_id, data, sent_at from push_sent order by sent_at desc limit 20;"

# far ripartire le notifiche di una classe (al prossimo giro, entro 60 s, rimanda le variazioni di oggi e dei giorni futuri)
docker compose exec db psql -U skedoo -c "delete from push_sent where class_id = '5J';"
```

Tra `PUSH_QUIET_START` e `PUSH_QUIET_END` (default 22:00-06:30) le variazioni vere non partono; la notifica di prova sì.

## Bacheca, OCR e variazioni

Il worker gira all'avvio e poi ogni `BACHECA_FETCH_INTERVAL_SECONDS` (15 minuti di default).

```bash
docker compose restart worker               # giro subito (scarica la bacheca e rilegge i cartelloni nuovi)

# variazioni lette dall'OCR (il file che usano /changes e le notifiche)
docker compose exec api python -m json.tool /app/data/dati-bacheca/data.json | less

# variazioni di una classe, come le vede l'app
docker compose exec api python -c "from app.changes import build_changes; [print(c.data, c.tipo, c.testo, c.orario or '') for c in build_changes('5J')]"

# l'OCR è raggiungibile dal worker? (stato e token)
docker compose exec worker python -c "import os,urllib.request as u; print(u.urlopen(os.environ['OCR_URL']+'/health').read())"
curl -s http://127.0.0.1:8090/health        # dal Pi dell'OCR: {"status":"ok"} ("starting" finché la chiave Gemini non è verificata)

# cartelloni già letti (cache dell'OCR): cancellandola, al prossimo giro vengono riletti tutti
docker compose exec worker ls /app/data/bacheca_fetch/ocr
docker compose exec worker sh -c 'rm -f /app/data/bacheca_fetch/ocr/*.json' && docker compose restart worker
```

Con Gemini ogni cartellone riletto costa una richiesta della quota gratuita: svuota la cache solo se serve.

## Database

```bash
docker compose exec db psql -U skedoo                       # console SQL (esci con \q)
docker compose exec db psql -U skedoo -c "\dt"              # tabelle
docker compose exec db psql -U skedoo -c "select count(*) from classes;"   # classi importate
docker compose exec db psql -U skedoo -c "select * from lessons where class_id = '5J' order by giorno, inizio;"
```

## Configurazione

```bash
docker compose config --services            # servizi attivi con i COMPOSE_PROFILES del .env
grep -E "^(COMPOSE_PROFILES|API_DOMAIN|CORS_ORIGINS|OCR_URL)=" .env      # impostazioni principali (niente segreti)
docker compose exec api env | grep -E "^(ENVIRONMENT|ALLOWED_HOSTS|PUSH_|VAPID_SUBJECT|TZ)"   # cosa vede l'API
```

Non incollare in chat o negli issue l'output completo di `docker compose config` o di `env`: contiene i segreti.

## Aggiornare e riavviare

```bash
git pull && docker compose up -d --build    # aggiornare il codice
docker compose up -d                        # applicare un .env modificato
docker compose restart api worker           # riavviare senza ricostruire
docker compose down                         # fermare tutto (i dati restano nei volumi)
docker image prune -f                       # cancellare le immagini vecchie dopo un aggiornamento
```
