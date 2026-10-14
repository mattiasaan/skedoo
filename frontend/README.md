# Skedoo frontend

App React per studenti: orario, voti (con calcolo del voto minimo) e agenda, collegata al backend FastAPI.
È una **PWA**: si installa su Android e iOS dalla schermata del browser, senza passare dagli store.

Stack: Vite + React 19 + React Router + CSS semplice (nessuna libreria di stato o di stile). Solo JavaScript.

## Avvio

```bash
npm install
npm run dev          # http://localhost:5173  (il backend deve girare su http://localhost:8000)
npm test             # test dei calcoli (voti, date)
npm run build        # versione per la produzione in dist/
```

In sviluppo le chiamate a `/api/...` vengono girate da Vite al backend (porta 8000), quindi non servono impostazioni
di CORS. Se il backend è altrove: `BACKEND_URL=http://altro-host:8000 npm run dev`.

Per provare dal telefono sulla stessa rete Wi‑Fi apri `http://IP-DEL-PC:5173` (`npm run dev` è già esposto in rete).
L'installazione come app richiede però HTTPS: vedi sotto.

## Struttura

```
src/
  main.jsx            avvio dell'app
  App.jsx             elenco delle pagine (route) e protezione del login
  api/
    client.js         fetch verso il backend: token, errori in italiano, ri-login automatico
    index.js          UNA funzione per endpoint (login, fetchGrades, fetchAgenda...)
    useApi.js         hook per caricare dati: { data, loading, error, reload }
    changes.js        modifiche all'orario: per ora dati di esempio (vedi sotto)
  auth/AuthContext.jsx  utente, classe scelta, login, logout
  pages/              una cartella-file per schermata: Login, ClassPicker, Home, Schedule, Grades, Agenda, Profile
  components/         pezzi riusati: BottomNav, LessonCard, SubjectCard, Banner, Status (caricamento/errore)...
  lib/                logica pura, senza React e con test: dates, gradeMath, lessons, changes, storage
  styles/             tokens.css (colori, spazi, font), base.css (bottoni, card, input...)
```

Ogni componente ha il suo `.css` accanto. Regola di casa: **le pagine chiamano `api/`, la logica sta in `lib/`,
i colori stanno solo in `tokens.css`.**

## Come si fa...

**Cambiare i colori o il font** → `src/styles/tokens.css`.

**Aggiungere una pagina**
1. crea `src/pages/Nome.jsx` (copia `Agenda.jsx`, è la più semplice);
2. aggiungi `<Route path="/nome" element={<Nome />} />` in `App.jsx`;
3. se serve nel menu, una riga in `ITEMS` di `components/BottomNav.jsx`.

**Chiamare un nuovo endpoint** → una funzione in `api/index.js` che usa `request()`, poi nella pagina
`const { data, loading, error } = useApi(() => fetchQualcosa(), [])`.

**Cambiare un testo di errore** → oggetto `MESSAGES` in `api/client.js` (uno per ogni `code` del backend).

## Come funziona il login

1. `POST /auth/login` con le credenziali ClasseViva → token JWT, salvato in `localStorage`.
2. Ogni chiamata manda `Authorization: Bearer <token>`.
3. Se il backend risponde `401 session_expired` (server riavviato, sessione scaduta) il client rifà **da solo** il login con le credenziali
   salvate e ripete la chiamata. Se non ci riesce (es. password cambiata) l'utente torna alla schermata di accesso.
4. *Esci* dal Profilo cancella token e credenziali.

⚠️ Le credenziali restano in `localStorage` del dispositivo (scelta di progetto, serve al ri-login automatico). È accettabile
finché l'app non carica codice di terze parti non fidato: non aggiungere script esterni (analytics, widget) senza valutarne il rischio.

## Modifiche all'orario (non ancora collegate)

Banner in Home, evidenziazione arancione nell'orario, pallino sui giorni con modifiche: tutto funziona, ma i dati
vengono da `src/api/changes.js`, che per ora restituisce **dati di esempio solo in sviluppo** (in produzione restituisce una lista vuota,
così gli studenti non vedono modifiche inventate; per forzare l'esempio: `VITE_MOCK_CHANGES=true`).
Quando il backend avrà l'endpoint basta cambiare il corpo di `fetchChanges` (formato dei dati in `src/lib/changes.js`).

## Pubblicazione e installazione come app

1. `npm run build` crea `dist/`: sono file statici, vanno bene Netlify, Vercel, Cloudflare Pages o un nginx.
   Serve la regola "ogni percorso → index.html" (SPA fallback); su Netlify e Cloudflare Pages è già incluso `public/_redirects`.
2. Imposta `VITE_API_URL=https://api.tuodominio.it` prima della build (vedi `.env.example`) e metti l'indirizzo del frontend
   in `CORS_ORIGINS` del backend (`ENVIRONMENT=production` lo richiede).
3. Serve **HTTPS** (altrimenti il browser non propone l'installazione).
4. Installazione: Android/Chrome → menu ⋮ → *Installa app*. iPhone/Safari → *Condividi* → *Aggiungi alla schermata Home*.

Il service worker salva solo l'app (HTML, JS, CSS, font) per aprirla anche senza rete; i dati personali (orario, voti, agenda) **non** vengono
mai messi in cache dal browser. Gli aggiornamenti si scaricano da soli alla riapertura.

## Cosa non c'è ancora

- Notifiche push (richiedono backend + chiavi VAPID; su iOS solo con l'app installata).
- Orario personalizzato per docente, community, storico delle modifiche.
- Schermate offline con gli ultimi dati visti.
