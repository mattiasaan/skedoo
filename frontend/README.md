# Skedoo — frontend

React 19 + Vite. Nessun router o state manager esterno: la navigazione usa l'hash dell'URL e i dati passano da una piccola cache condivisa.

```bash
npm install
npm run dev            # http://localhost:5173, /api/* inoltrato al backend (vite.config.js)
npm run dev -- --host  # per provarlo dal telefono sulla stessa rete
npm test               # test della logica (vitest)
npm run lint
npm run build          # in dist/, con Content Security Policy
```

Variabili (file `.env`, vedi `.env.example`): `VITE_API_URL` indirizzo dell'API in produzione (senza `/` finale, default `/api`), `SKEDOO_API_TARGET` dove il proxy di sviluppo inoltra `/api`.

## Struttura

```text
src/
├── main.jsx             avvio: stili base, ToastProvider, App
├── App.jsx              login -> scelta classe (solo Galilei) -> dashboard; sessione scaduta
├── lib/                 logica senza interfaccia (testabile)
│   ├── api.js           unico client HTTP: token, errori {code,message}, evento 401
│   ├── useApi.js        cache in memoria condivisa + hook useApi(chiave, fetcher)
│   ├── data.js          hook dei dati (useGrades, useSchedule, useAgendaRange...) e stati locali
│   ├── session.js       localStorage: token, utente, secondo account, classe e preferenze per utente
│   ├── tokenRefresh.js  rinnovo del token (POST /auth/refresh) quando ha più di 12 ore
│   ├── routes.js        schermate e sottoschermate (#voti, #profilo/assenze...)
│   ├── schedule.js      orario del giorno: blocchi di ore, variazioni, lezione in corso
│   ├── lessons.js       registro di classe: argomenti delle lezioni abbinati all'orario, lezioni di oggi
│   ├── grades.js        medie, periodi, andamento, simulatore
│   ├── agenda.js        eventi dell'agenda -> compiti / verifiche / eventi
│   ├── format.js        date, nomi di docenti/classi/scuole, numeri
│   ├── didactics.js     materiali didattici
│   ├── appContext.js    contesto della dashboard (useApp)
│   ├── toast.js         contesto dei toast (useToast)
│   └── a11y.js          card cliccabili accessibili da tastiera
├── components/          pezzi riusati (icone, card, pannelli di dettaglio, navigazione, toast...)
├── screens/             una cartella/file per schermata
│   ├── DashboardShell.jsx   barra in alto, navigazione, route, contesto
│   ├── home/                Home Galilei e Home per le altre scuole
│   └── subpages/            Compiti, Bacheca, Presenze, Materiali
└── styles/
    ├── base.css         token del design (colori, raggi...), reset, elementi comuni
    ├── auth.css         login e scelta classe
    ├── feedback.css     toast, conferme, schermata d'errore
    └── dashboard/       un file per area; index.css li importa in ordine (responsive per ultimo)
```

## Come funziona

- **Dati.** Ogni schermata chiede i dati con un hook di `lib/data.js`. Le risposte sono in cache per 5 minuti
  e condivise: due schermate che usano `useGrades()` fanno una sola richiesta (il backend permette 20 chiamate
  a ClasseViva al minuto). `reload()` forza l'aggiornamento e restituisce `true` se è riuscito;
  `clearApiCache()` svuota tutto (logout, "Sincronizza").
- **Errori.** `api.js` trasforma ogni risposta di errore in `ApiError` con `status`, `code` e un messaggio in italiano.
  Un 401 di sessione scaduta emette `skedoo:unauthorized` e `App` torna al login.
- **Sessione.** Il token dura 7 giorni ma `App` lo rinnova all'avvio, ogni ora e quando la PWA torna in primo piano
  (solo se ha più di 12 ore): si rifà il login solo dopo 7 giorni senza usare l'app o 90 giorni dall'accesso.
- **Due account (studente e genitore).** Dal Profilo si aggiunge un secondo account ClasseViva: l'account in uso
  resta in `token`/`utente`, l'altro aspetta in `skedoo:altro-account` con il suo JWT (mai la password) e si
  rinnova insieme al primo. Cambiare account scambia i due token, svuota la cache e rimonta la dashboard (compiti
  completati e preferenze sono per utente). Il logout chiude solo l'account in uso e passa all'altro.
- **Navigazione.** La schermata è nell'hash (`#home`, `#profilo/materiali`): "indietro" e refresh funzionano.
  Per aggiungere una schermata: componente in `screens/`, voce in `SCREENS` di `DashboardShell.jsx`
  e, se è una sottoschermata, in `SUBPAGES` di `lib/routes.js`.
- **Dettagli.** Lezioni, compiti, materie, circolari e conferme si aprono con
  `openDetail({ type, ... })` dal contesto; i pannelli sono in `components/Details.jsx`.
- **Galilei / altre scuole.** Gli orari esistono solo per il Galilei di Bolzano (`isGalileiSchool`): solo loro
  scelgono la classe e vedono orario e variazioni. Le altre scuole hanno la Home con bacheca, voti e presenze.
- **Stati locali.** Compiti completati, verifiche salvate, circolari lette e preferenze sono in `localStorage`,
  separati per utente (`readJson`/`writeJson`, `usePersistentFlags`).

## Convenzioni

- Testi in italiano, nomi di variabili in inglese; commenti solo dove il perché non è ovvio.
- La logica va in `lib/` (funzioni pure, con test accanto: `*.test.js`); i componenti mostrano e basta.
- Colori e misure solo tramite i token di `styles/base.css`. Mobile first: le regole base sono per il telefono,
  `styles/dashboard/responsive.css` adatta tablet (≥600px) e desktop (≥1024px).
- Nessun HTML da stringhe (`dangerouslySetInnerHTML`): i testi della scuola sono sempre mostrati come testo.
