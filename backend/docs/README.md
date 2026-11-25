# Skedoo backend

API FastAPI per la PWA: orari delle classi, dati di ClasseViva (voti, agenda, lezioni, assenze, bacheca, didattica),
variazioni d'orario lette dall'OCR e notifiche push. Tutto richiede il token JWT tranne `/auth/login` e `/health`.

## Struttura

```
app/
  main.py        app FastAPI, lifespan, middleware (limite IP, body, header), CORS, router
  config.py      tutte le impostazioni (da .env) e i controlli per la produzione
  security.py    JWT, rate limiter, dipendenza `current_session` usata da ogni endpoint protetto
  classeviva.py  sessioni ClasseViva (login, cache, ri-login) e traduzione degli errori
  errors.py      formato errori {"code","message"}
  auth.py        POST /auth/login, GET /auth/me, POST /auth/refresh, POST /auth/logout
  schedules.py   orari (JSON o DB) + endpoint /schedules
  grades.py      GET /grades
  agenda.py      GET /agenda
  didactics.py   GET /didattica, GET /didattica/{contenuto} (download)
  board.py       GET /bacheca, GET /bacheca/{codice}/{id}/allegati/{numero} (download)
  downloads.py   download in streaming da ClasseViva, con limite di dimensione e di download contemporanei
  lessons.py     GET /lezioni (registro di classe e argomenti)
  absences.py    GET /assenze
  changes.py     GET /changes, /changes/entrate-uscite, /changes/cambi-aula
  push.py        GET /push/public-key, POST /push/subscribe, POST /push/unsubscribe
  push_sender.py task dell'API che manda le notifiche push delle variazioni nuove
  validation.py  controlli comuni sui parametri (intervalli di date)
  db.py          tabelle SQLAlchemy (classes, lessons, push_subscriptions, push_sent)
scripts/import_schedules.py             importa i JSON nel database
scripts/generate_vapid.py               genera le chiavi VAPID delle notifiche push
scripts/send_test_push.py               notifica di prova ai dispositivi di una classe
scripts/healthcheck.py                  healthcheck del container API
scripts/bacheca_fetch/fetch_bacheca.py  recupera e filtra la bacheca ClasseViva
scripts/bacheca_fetch/run_periodic.py   esegue il fetch della bacheca a intervalli regolari
scripts/bacheca_fetch/ocr_changes.py    legge con l'OCR i cartelloni scaricati e scrive data/dati-bacheca/data.json
tests/                                  python -m pytest -q tests
docs/db-schema.md                       schema e relazioni
```

## Avvio

```bash
# su Windows enviorment-setup.bat crea .venv e installa tutto (anche requirements-dev.txt)
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload              # Swagger su /docs (solo in sviluppo)
```

Gli orari si leggono da `data/`: `classi_index.json` (facoltativo) e `classi/<ID>.json` (uno per classe), oppure `tutte_le_classi.json`.

**Un solo processo**: sessioni e rate limit sono in memoria (niente `--workers N`).

**Password ClasseViva**: il server la tiene solo cifrata (AES-256-GCM) dentro la sessione. La chiave è casuale per ogni login e viaggia solo nel JWT (claim `k`): il server la riceve con ogni richiesta, decifra la password per la durata della chiamata a ClasseViva e poi la toglie dall'oggetto `Utente`. Un JWT senza `k` valido è rifiutato.

## Login e sessione

`POST /auth/login` con le credenziali ClasseViva → token JWT da mandare come `Authorization: Bearer <token>`. Il token punta a una sessione tenuta in memoria dal server: se il server riparte, dopo `logout` o alla scadenza il server risponde `401 session_expired` e il frontend torna al login con username e nome già compilati: serve solo la password, che il dispositivo non conserva mai.

Ogni token dura `JWT_TTL_HOURS` (7 giorni), ma il frontend lo rinnova con `POST /auth/refresh` quando l'app viene usata: si esce solo dopo 7 giorni di inattività, oppure dopo `SESSION_MAX_DAYS` (90) dal login. Il claim `auth` (istante del login) resta uguale a ogni rinnovo.

## Endpoint

