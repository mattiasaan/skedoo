# Documentazione legale di Skedoo

| Documento | Pubblico? | Dove |
|---|---|---|
| Informativa privacy | Sì | [frontend/src/legal/privacy.md](../frontend/src/legal/privacy.md), nell'app su `#privacy` |
| Cookie policy | Sì | [frontend/src/legal/cookie.md](../frontend/src/legal/cookie.md), nell'app su `#cookie` |
| Termini di servizio | Sì | [frontend/src/legal/termini.md](../frontend/src/legal/termini.md), nell'app su `#termini` |
| Registro dei trattamenti | **No** | [registro-trattamenti.md](registro-trattamenti.md) |
| Procedura data breach | **No** | [procedura-data-breach.md](procedura-data-breach.md) |

I documenti pubblici sono i file Markdown usati dall'app: se li modifichi, cambia anche la data "Ultimo aggiornamento".

I due documenti interni sono esclusi da git (`.gitignore`) perché il repository è pubblico: restano solo su questo computer, quindi **fanne una copia di backup** (per esempio su un cloud privato).

> Questi documenti sono una base accurata rispetto al codice al 19/11/2026, **non una consulenza legale**. Prima dell'apertura al pubblico conviene farli rileggere a un professionista (anche uno sportello gratuito, ad esempio quello di un'associazione di consumatori o di un ordine degli avvocati).

## Da fare prima di pubblicare

- [x] Titolare indicato (Mattia Santomaso). Contatto: issue su GitHub.
- [ ] Sostituire `[NOME E COGNOME DEL COLLABORATORE]` nel registro dei trattamenti.
- [ ] **Consigliato:** creare un indirizzo email dedicato a Skedoo e usarlo come contatto privacy al posto degli issue di GitHub, che sono pubblici: chi vuole esercitare un diritto non dovrebbe dover scrivere in pubblico.
- [ ] Far firmare al collaboratore l'autorizzazione (modello in fondo al registro).
- [ ] **Leggere le condizioni d'uso di ClasseViva/Spaggiari.** È il rischio legale più grande: se vietano l'accesso tramite app di terze parti o la cessione delle credenziali, Spaggiari può bloccare il servizio o contestarlo, e nessuna informativa ti mette al riparo da questo. Valutare anche di chiedere alla scuola un riconoscimento del progetto.

## Da sistemare nel codice o nella configurazione (perché le policy restino vere)

- [ ] **Log al massimo 30 giorni:** le policy lo promettono, ma oggi i log Docker ruotano per dimensione (10 MB x 3), non per tempo. Con poco traffico possono restare più a lungo. Soluzione semplice: un cron settimanale che riavvia i container o svuota i log più vecchi di 30 giorni; in alternativa, cambiare la promessa nelle policy.
- [ ] **Google Fonts:** servire il font Inter dall'app stessa (pacchetto `@fontsource-variable/inter`) elimina l'invio dell'IP a Google. Fatto questo, togliere Google dalle policy, dal registro e dalla CSP in `vite.config.js`.
- [ ] Se cambi hosting (per esempio niente più Cloudflare, oppure un VPS fuori dall'Italia), aggiornare il punto 5 dell'informativa e il registro.
- [ ] Se aggiungi analytics, notifiche push, account o salvataggi sul server: **prima** aggiornare le policy (alcune di queste cose richiedono il consenso).
