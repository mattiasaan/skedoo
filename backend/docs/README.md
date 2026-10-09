# Skedoo backend

API FastAPI per la PWA: orari delle classi, voti e agenda da ClasseViva. Tutto richiede il token JWT tranne `/auth/login` e `/health`.

## Struttura

```
app/
  main.py        app FastAPI, middleware (limite IP, dimensione body, header di sicurezza), CORS, router
  config.py      tutte le impostazioni (da .env) e i controlli per la produzione
  security.py    JWT, rate limiter, dipendenza `current_session` usata da ogni endpoint protetto
  classeviva.py  sessioni ClasseViva (login, cache, ri-login) e traduzione degli errori
  errors.py      formato errori {"code","message"}
  auth.py        POST /auth/login, GET /auth/me, POST /auth/logout
  schedules.py   orari (JSON o DB) + endpoint /schedules
  grades.py      GET /grades
  agenda.py      GET /agenda
  db.py          tabelle SQLAlchemy (classes, lessons)
scripts/import_schedules.py   importa i JSON nel database
tests/                        python -m pytest -q tests
docs/db-schema.md             schema e relazioni
```

Per aggiungere un endpoint: nuovo file in `app/` con un `APIRouter`, `Depends(current_session)` (e `upstream_limit` se chiama ClasseViva), poi `app.include_router(...)` in `main.py`.

## Avvio

```bash
pip install -r requirements.txt            # Classeviva.py 1.3: pip install /percorso/Classeviva.py
cp .env.example .env
uvicorn app.main:app --reload              # Swagger su /docs (solo in sviluppo)
```

Gli orari si leggono da `data/`: `classi_index.json` (facoltativo) e `classi/<ID>.json` (uno per classe), oppure `tutte_le_classi.json`.

**Un solo processo**: sessioni e rate limit sono in memoria (niente `--workers N`).

## Login e sessione

`POST /auth/login` con le credenziali ClasseViva → token JWT da mandare come `Authorization: Bearer <token>`. Il token punta a una sessione tenuta in memoria dal server: se il server riparte, dopo `logout` o alla scadenza il server risponde `401 session_expired` e il frontend rifà il login con le credenziali salvate.

## Endpoint

| Metodo | Path | Descrizione |
|---|---|---|
| POST | `/auth/login` | `{username, password}` → `{access_token, token_type, expires_in, utente:{id,nome,cognome}}` |
| GET | `/auth/me` | `{id, nome, cognome}` |
| POST | `/auth/logout` | 204, chiude la sessione |
| GET | `/schedules/classes` | `[{id, nome, docente_coordinatore, pomeriggio}]` |
| GET | `/schedules/{classe}` | orario completo (id non sensibile a maiuscole: `1a` = `1A`) |
| GET | `/schedules/{classe}/today` | lezioni di oggi (fuso Europe/Rome) |
| GET | `/grades?anno=26&periodo=1` | voti per materia con medie |
| GET | `/agenda?da=YYYY-MM-DD&a=YYYY-MM-DD` | eventi per giorno (default oggi…+13 giorni, max 366) |
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
 "materie":[{"materia_id":1,"materia":"MATEMATICA","media":7.5,
   "voti":[{"id":1,"data":"2026-10-02","voto":"7+","valore":7.25,"tipo":"Scritto","periodo":"1","peso":1.0,"note":null,"colore":"green","annullato":false}]}]}
// "voto" è il testo da mostrare, "valore" serve per i calcoli (null per i giudizi)

// /agenda
{"giorni":[{"data":"2026-10-09","eventi":[
   {"id":5,"tipo":"compito","ora_inizio":null,"ora_fine":null,"tutto_il_giorno":true,"materia":"FISICA","autore":"BIANCHI Anna","testo":"Esercizi 1-10"}]}]}
```

### Errori

Formato `{"code": "...", "message": "..."}` (le validazioni di FastAPI restano il classico `422 {"detail":[...]}`).

| Status | code | Quando |
|---|---|---|
| 401 | `not_authenticated`, `invalid_token` | token mancante o non valido |
| 401 | `session_expired` | sessione chiusa/riavviata → rifare il login |
| 401 | `invalid_credentials` | login con password errata |
| 404 | `class_not_found` | classe inesistente |
| 413 | `payload_too_large` | body > 16 KB |
| 422 | `invalid_range`, `range_too_large`, `invalid_parameter`, `date_out_of_range` | parametri agenda |
| 429 | `rate_limited`, `too_many_attempts` | troppe richieste (header `Retry-After`) |
| 502 | `classeviva_error` | ClasseViva non risponde |
| 503 | `database_unavailable` | DB non raggiungibile |

## Sicurezza

- JWT HS256 con `sub`, `sid`, `iss`, `aud`, `iat`, `exp` obbligatori.
- Rate limit (finestra di 1 minuto, in memoria): per IP 300, per utente 60, voti/agenda 20, login 5 per (IP, username); dopo 10 password sbagliate in 15 minuti blocco temporaneo.
- Body max 16 KB, header di sicurezza, CORS e host espliciti, `/docs` spento in produzione.
- `ENVIRONMENT=production` rifiuta di partire senza `JWT_SECRET` (≥32 caratteri), `SCHEDULE_SOURCE=db` + `DATABASE_URL`, `CORS_ORIGINS` e `ALLOWED_HOSTS` espliciti.
- Dietro a un reverse proxy imposta `TRUST_PROXY_HEADERS=true`, altrimenti il rate limit per IP vede solo l'IP del proxy.
- Il file `.env` non va mai committato.

## Database degli orari

`SCHEDULE_SOURCE=json` (default, comodo in sviluppo) oppure `db` (produzione).

```bash
docker compose up -d                                   # PostgreSQL di sviluppo
# .env: DATABASE_URL=postgresql://skedoo:skedoo@localhost:5432/skedoo  e  SCHEDULE_SOURCE=db
python -m scripts.import_schedules                     # legge data/, crea le tabelle, importa (ripetibile)
# opzioni: --data-dir PATH  --database-url URL
```

Schema in [docs/db-schema.md](docs/db-schema.md).

## Test

```bash
pip install -r requirements-dev.txt
python -m pytest -q tests
TEST_DATABASE_URL=postgresql://… python -m pytest -q tests/test_db.py   # su PostgreSQL vero (database vuoto di prova)
```
