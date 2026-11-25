# Sicurezza

Skedoo tratta dati personali di studenti, spesso minorenni: credenziali ClasseViva, voti, assenze, agenda e iscrizioni alle notifiche push. Per questo prendiamo sul serio ogni segnalazione.

## Versioni supportate

| Versione                     | Supportata |
|------------------------------|------------|
| `main` (ultimo deploy)       | ✅         |
| Branch e commit precedenti   | ❌         |

Correggiamo solo il codice su `main` e l'istanza attualmente in produzione.

## Come segnalare una vulnerabilità

**Non aprire una issue pubblica, una discussione o una PR** per un problema di sicurezza.

Usa il **GitHub Private Vulnerability Reporting**:

1. Vai nella scheda **Security** della repository.
2. Clicca **Report a vulnerability**.
3. Compila il modulo: la segnalazione resta visibile solo a te e ai maintainer.

### Cosa includere

- Descrizione del problema e del suo impatto (quali dati o funzioni sono a rischio)
- Componente coinvolto (`backend/`, `frontend/`, `helper/`, `deploy/`)
- Passi per riprodurlo, con richieste o payload di esempio
- Versione o commit su cui l'hai trovato
- Eventuale proposta di correzione

**Non includere dati reali di altre persone** (credenziali, voti, screenshot con nomi). Se servono, usa dati finti o oscurati.

## Tempi di risposta

| Fase                                  | Obiettivo                                         |
|---------------------------------------|---------------------------------------------------|
| Conferma di ricezione                 | entro 72 ore                                      |
| Prima valutazione (gravità, impatto)  | entro 7 giorni                                    |
| Correzione                            | in base alla gravità, di solito entro 30 giorni   |

Ti terremo aggiornato nella segnalazione stessa. Quando la correzione è rilasciata pubblichiamo un advisory e, se vuoi, ti citiamo nei ringraziamenti.

## Perimetro

**Rientrano:**

- API del backend (autenticazione, sessioni, autorizzazione, rate limiting)
- Gestione e conservazione delle credenziali e dei token ClasseViva
- Notifiche Web Push (chiavi VAPID, iscrizioni)
- Pipeline OCR della bacheca e invio di dati a servizi esterni (Gemini API)
- Frontend (XSS, gestione dei token nel browser, service worker)
- Configurazione di deploy (`deploy/`: Docker Compose, Caddy)

**Non rientrano:**

- Vulnerabilità di ClasseViva/Spaggiari o di altri servizi terzi: segnalale a chi li gestisce
- Attacchi che richiedono accesso fisico al dispositivo o un account già compromesso
- DoS volumetrici, spam, social engineering
- Report automatici di scanner senza un impatto dimostrato

## Regole per i test

- Testa solo su un'istanza **locale** tua (vedi [CONTRIBUTING.md](CONTRIBUTING.md)), non sull'istanza di produzione.
- Non accedere a dati di altri utenti e non modificarli o cancellarli.
- Non degradare il servizio.
- Lascia il tempo di correggere prima di divulgare pubblicamente.

Chi rispetta queste regole è considerato in buona fede e il Titolare non intraprenderà azioni nei suoi confronti.

## Violazioni di dati personali

Se una vulnerabilità ha causato (o potrebbe aver causato) una violazione di dati personali, il Titolare segue la [procedura di gestione dei data breach](legal/procedura-data-breach.md), che comprende le valutazioni previste dal GDPR (artt. 33-34).
