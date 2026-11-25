# Contribuire a Skedoo

Grazie per voler contribuire! Questa guida spiega come preparare l'ambiente, come proporre modifiche e quali regole seguire.

## Prima di iniziare: la licenza

Skedoo **non è open source**: è distribuito con una [licenza proprietaria](License). In sintesi:

- puoi leggere e modificare il codice **solo per contribuire** al progetto;
- le modifiche vanno inviate **tramite Pull Request** a questa repository;
- non puoi distribuire o pubblicare versioni modificate o derivate al di fuori di questo processo;
- il Titolare può accettare, rifiutare o modificare qualsiasi contributo.

Aprendo una PR dichiari di aver letto e accettato la Licenza, compresa la parte sui diritti dei contributi. In caso di dubbio fa fede il testo della Licenza.

## Codice di condotta

Partecipando accetti il [Codice di condotta](CODE_OF_CONDUCT.md).

## Segnalare bug e proporre idee

- **Bug** e **nuove funzionalità**: apri una issue con il modello apposito.
- **Vulnerabilità di sicurezza**: **mai** in una issue pubblica. Segui [SECURITY.md](SECURITY.md).

Prima di aprire una issue controlla che non ne esista già una simile. Per le modifiche grandi apri prima una issue per discuterne: così non lavori su qualcosa che poi non viene accettato.

## Struttura della repo

| Cartella    | Contenuto                                         |
|-------------|---------------------------------------------------|
| `frontend/` | React + Vite                                      |
| `backend/`  | FastAPI, PostgreSQL, integrazione ClasseViva      |
| `helper/`   | Parsing del PDF degli orari e OCR della bacheca   |
| `deploy/`   | Docker Compose e Caddy per il Raspberry Pi        |
| `legal/`    | Documentazione privacy e GDPR                     |

La documentazione tecnica è in [backend/docs/](backend/docs/).

## Ambiente di sviluppo

### Requisiti

- Python **3.13**
- Node.js **22**
- PostgreSQL (oppure Docker per avviarlo)

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate   |   Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env    # poi compila i valori
uvicorn app.main:app --reload
```

I dettagli sulle variabili d'ambiente sono in [backend/docs/enviorment.md](backend/docs/enviorment.md).

### Frontend

```bash
cd frontend
npm ci
cp .env.example .env    # imposta VITE_API_URL
npm run dev
```

## Test e lint

Prima di aprire una PR assicurati che questi comandi passino:

```bash
# backend
cd backend && pytest

# frontend
cd frontend && npm run lint && npm test && npm run build
```

La CI li esegue automaticamente su ogni PR. Se aggiungi una funzionalità o correggi un bug, aggiungi o aggiorna i test.

## Regole sui dati (importante)

Skedoo tratta dati di studenti. Quindi:

- **Mai** committare file `.env`, chiavi API, chiavi VAPID, token o credenziali ClasseViva.
- **Mai** usare dati reali (nomi, voti, foto della bacheca, orari con nomi di docenti) in test, fixture, screenshot o issue. Usa dati finti, come in `backend/tests/conftest.py`.
- Se una modifica cambia **quali dati** raccogliamo, come li conserviamo o a chi li inviamo (per esempio un nuovo servizio esterno), segnalalo nella PR: potrebbe essere necessario aggiornare la documentazione in `legal/` e l'informativa privacy.

Se committi un segreto per errore, avvisa subito il maintainer: va sostituito con uno nuovo, perché cancellarlo dalla history non basta.

## Branch e commit

- Lavora su un fork o su un branch, mai direttamente su `main`.
- Nomi dei branch: `feature/<descrizione>`, `fix/<descrizione>`, `docs/<descrizione>`, `chore/<descrizione>`.
- Messaggi di commit in italiano, nel formato già usato nella repo:

  ```
  Area: descrizione breve
  ```

  Esempi: `Push: script per la notifica di prova`, `Privacy: OCR con Gemini API`.
- Commit piccoli e mirati: ogni PR dovrebbe occuparsi di una cosa sola.

## Pull Request

1. Aggiorna il tuo branch con l'ultimo `main`.
2. Verifica che test, lint e build passino.
3. Apri la PR verso `main` e compila il modello (cosa cambia, come l'hai testato, checklist).
4. Collega la issue relativa (`Closes #123`).
5. Rispondi alle richieste di revisione: le PR vengono unite solo dopo l'approvazione del maintainer.

## Stile del codice

- **Python**: PEP 8, type hint dove possibile, nomi e commenti coerenti con il codice esistente.
- **JavaScript/React**: segui la configurazione ESLint del progetto (`npm run lint`).
- Commenti e documentazione in italiano.
