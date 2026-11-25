# Informativa sulla privacy

*Ultimo aggiornamento: 25 novembre 2026*

Questa informativa spiega quali dati personali tratta Skedoo, perché, per quanto tempo e quali diritti hai. È resa ai sensi degli articoli 13 e 14 del Regolamento (UE) 2016/679 ("GDPR") e del D.Lgs. 196/2003 ("Codice privacy").

In breve:

- per usare Skedoo accedi con le tue credenziali ClasseViva: la password **non viene mai salvata su disco** e sul server resta **solo cifrata**, con una chiave che si trova unicamente sul tuo dispositivo;
- voti, agenda, assenze, materiali e bacheca vengono letti da ClasseViva **quando li apri** e **non vengono archiviati** sui nostri server;
- non usiamo cookie, pubblicità, profilazione né strumenti di analisi; non vendiamo né cediamo dati a nessuno.

## 1. Titolare del trattamento

Il titolare del trattamento è **Mattia Santomaso**, persona fisica che sviluppa e gestisce Skedoo a titolo personale e non commerciale.

Per qualsiasi richiesta sulla privacy puoi aprire un issue nel repository del progetto su [GitHub](https://github.com/mattiasaan/skedoo/issues). Gli issue sono **pubblici**: scrivi solo il tipo di richiesta (per esempio "accesso ai dati" o "opposizione"), **senza dati personali** (nome, codice ClasseViva, scuola). Ti indicheremo nell'issue un canale privato dove completare la richiesta.

Skedoo è un progetto indipendente: **non è affiliato, approvato o gestito da Gruppo Spaggiari Parma S.p.A.** (che gestisce ClasseViva) **né da alcuna scuola**. Per i dati del registro elettronico il titolare resta la tua scuola: Skedoo li legge per tuo conto, con le tue credenziali, solo per mostrarli a te.

## 2. Quali dati trattiamo

### 2.1 Credenziali ClasseViva

Codice personale (o email) e password che inserisci al login. Servono ad accedere a ClasseViva per tuo conto.

- La password è trasmessa al server in modo cifrato (HTTPS) e **non viene mai scritta su disco, nei log, nel database o nel token di accesso**.
- Serve a ricollegarsi a ClasseViva quando la sessione di ClasseViva scade, per questo il server la conserva per tutta la durata della sessione, ma **solo cifrata** (AES-256) e **solo nella memoria di lavoro (RAM)**.
- La **chiave** per decifrarla viene creata a caso a ogni accesso e **non resta sul server**: è contenuta solo nel token di accesso salvato sul tuo dispositivo. La password viene decifrata solo per il tempo di una richiesta che fai tu, e subito dopo torna disponibile solo in forma cifrata.
- La password cifrata viene cancellata quando esci (logout), quando la sessione resta inattiva per più di 7 giorni, quando il server si riavvia o quando accedi con lo stesso account da più di 10 dispositivi (si chiude la sessione usata meno di recente).
- Poiché il token sul tuo dispositivo contiene la chiave, su un dispositivo condiviso ricordati di uscire (logout) quando hai finito.

Fornire le credenziali è necessario per usare Skedoo: senza non è possibile accedere al servizio.

### 2.2 Dati del registro elettronico

Quando apri una schermata, Skedoo legge da ClasseViva i dati che servono a mostrarla: nome, cognome e scuola; voti e materie; agenda, compiti e verifiche; assenze, ritardi e uscite; lezioni e argomenti; materiali didattici; comunicazioni della bacheca.

- Questi dati **non vengono salvati** nel database né su disco. I file che scarichi (allegati e materiali) passano dal server a pezzi, senza essere salvati.
- Per alleggerire il carico su ClasseViva, ogni risposta resta in memoria sul server **per circa 60 secondi**, poi viene scartata.
- Il **motivo delle giustificazioni** delle assenze (che può riguardare la salute) viene scartato appena arriva da ClasseViva: Skedoo non lo mostra e non lo conserva, nemmeno per quei 60 secondi.
- Altri contenuti del registro (per esempio le note dei docenti o le comunicazioni) potrebbero contenere informazioni delicate: Skedoo non li cerca né li elabora, li mostra soltanto a te, così come arrivano da ClasseViva.

### 2.3 Dati salvati sul tuo dispositivo

Nel browser (localStorage, non cookie) Skedoo salva: il token di accesso, nome, cognome e scuola, la classe scelta e alcune preferenze (avvisi e notifiche push attivi, comunicazioni già lette, ultima sincronizzazione, colore dell'app); se aggiungi un secondo account (studente e genitore), anche il suo token e il suo profilo. I dettagli sono nella [Cookie policy](#cookie). Questi dati restano sul tuo dispositivo e non vengono inviati a nessuno, a parte il token che accompagna ogni richiesta al server.

### 2.4 Dati tecnici e di sicurezza

Come ogni servizio online, il server riceve il tuo indirizzo IP e i dati tecnici delle richieste (data e ora, pagina richiesta, esito). In particolare:

- per i **tentativi di login falliti** i log tecnici del server registrano l'indirizzo IP e uno **pseudonimo** del codice personale usato (un codice che non permette di risalire al codice personale senza una chiave segreta del server);
- per proteggere il servizio da abusi (ad esempio tentativi ripetuti di indovinare una password) il server tiene in memoria, da pochi minuti a un'ora, quante richieste arrivano da ciascun IP e utente.

### 2.5 Orari delle classi e variazioni (riguarda anche i docenti)

Per il solo ITT "G. Galilei" di Bolzano, Skedoo mostra l'orario delle classi e le variazioni giornaliere (entrate posticipate, uscite anticipate, cambi d'aula). Questi dati comprendono **nomi e cognomi dei docenti** e sono ricavati dall'orario della scuola e dalle comunicazioni della bacheca ClasseViva, lette in automatico con un sistema di riconoscimento del testo (OCR). Sono visibili **solo agli utenti di quella scuola**.

- Del cartellone della bacheca si conservano l'immagine e il risultato della lettura **per al massimo 30 giorni**; si leggono solo le comunicazioni degli ultimi 14 giorni.
- Le variazioni dei giorni passati vengono eliminate in automatico.

Il sistema OCR può funzionare interamente sui nostri server oppure, come avviene attualmente, appoggiandosi al servizio di intelligenza artificiale **Gemini API di Google LLC**:

- l'immagine del cartellone viene prima divisa in ritagli sui nostri server, e a Google vengono inviati **solo** il titolo con la data, i riquadri delle entrate posticipate, delle uscite anticipate e dei pomeriggi senza lezione, e le righe dei cambi d'aula. Questi ritagli contengono classi, aule, orari e le note scritte nei riquadri, che possono comprendere il **cognome di un docente** (per esempio "ROSSI posticipa 1ª a 3ª");
- i riquadri informativi (per esempio docenti assenti, FSL, uscite e viaggi) **non vengono letti né inviati**;
- ogni immagine viene inviata una sola volta: il risultato resta salvato sui nostri server (al massimo 30 giorni) e non viene richiesto di nuovo;
- a Google non arriva **alcun dato degli utenti di Skedoo** (credenziali, voti, assenze, classe scelta): solo il contenuto dei cartelloni pubblicati dalla scuola in bacheca;
- secondo i termini di Google per chi usa Gemini API dallo Spazio economico europeo, Google non usa questi contenuti per migliorare i propri prodotti e li conserva per un periodo limitato, solo per prevenire abusi.

Se sei un docente puoi esercitare i tuoi diritti su questi dati, compresa l'**opposizione** (punto 9), usando il contatto indicato al punto 1.

### 2.6 Notifiche push (facoltative)

Se attivi le notifiche push dal Profilo (solo per gli studenti dell'ITT Galilei), il browser crea un'**iscrizione** per il tuo dispositivo e Skedoo la salva nel database insieme alla **classe** scelta. L'iscrizione è composta dall'indirizzo del servizio di notifiche del tuo browser e da due chiavi di cifratura. **Non contiene nome, codice ClasseViva, password né altri dati del registro**.

- Le notifiche riguardano solo le variazioni d'orario della classe (entrate posticipate, uscite anticipate, cambi d'aula), cioè gli stessi dati descritti al punto 2.5.
- Le consegna il servizio di notifiche scelto dal tuo browser, non da Skedoo: Google (Chrome, Edge su Android e la maggior parte dei browser Android), Mozilla (Firefox), Microsoft (Edge su Windows) o Apple (Safari). Il contenuto è **cifrato per il tuo dispositivo**: questi servizi non possono leggerlo, ma vedono che una notifica viene consegnata.
- Per non inviare due volte la stessa variazione, il server ricorda quali variazioni ha già notificato a ogni classe (senza alcun riferimento alle persone) e lo cancella quando quel giorno è passato.
- Puoi disattivarle in qualsiasi momento dal Profilo o dalle impostazioni del browser. L'iscrizione viene cancellata quando le disattivi, quando esci (logout) o quando il servizio di notifiche la segnala come non più valida.

## 3. Perché trattiamo i dati e su quale base giuridica

| Finalità | Base giuridica (art. 6 GDPR) |
|---|---|
| Accedere a ClasseViva e mostrarti i tuoi dati scolastici (punti 2.1, 2.2, 2.3) | Esecuzione del servizio che hai richiesto (art. 6.1.b) |
| Sicurezza del servizio, prevenzione degli abusi, risoluzione di problemi tecnici (punto 2.4) | Legittimo interesse a mantenere il servizio sicuro e funzionante (art. 6.1.f) |
| Inviarti le notifiche push che hai attivato (punto 2.6) | Esecuzione del servizio che hai richiesto (art. 6.1.b) |
| Mostrare orari e variazioni con i nomi dei docenti agli studenti della scuola (punto 2.5) | Legittimo interesse degli studenti a conoscere l'organizzazione delle lezioni (art. 6.1.f); i dati provengono da fonti che la scuola mette a disposizione dei propri studenti |
| Rispondere a richieste e difendere i propri diritti | Obblighi di legge e legittimo interesse (art. 6.1.c e 6.1.f) |

Skedoo **non** prende decisioni automatizzate che producano effetti giuridici su di te. Le funzioni di calcolo (per esempio la media o la stima del voto necessario) sono semplici calcoli mostrati solo a te.

## 4. Per quanto tempo conserviamo i dati

| Dato | Conservazione |
|---|---|
| Password ClasseViva | Solo cifrata, in memoria (RAM), fino al logout, a 7 giorni di inattività, al riavvio del server o all'accesso da più di 10 dispositivi; la chiave resta solo sul tuo dispositivo |
| Dati del registro (voti, agenda, assenze...) | In memoria per circa 60 secondi, poi scartati; il motivo delle giustificazioni non viene conservato |
| Token di accesso | Rinnovato mentre usi l'app: scade dopo 7 giorni di inattività e comunque dopo 90 giorni dall'accesso; cancellato dal dispositivo al logout |
| Dati sul tuo dispositivo | Finché esci o cancelli i dati del sito dal browser (classe e preferenze restano anche dopo il logout, finché non li cancelli) |
| Contatori anti-abuso | In memoria, da 1 a 60 minuti |
| Log tecnici del server | Cancellati automaticamente dopo 30 giorni |
| Iscrizione alle notifiche push | Finché non le disattivi, esci (logout) o il servizio di notifiche la segnala come scaduta |
| Variazioni già notificate (per classe) | Fino alla fine del giorno della variazione |
| Orari delle classi | Per l'anno scolastico in corso |
| Variazioni d'orario | Fino alla fine del giorno della variazione |
| Immagini dei cartelloni e risultati dell'OCR | Al massimo 30 giorni |

## 5. A chi vengono comunicati i dati

I dati non vengono venduti, ceduti o usati per pubblicità. Vengono trattati dal titolare e da un collaboratore autorizzato allo sviluppo, vincolato alla riservatezza. Per far funzionare il servizio ci appoggiamo inoltre a questi fornitori:

- **Gruppo Spaggiari Parma S.p.A. (ClasseViva)**: è il servizio da cui leggiamo i tuoi dati, con le tue credenziali. Spaggiari tratta i dati del registro per conto della tua scuola, secondo la propria informativa.
- **GitHub, Inc. (GitHub Pages)**: ospita l'interfaccia dell'app (i file della pagina web, compreso il carattere tipografico). Riceve l'indirizzo IP e i dati tecnici di chi apre il sito. Non riceve credenziali né dati scolastici.
- **Cloudflare, Inc.**: instrada in modo sicuro il traffico verso il nostro server (Cloudflare Tunnel) e lo protegge dagli attacchi. Il traffico, comprese le richieste di login, transita cifrato attraverso la sua rete.
- **Servizi di notifiche push dei browser** (Google, Mozilla, Microsoft, Apple), solo se attivi le notifiche: ricevono il contenuto cifrato della notifica e l'indirizzo dell'iscrizione, e la consegnano al tuo dispositivo (punto 2.6).
- **Google LLC (Gemini API)**: legge il testo dei ritagli dei cartelloni della bacheca per ricavare le variazioni d'orario (punto 2.5). Non riceve dati degli utenti di Skedoo.

Il server dell'applicazione e il database si trovano in Italia, su hardware gestito direttamente dal titolare.

## 6. Trasferimenti fuori dall'Unione europea

GitHub, Cloudflare e Google hanno sede negli Stati Uniti e possono trattare dati tecnici (in particolare l'indirizzo IP) anche fuori dall'UE; Google tratta fuori dall'UE anche i ritagli dei cartelloni inviati a Gemini API (punto 2.5). Le tre società aderiscono all'EU-U.S. Data Privacy Framework, riconosciuto adeguato dalla Commissione europea (decisione del 10 luglio 2023), e applicano inoltre le Clausole contrattuali standard approvate dalla Commissione.

Anche i servizi di notifiche push dei browser (punto 2.6) possono trovarsi fuori dall'UE: ricevono però solo contenuti cifrati, che non possono leggere.

## 7. Minori

Skedoo è pensato anche per studenti minorenni. Se hai **meno di 14 anni** puoi usare Skedoo solo con il permesso di un genitore o di chi esercita la responsabilità genitoriale. Chi ha almeno 14 anni può usarlo autonomamente (art. 2-quinquies del Codice privacy).

## 8. Sicurezza

Adottiamo misure tecniche e organizzative adeguate: connessioni cifrate (HTTPS), password mai scritte su disco e conservate in memoria solo cifrate con una chiave che il server non conserva, token firmati con scadenza, limiti ai tentativi di login, log con pseudonimi al posto dei codici personali, isolamento dei servizi in container con permessi minimi, accesso al server riservato al titolare. Nessun sistema è però sicuro al 100%: in caso di violazione dei dati che possa mettere a rischio i tuoi diritti, ti informeremo come previsto dalla legge.

## 9. I tuoi diritti

In ogni momento puoi chiedere di:

- **accedere** ai tuoi dati e riceverne copia (art. 15);
- **rettificarli** (art. 16) o **cancellarli** (art. 17);
- **limitarne** il trattamento (art. 18);
- riceverli in un formato leggibile (**portabilità**, art. 20);
- **opporti** ai trattamenti basati sul legittimo interesse (art. 21), compresi quelli che riguardano i docenti (punto 2.5).

Usa il contatto indicato al punto 1, senza scrivere dati personali nell'issue: risponderemo entro un mese. Dato che Skedoo non archivia i tuoi dati scolastici, nella maggior parte dei casi basta uscire dall'app (logout) e cancellare i dati del sito dal browser per eliminare ogni traccia. Per i dati del registro elettronico devi rivolgerti alla tua scuola.

Hai inoltre il diritto di proporre **reclamo al Garante per la protezione dei dati personali** (www.garanteprivacy.it), Piazza Venezia 11, 00187 Roma.

## 10. Modifiche

Se l'informativa cambia in modo rilevante lo segnaleremo nell'app. La data dell'ultimo aggiornamento è indicata in alto.
