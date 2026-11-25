# Skedoo

**Skedoo** è una webapp che centralizza **orari scolastici, comunicazioni e modifiche giornaliere** in un'unica app moderna per studenti e professori.
Il progetto nasce per risolvere un problema comune nelle scuole: informazioni frammentate tra **PDF statici, immagini nella bacheca e notifiche poco chiare**.
Skedoo trasforma questi dati in un sistema **interattivo, aggiornato e notificabile**.

# Panoramica

| Cartella    | Cosa contiene                                                                 |
|-------------|-------------------------------------------------------------------------------|
| `frontend/` | App **React + Vite** (login, home, orario e agenda, voti, profilo)            |
| `backend/`  | API **FastAPI** con database PostgreSQL, integrazione ClasseViva e documentazione |
| `helper/`   | Strumenti di supporto: parsing del PDF degli orari (`orario_dataset/`) e **OCR** della bacheca (`OCR/V5-Gemini/`) |
| `deploy/`   | Docker Compose per mettere tutto su un Raspberry Pi                           |
| `legal/`    | Indice della documentazione legale (privacy, cookie, termini)                 |
| `history/`  | Vecchie versioni funzionanti ma non più usate dal progetto (OCR V3 e V4)      |

# Cosa Fa
Skedoo permette di:
* 📅 Visualizzare l'orario scolastico in formato **digitale e interattivo**
* 🔄 Vedere le **modifiche giornaliere** (entrate posticipate, uscite anticipate, pomeriggi senza lezione, cambi aula)
* 📝 Consultare **voti, agenda, assenze e bacheca** di ClasseViva
* 🔔 Ricevere **notifiche mirate**
* Evidenziare le differenze tra **orario standard e modifiche giornaliere**

# Come Funziona
Skedoo raccoglie e normalizza le informazioni scolastiche provenienti da:

* PDF degli orari
* comunicazioni pubblicate su ClasseViva (anche immagini, lette tramite OCR)

### Processo

1. Parsing del **PDF dell'orario scolastico** e conversione in **struttura dati**
2. Salvataggio nel **database**
3. Lettura delle **circolari e delle immagini della bacheca** tramite OCR
4. Sincronizzazione delle **modifiche giornaliere**
5. Confronto automatico con l'orario base

# Tech Stack

## Backend

* **Python**
* **FastAPI**
* **PostgreSQL**
* **JWT Authentication**

Integrazione con:

* `Classeviva.py` per accesso alle API di ClasseViva

## Frontend

* **React** + **Vite**
* **Responsive UI** (telefono, tablet e desktop con sidebar)
* **Push Notifications**

Avvio in sviluppo (dettagli in [backend/docs/README.md](backend/docs/README.md) e [frontend/README.md](frontend/README.md)):

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0   # API su http://localhost:8000

cd frontend
npm install
npm run dev            # http://localhost:5173, le chiamate /api/* passano dal proxy di Vite
npm run dev -- --host  # per provarlo dal telefono sulla stessa rete
```

In produzione impostare `VITE_API_URL` con l'indirizzo dell'API (vedi `frontend/.env.example`).

## OCR

Un servizio dedicato divide i cartelloni della bacheca in ritagli (OpenCV), li fa leggere all'API **Gemini** di Google
e controlla ogni voce con dei validatori (griglia degli orari, elenchi di classi e aule), assegnandole un'affidabilità.
La pipeline si trova in [helper/OCR/V5-Gemini](helper/OCR/V5-Gemini/README.md). Le versioni precedenti
(Tesseract, Qwen3-VL su Ollama) sono archiviate in [history/](history/README.md).

## Deploy (Raspberry Pi)

Backend, database e OCR girano in container Docker, su un solo Raspberry o su due (stessa LAN o reti diverse):
guida passo passo in [deploy/README.md](deploy/README.md).

# Sicurezza

* Autenticazione tramite ClasseViva
* JWT authentication
* Validazione input
* Rate limiting

Hai trovato una vulnerabilità? **Non aprire una issue pubblica**: segui [SECURITY.md](SECURITY.md) e usa la scheda **Security → Report a vulnerability**.

# Contribuire

I contributi sono benvenuti tramite Pull Request, nei limiti della [Licenza](License).
Leggi [CONTRIBUTING.md](CONTRIBUTING.md) e il [Codice di condotta](CODE_OF_CONDUCT.md) prima di iniziare.

# Stato del Progetto

**Work in Progress**

Skedoo è attualmente in fase di sviluppo, il beta testing inizierà a breve.