| Metodo | Path | Descrizione |
|---|---|---|
| POST | `/auth/login` | `{username, password}` → token e `utente` con dati personali, `tipo` (`studente`/`genitore`, dal codice S…/G…; assente se non riconoscibile) e `scuola` (codice, nome, città, provincia) |
| GET | `/auth/me` | profilo utente e scuola |
| POST | `/auth/refresh` | nuovo token per la stessa sessione (`access_token`, `expires_in`); 401 `session_expired` dopo `SESSION_MAX_DAYS` dal login |
| POST | `/auth/logout` | 204, chiude la sessione |
| GET | `/schedules/classes` | `[{id, nome, docente_coordinatore, pomeriggio}]` |
| GET | `/schedules/{classe}` | orario completo (id non sensibile a maiuscole: `1a` = `1A`) |
| GET | `/schedules/{classe}/today` | lezioni di oggi (fuso Europe/Rome) |
| GET | `/grades?anno=26&periodo=1` | voti per materia con medie e docenti della materia |
| GET | `/agenda?da=YYYY-MM-DD&a=YYYY-MM-DD` | eventi per giorno (default oggi…+13 giorni, max 366) |
| GET | `/didattica` | materiali didattici organizzati per docente e cartella |
| GET | `/didattica/{contenuto}` | scarica un materiale (`id` dell'elenco); per link e testi risponde `{tipo: "link", url}` o `{tipo: "testo", testo}` |
| GET | `/bacheca` | circolari e comunicazioni, con allegati |
| GET | `/bacheca/{codice}/{id}` | dettaglio di una comunicazione `{titolo, testo}` (la segna come letta su ClasseViva) |
| GET | `/bacheca/{codice}/{id}/allegati/{numero}` | scarica un allegato (`numero` dell'elenco `allegati`) |
| GET | `/lezioni?data=YYYY-MM-DD` | registro di classe del giorno (default oggi): lezioni firmate con l'argomento scritto dal docente |
| GET | `/assenze?da=YYYY-MM-DD&a=YYYY-MM-DD` | assenze, ritardi e uscite con `riepilogo`; senza date restituisce l'anno |
| GET | `/changes?classe=1A&data=YYYY-MM-DD` | modifiche della classe (tutti i giorni nel file, o solo `data`) |
| GET | `/changes/entrate-uscite?classe=1A` | entrate e uscite della classe |
| GET | `/changes/cambi-aula?classe=1A` | cambi aula della classe |
| GET | `/push/public-key` | `{public_key}`: chiave VAPID pubblica per creare l'iscrizione nel browser |
| POST | `/push/subscribe` | 204; `{subscription: {endpoint, keys: {p256dh, auth}}, classe}` (stesso `endpoint` = aggiorna la classe). Max 20 all'ora per utente (429) |
| POST | `/push/unsubscribe` | 204; `{endpoint}` |
| GET | `/health` | `{"status":"ok"}`, pubblico |

### Risposte

```jsonc
// /schedules/1A
{"id":"1A","nome":"1 A","docente_coordinatore":"…","pomeriggio":false,
 "giorni":[{"giorno":"lunedi","etichetta":"Lunedì","lezioni":[
   {"ora":1,"inizio":"08:10","fine":"09:00","materia":"Inglese","materia_completa":null,"docenti":["ROSSI Mario"],"aula":"A12"}]}]}

// /schedules/1A/today
{"giorno":"lunedi","etichetta":"Lunedì","data":"2026-10-12","attivo":true,"lezioni":[ …come sopra… ]}

// /grades
{"anno":"26","periodo":null,"media_generale":7.4,
 "materie":[{"materia_id":1,"materia":"MATEMATICA","media":7.5,"docenti":["BIANCHI ANNA"],
   "voti":[{"id":1,"data":"2026-10-02","voto":"7+","valore":7.25,"tipo":"Scritto","periodo":"Primo periodo","periodo_pos":1,"peso":1.0,"note":null,"colore":"green","annullato":false}]}]}
// "voto" è il testo da mostrare, "valore" serve per i calcoli (null per i giudizi)
// "periodo_pos" permette al frontend di filtrare per quadrimestre con una sola richiesta
// "docenti" arriva da ClasseViva `materie`: se non disponibile è [] e i voti arrivano comunque

// /assenze
{"eventi":[{"id":21,"data":"2026-10-08","tipo":"assenza","codice":"ABA0","ora":null,"giustificata":false,"motivo":null,"ore":[]}],
 "riepilogo":{"assenze":2,"ritardi":2,"uscite":1,"da_giustificare":2}}
// tipo: assenza (ABA0) | ritardo (ABR0, ABR1) | uscita (ABU0) | altro

// /lezioni
{"data":"2026-10-06","lezioni":[
   {"id":31,"ora":2,"durata":2,"materia":"FISICA","docente":"BIANCHI Anna","tipo":"Lezione","compresenza":false,"argomento":"Moto rettilineo"},
   {"id":32,"ora":2,"durata":1,"materia":"SOSTEGNO","docente":"VERDI Luca","tipo":"Compresenza","compresenza":true,"argomento":null}]}
// le lezioni compaiono solo dopo la firma; "argomento" è null se il docente non l'ha scritto, altrimenti è il testo
// intero (spazi ripuliti, a capo mantenuti, al massimo 5000 caratteri): lo accorcia il frontend

// /agenda
{"giorni":[{"data":"2026-10-09","eventi":[
   {"id":5,"tipo":"compito","ora_inizio":null,"ora_fine":null,"tutto_il_giorno":true,"materia":"FISICA","autore":"BIANCHI Anna","testo":"Esercizi 1-10"}]}]}
```

### Errori

Formato `{"code": "...", "message": "..."}`. Le validazioni dei parametri rispondono `422 {"code": "validation_error", "message", "detail": [{"loc", "msg", "type"}]}`: a differenza del default di FastAPI non ripetono i valori inviati (es. la password).

| Status | code | Quando |
|---|---|---|
| 401 | `not_authenticated`, `invalid_token` | token mancante o non valido |
| 401 | `session_expired` | sessione chiusa/riavviata → rifare il login |
| 401 | `invalid_credentials` | login con password errata |
| 401 | `credentials_changed` | ClasseViva rifiuta la password al ricollegamento (cambiata dopo il login): la sessione viene chiusa → rifare il login |
| 404 | `class_not_found` | classe inesistente |
| 422 | `invalid_class` | classe nel formato sbagliato (`/changes`, `/push/subscribe`) |
| 413 | `payload_too_large` | body > 16 KB |
| 422 | `validation_error` | parametri mancanti o nel formato sbagliato |
| 422 | `invalid_range`, `range_too_large`, `invalid_parameter`, `date_out_of_range` | date di agenda e assenze |
| 429 | `rate_limited`, `too_many_attempts` | troppe richieste (header `Retry-After`) |
| 502 | `classeviva_error` | ClasseViva non risponde |
| 500 | `internal_error` | errore inatteso, dettagli solo nei log |
| 503 | `database_unavailable`, `changes_unavailable` | DB o dati locali non disponibili |
| 503 | `push_disabled` | notifiche push non configurate (mancano `VAPID_*` o `DATABASE_URL`) |

I download possono rispondere anche `404 file_not_found`, `413 file_too_large` (oltre `MAX_DOWNLOAD_MB`),
`429 too_many_downloads` (oltre `MAX_PARALLEL_DOWNLOADS` in corso) e `502 not_downloadable` (ClasseViva non
fornisce il contenuto come file).

## Sicurezza

- JWT HS256 con `sub`, `sid`, `iss`, `aud`, `iat`, `exp` obbligatori.
- Rate limit (finestra di 1 minuto, in memoria): per IP 300, per utente 60, in più 20 sugli endpoint che chiamano ClasseViva (voti, agenda, lezioni, assenze, bacheca, didattica), login 5 per (IP, username); dopo 10 password sbagliate in 15 minuti blocco temporaneo.
- Body max 16 KB, header di sicurezza, CORS e host espliciti, `/docs` spento in produzione.
- Download: il file passa a pezzi da 64 KB senza stare in memoria, al massimo `MAX_DOWNLOAD_MB` (250) e
  `MAX_PARALLEL_DOWNLOADS` (2) per utente; i redirect si seguono solo in https verso `*.spaggiari.eu`.
- `ENVIRONMENT=production` rifiuta di partire senza `JWT_SECRET` (≥32 caratteri), `SCHEDULE_SOURCE=db` + `DATABASE_URL`, `CORS_ORIGINS` e `ALLOWED_HOSTS` espliciti.
- Dietro a un reverse proxy imposta `TRUST_PROXY_HEADERS=true`, altrimenti il rate limit per IP vede solo l'IP del proxy.
- Il file `.env` non va mai committato.
- `.env.example` contiene solo nomi e valori di esempio, mai credenziali reali.

## Database degli orari

`SCHEDULE_SOURCE=json` (default, comodo in sviluppo) oppure `db` (produzione).

```bash
# PostgreSQL di sviluppo, raggiungibile solo dal tuo computer
docker run -d --name skedoo-db -e POSTGRES_USER=skedoo -e POSTGRES_PASSWORD=skedoo -e POSTGRES_DB=skedoo \
  -p 127.0.0.1:5432:5432 -v skedoo-db:/var/lib/postgresql/data postgres:16-alpine
# .env: DATABASE_URL=postgresql://skedoo:skedoo@localhost:5432/skedoo  e  SCHEDULE_SOURCE=db
python -m scripts.import_schedules                     # legge data/, crea le tabelle, importa (ripetibile)
# opzioni: --data-dir PATH  --database-url URL
```

Schema in [db-schema.md](db-schema.md).

## Notifiche push

Attive solo con `DATABASE_URL` e le chiavi VAPID (`python -m scripts.generate_vapid`, poi `VAPID_PUBLIC_KEY`,
`VAPID_PRIVATE_KEY` e `VAPID_SUBJECT` in `.env`); altrimenti `/push/*` risponde `503 push_disabled`.
Il task di `app/push_sender.py` ogni `PUSH_CHECK_SECONDS` (60) rilegge `data/dati-bacheca/data.json` e manda a ogni
classe iscritta una notifica per giorno con le variazioni nuove, tranne tra `PUSH_QUIET_START` e `PUSH_QUIET_END`
(22:00-06:30). Prova manuale: `python -m scripts.send_test_push 5J`.

## Test

```bash
pip install -r requirements-dev.txt
python -m pytest -q tests
TEST_DATABASE_URL=postgresql://… python -m pytest -q tests/test_db.py   # su PostgreSQL vero (database vuoto di prova)
```

### Aggiornamento periodico della bacheca

Il runner usa `CLASSVIVA_USERNAME` e `CLASSVIVA_PASSWORD` da `.env` o
dall'ambiente del processo. Esegue subito un fetch e poi ogni 15 minuti:

```bash
python -m scripts.bacheca_fetch.run_periodic
```

Variabili opzionali:

- `BACHECA_FETCH_INTERVAL_SECONDS`: intervallo in secondi, maggiore di zero;
- `BACHECA_FETCH_RUN_ON_START=false`: salta il fetch iniziale;
- `CLASSVIVA_BOARD_OUTPUT`: JSON prodotto (default `data/bacheca_fetch/board_matches.json`);
- `CLASSVIVA_BOARD_ATTACHMENTS`: directory degli allegati;
- `BACHECA_FETCH_LOG_LEVEL`: livello di logging, default `INFO`.

Gli errori di un ciclo vengono registrati e non interrompono i cicli successivi.

### Dai cartelloni alle variazioni (OCR)

Dopo ogni fetch riuscito `run_periodic` esegue `ocr_changes`, che si può lanciare anche da solo:

```bash
python -m scripts.bacheca_fetch.ocr_changes            # usa board_matches.json del fetch
python -m scripts.bacheca_fetch.ocr_changes --min-affidabilita media
```

1. per ogni comunicazione trovata prende le immagini allegate (i PDF vengono ignorati);
2. le legge con l'OCR di `helper/OCR/V5-Gemini` (API Gemini): con `OCR_URL` le invia al servizio HTTP (nel deploy
   il container `ocr-gemini`), altrimenti lancia `main.py` in un processo separato con lo stesso Python del backend
   (`opencv-python` e `numpy` sono in `requirements.txt`; `OCR_PYTHON` per usarne un altro) e gli passa
   `GEMINI_API_KEY` e `GEMINI_MODELS` di `.env`;
3. i risultati sono in cache per contenuto (`data/bacheca_fetch/ocr/`): un'immagine già letta non si rilegge;
4. tiene solo le voci con affidabilità almeno `BACHECA_OCR_MIN_AFFIDABILITA` (default `alta`) e la data del
   cartellone solo se affidabile o coerente con la data di pubblicazione;
5. se più comunicazioni riguardano lo stesso giorno vale la più recente ("Aggiornamento comunicazione...");
6. scrive `data/dati-bacheca/data.json` (giorni da oggi in poi). Se nessuna immagine è leggibile il file precedente resta invariato.

`/changes` rilegge il file quando cambia, senza riavviare l'API. Formato:

```jsonc
{"aggiornato_il": "...", "affidabilita_minima": "alta", "giorni": [
  {"data_iso": "2026-11-17", "entrate": [{"ora": "09:50", "classi": ["1A"]}], "uscite": [...],
   "senza_lezioni_pomeridiane": [{"classi": ["2OD"]}],
   "cambi_aula": [{"classe": "1C", "orario": "09:50 - 11:45", "aula": "AULA B108"}]}]}
// risposta di /changes: {"id","data","ora","ore":[3,4],"tipo","testo","nuova_aula","orario"}
// tipo: cambio_aula | entrata_posticipata | uscita_anticipata | senza_lezioni_pomeridiane
// ore: per cambio_aula le ore in cui vale; per entrate/uscite/pomeriggio le ore annullate
//   (entrata 15:20 -> [8], la mattina resta; uscita 11:45 -> [5,6,7], il pomeriggio resta)
// "3C/T" sul cartellone vale sia per 3C sia per 3T
```