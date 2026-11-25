# Documentazione legale di Skedoo

| Documento | Pubblico? | Dove |
|---|---|---|
| Informativa privacy | Sì | [frontend/src/legal/privacy.md](../frontend/src/legal/privacy.md), nell'app su `#privacy` |
| Cookie policy | Sì | [frontend/src/legal/cookie.md](../frontend/src/legal/cookie.md), nell'app su `#cookie` |
| Termini di servizio | Sì | [frontend/src/legal/termini.md](../frontend/src/legal/termini.md), nell'app su `#termini` |
| Registro dei trattamenti | **No** | [registro-trattamenti.md](registro-trattamenti.md) |
| Procedura data breach | **No** | [procedura-data-breach.md](procedura-data-breach.md) |
| Valutazione d'impatto (DPIA) | **No** | [dpia.md](dpia.md) |

I documenti pubblici sono i file Markdown usati dall'app: se li modifichi, cambia anche la data "Ultimo aggiornamento".

I documenti interni sono esclusi da git (`.gitignore`) perché il repository è pubblico: restano solo su questo computer, quindi **fanne una copia di backup** (per esempio su un cloud privato).

> Questi documenti sono una base accurata rispetto al codice al 25/11/2026, **non una consulenza legale**. Prima dell'apertura al pubblico conviene farli rileggere a un professionista (anche uno sportello gratuito, ad esempio quello di un'associazione di consumatori o di un ordine degli avvocati).

## Regola per il repository (pubblico)

**Mai dati personali di persone reali** nel repository, neanche nei test: immagini dei cartelloni, PDF o JSON
dell'orario, risposte vere di ClasseViva, nomi di docenti o studenti. Nei test si usano nomi inventati
(ROSSI Mario, BIANCHI Anna, ...). Immagini e orario servono solo in locale e sono in `.gitignore`.

## Da fare prima di pubblicare

- [x] Titolare indicato (Mattia Santomaso). Contatto: issue su GitHub.
- [ ] **Gemini API e minorenni.** I termini di Google (Gemini API Additional Terms, in vigore dal 23/03/2026) vietano di
  usare le API in un servizio "rivolto o che probabilmente sarà usato da minori di 18 anni" e, per utenti nello SEE,
  permettono solo i servizi a pagamento. Skedoo è usato da studenti minorenni: con Gemini (anche a pagamento) il
  servizio viola il contratto con Google, che può revocare la chiave. Serve un OCR diverso: locale sul server (come la
  V4) oppure un fornitore i cui termini ammettano servizi usati da minori, con un accordo sul trattamento (art. 28).
- [ ] Sostituire `[NOME E COGNOME DEL COLLABORATORE]` nel registro dei trattamenti.
- [ ] **Consigliato:** creare un indirizzo email dedicato a Skedoo e usarlo come contatto privacy al posto degli issue di GitHub, che sono pubblici: chi vuole esercitare un diritto non dovrebbe dover scrivere in pubblico (oggi l'informativa chiede di indicare solo il tipo di richiesta e di proseguire su un canale privato).
- [ ] Far firmare al collaboratore l'autorizzazione (modello in fondo al registro).
- [ ] **Leggere le condizioni d'uso di ClasseViva/Spaggiari.** È il rischio legale più grande: se vietano l'accesso tramite app di terze parti o la cessione delle credenziali, Spaggiari può bloccare il servizio o contestarlo, e nessuna informativa ti mette al riparo da questo. Valutare anche di chiedere alla scuola un riconoscimento del progetto.
- [ ] **Chiedere alla scuola** se è d'accordo che gli orari con i nomi dei docenti e le variazioni della bacheca siano mostrati in Skedoo (è la scuola il titolare di quei dati).
- [ ] Sul Raspberry: installare `deploy/journald-skedoo.conf` (log a 30 giorni, vedi `deploy/README.md`).

## Già sistemato nel codice (25/11/2026)

- Log al massimo 30 giorni (journald); nessun access log su Caddy; nei login falliti uno pseudonimo al posto del codice personale.
- Google Fonts eliminato: il font è servito dall'app (CSP `font-src 'self'`).
- Motivo delle giustificazioni (dato sulla salute) scartato appena arriva da ClasseViva.
- Sessioni e cache in memoria ripulite ogni 30 secondi: le durate dell'informativa valgono anche senza nuovi login.
- Orari, variazioni e notifiche push accessibili solo agli utenti dell'ITT Galilei (controllo anche sul server).
- Immagini dei cartelloni e letture OCR cancellate dopo 30 giorni; si leggono solo le comunicazioni degli ultimi 14.
- Immagini dei cartelloni, PDF dell'orario e nomi reali dei docenti tolti dal repository e dalla sua storia.

## Da tenere a mente

- [ ] Se cambi hosting (per esempio niente più Cloudflare, oppure un VPS fuori dall'Italia), aggiornare il punto 5 dell'informativa e il registro.
- [ ] Se aggiungi analytics, account o salvataggi sul server, o cambi cosa ricevono i servizi esterni (push, OCR): **prima** aggiornare le policy (alcune di queste cose richiedono il consenso).
