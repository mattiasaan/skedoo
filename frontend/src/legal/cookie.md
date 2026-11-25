# Cookie policy

*Ultimo aggiornamento: 25 novembre 2026*

## Skedoo non usa cookie

Skedoo **non installa cookie** sul tuo dispositivo: né cookie tecnici, né di profilazione, né di analisi, né di terze parti a scopo pubblicitario. Per questo non ti viene mostrato alcun banner per il consenso.

## Cosa salviamo nel browser

Per funzionare, l'app salva alcune informazioni nella **memoria locale del browser** (localStorage). Si tratta solo di strumenti tecnici, strettamente necessari a fornire il servizio che hai richiesto. Per legge non richiedono il tuo consenso (art. 122 del D.Lgs. 196/2003 e Linee guida del Garante privacy del 10 giugno 2021).

| Nome | Cosa contiene | Quanto dura |
|---|---|---|
| `token` | Il token che ti tiene collegato. Non contiene la password, ma la chiave che la sblocca sul server | Fino al logout; scade dopo 7 giorni senza usare l'app e comunque dopo 90 giorni dall'accesso |
| `utente` | Nome, cognome e scuola, per mostrarli subito all'avvio | Fino al logout |
| `skedoo:altro-account` | Solo se aggiungi un secondo account (studente e genitore): il suo token e il suo profilo, per passare da un account all'altro senza password | Fino al logout da quell'account |
| `skedoo:ultimo-accesso` | Codice personale e nome, solo se la sessione scade da sola: li ritrovi già inseriti e ti basta la password | Fino al nuovo accesso o al logout |
| `skedoo:class:<utente>` | La classe che hai scelto (solo ITT Galilei) | Finché non cancelli i dati del sito |
| `skedoo:<utente>:pref-alerts` | Se gli avvisi sono attivi | Finché non cancelli i dati del sito |
| `skedoo:<utente>:pref-push` | Se hai attivato le notifiche push su questo dispositivo | Finché non cancelli i dati del sito |
| `skedoo:<utente>:notifications-seen` | Quali comunicazioni hai già letto | Finché non cancelli i dati del sito |
| `skedoo:<utente>:last-sync` | Data dell'ultima sincronizzazione | Finché non cancelli i dati del sito |
| `skedoo-accent` | Il colore dell'app che hai scelto | Finché non cancelli i dati del sito |

Se attivi le notifiche push, il browser registra anche un **service worker** di Skedoo: un piccolo script che serve solo
a mostrare le notifiche quando l'app è chiusa. Non salva dati e non traccia la navigazione. Il browser lo elimina quando
cancelli i dati del sito.

Questi dati restano sul tuo dispositivo e **non vengono letti da terze parti**. Il token viene inviato solo al server di Skedoo, insieme a ogni richiesta, per dimostrare che sei collegato.

## Servizi di terze parti

Nessuno: l'app non carica contenuti da altri siti. Anche il carattere tipografico (Inter) è incluso nell'app e arriva dallo stesso indirizzo della pagina.

## Come cancellare i dati

- **Esci dall'app** (Profilo, poi Esci): vengono cancellati il token e i dati del profilo dell'account in uso. Se avevi aggiunto un secondo account, l'app passa a quello: esci anche da lì per cancellarlo.
- Per cancellare anche classe e preferenze, elimina i dati del sito dalle impostazioni del browser (di solito: Impostazioni, Privacy, Dati dei siti). Usando la navigazione privata, tutto viene cancellato alla chiusura della finestra.

Per qualsiasi domanda leggi l'[Informativa privacy](#privacy), dove trovi anche come contattarci.
