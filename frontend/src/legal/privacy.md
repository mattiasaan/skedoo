# Informativa sulla privacy

*Ultimo aggiornamento: 19 novembre 2026*

Questa informativa spiega quali dati personali tratta Skedoo, perché, per quanto tempo e quali diritti hai. È resa ai sensi degli articoli 13 e 14 del Regolamento (UE) 2016/679 ("GDPR") e del D.Lgs. 196/2003 ("Codice privacy").

In breve:

- per usare Skedoo accedi con le tue credenziali ClasseViva: la password **non viene mai salvata su disco** e sul server resta **solo cifrata**, con una chiave che si trova unicamente sul tuo dispositivo;
- voti, agenda, assenze, materiali e bacheca vengono letti da ClasseViva **quando li apri** e **non vengono archiviati** sui nostri server;
- non usiamo cookie, pubblicità, profilazione né strumenti di analisi; non vendiamo né cediamo dati a nessuno.

## 1. Titolare del trattamento

Il titolare del trattamento è **Mattia Santomaso**, persona fisica che sviluppa e gestisce Skedoo a titolo personale e non commerciale.

Per qualsiasi richiesta sulla privacy puoi aprire un issue nel repository del progetto su [GitHub](https://github.com/mattiasaan/skedoo/issues). Gli issue sono **pubblici**: non scriverci dati personali (nome, codice ClasseViva, scuola), descrivi solo il tipo di richiesta.

Skedoo è un progetto indipendente: **non è affiliato, approvato o gestito da Gruppo Spaggiari Parma S.p.A.** (che gestisce ClasseViva) **né da alcuna scuola**. Per i dati del registro elettronico il titolare resta la tua scuola: Skedoo li legge per tuo conto, con le tue credenziali, solo per mostrarli a te.

## 2. Quali dati trattiamo

### 2.1 Credenziali ClasseViva

Codice personale (o email) e password che inserisci al login. Servono ad accedere a ClasseViva per tuo conto.

- La password è trasmessa al server in modo cifrato (HTTPS) e **non viene mai scritta su disco, nei log, nel database o nel token di accesso**.
- Serve a ricollegarsi a ClasseViva quando la sessione di ClasseViva scade, per questo il server la conserva per tutta la durata della sessione, ma **solo cifrata** (AES-256) e **solo nella memoria di lavoro (RAM)**.
- La **chiave** per decifrarla viene creata a caso a ogni accesso e **non resta sul server**: è contenuta solo nel token di accesso salvato sul tuo dispositivo. La password viene decifrata solo per il tempo di una richiesta che fai tu, e subito dopo torna disponibile solo in forma cifrata.
- La password cifrata viene cancellata quando esci (logout), quando la sessione resta inattiva per più di 7 giorni o quando il server si riavvia.
- Poiché il token sul tuo dispositivo contiene la chiave, su un dispositivo condiviso ricordati di uscire (logout) quando hai finito.

### 2.2 Dati del registro elettronico

Quando apri una schermata, Skedoo legge da ClasseViva i dati che servono a mostrarla: nome, cognome e scuola; voti e materie; agenda, compiti e verifiche; assenze, ritardi e uscite; materiali didattici; comunicazioni della bacheca.

- Questi dati **non vengono salvati** nel database né su disco.
- Per alleggerire il carico su ClasseViva, ogni risposta resta in memoria sul server **per circa 60 secondi**, poi viene scartata.
- Alcuni di questi dati possono riguardare la salute o altre informazioni delicate (ad esempio il motivo di un'assenza, se inserito nel registro). Skedoo non li cerca né li elabora: li mostra soltanto, così come arrivano da ClasseViva.

### 2.3 Dati salvati sul tuo dispositivo

Nel browser (localStorage, non cookie) Skedoo salva: il token di accesso, nome, cognome e scuola, la classe scelta e alcune preferenze (avvisi attivi, comunicazioni già lette, ultima sincronizzazione, colore dell'app). I dettagli sono nella [Cookie policy](#cookie). Questi dati restano sul tuo dispositivo e non vengono inviati a nessuno, a parte il token che accompagna ogni richiesta al server.

### 2.4 Dati tecnici e di sicurezza

Come ogni servizio online, il server riceve il tuo indirizzo IP e i dati tecnici delle richieste (data e ora, pagina richiesta, esito). In particolare:

- i **log tecnici** del server registrano le richieste e, per i **tentativi di login falliti**, l'indirizzo IP e il codice personale usato;
- per proteggere il servizio da abusi (ad esempio tentativi ripetuti di indovinare una password) il server tiene in memoria, per pochi minuti, quante richieste arrivano da ciascun IP e utente.

### 2.5 Orari delle classi e variazioni (riguarda anche i docenti)

Per il solo ITT "G. Galilei" di Bolzano, Skedoo mostra l'orario delle classi e le variazioni giornaliere (entrate posticipate, uscite anticipate, cambi d'aula). Questi dati comprendono **nomi e cognomi dei docenti** e sono ricavati dall'orario pubblicato dalla scuola e dalle comunicazioni della bacheca ClasseViva, lette in automatico con un sistema di riconoscimento del testo (OCR) che gira **interamente sui nostri server**, senza servizi esterni di intelligenza artificiale.

Se sei un docente e vuoi esercitare i tuoi diritti su questi dati, usa il contatto indicato al punto 1.

## 3. Perché trattiamo i dati e su quale base giuridica

| Finalità | Base giuridica (art. 6 GDPR) |
|---|---|
| Accedere a ClasseViva e mostrarti i tuoi dati scolastici (punti 2.1, 2.2, 2.3) | Esecuzione del servizio che hai richiesto (art. 6.1.b) |
| Sicurezza del servizio, prevenzione degli abusi, risoluzione di problemi tecnici (punto 2.4) | Legittimo interesse a mantenere il servizio sicuro e funzionante (art. 6.1.f) |
| Mostrare orari e variazioni con i nomi dei docenti (punto 2.5) | Legittimo interesse degli studenti a conoscere l'organizzazione delle lezioni (art. 6.1.f); i dati provengono da fonti già messe a disposizione dalla scuola |
| Rispondere a richieste e difendere i propri diritti | Obblighi di legge e legittimo interesse (art. 6.1.c e 6.1.f) |

Eventuali dati sanitari o particolari presenti nel registro (punto 2.2) non vengono elaborati né conservati: sono solo visualizzati a te, su tua richiesta, nell'ambito del servizio.

Skedoo **non** prende decisioni automatizzate che producano effetti giuridici su di te. Le funzioni di calcolo (per esempio la media o la stima del voto necessario) sono semplici calcoli mostrati solo a te.

## 4. Per quanto tempo conserviamo i dati

| Dato | Conservazione |
|---|---|
| Password ClasseViva | Solo cifrata, in memoria (RAM), fino al logout, a 7 giorni di inattività o al riavvio del server; la chiave resta solo sul tuo dispositivo |
| Dati del registro (voti, agenda, assenze...) | In memoria per circa 60 secondi, poi scartati |
| Token di accesso | Valido al massimo 7 giorni; cancellato dal dispositivo al logout |
| Dati sul tuo dispositivo | Finché esci o cancelli i dati del sito dal browser (classe e preferenze restano anche dopo il logout, finché non li cancelli) |
| Contatori anti-abuso | In memoria, da 1 a 60 minuti |
| Log tecnici del server | Sovrascritti automaticamente a rotazione, e comunque non oltre 30 giorni |
| Orari e variazioni delle classi | Per l'anno scolastico in corso; le variazioni dei giorni passati vengono eliminate in automatico |

## 5. A chi vengono comunicati i dati

I dati non vengono venduti, ceduti o usati per pubblicità. Vengono trattati dal titolare e da un collaboratore autorizzato allo sviluppo, vincolato alla riservatezza. Per far funzionare il servizio ci appoggiamo inoltre a questi fornitori:

- **Gruppo Spaggiari Parma S.p.A. (ClasseViva)**: è il servizio da cui leggiamo i tuoi dati, con le tue credenziali. Spaggiari tratta i dati del registro per conto della tua scuola, secondo la propria informativa.
- **GitHub, Inc. (GitHub Pages)**: ospita l'interfaccia dell'app (i file della pagina web). Riceve l'indirizzo IP e i dati tecnici di chi apre il sito. Non riceve credenziali né dati scolastici.
- **Cloudflare, Inc.**: instrada in modo sicuro il traffico verso il nostro server (Cloudflare Tunnel) e lo protegge dagli attacchi. Il traffico, comprese le richieste di login, transita cifrato attraverso la sua rete.
- **Google LLC (Google Fonts)**: fornisce il carattere tipografico dell'app. Il browser scarica il font dai server di Google, che ricevono il tuo indirizzo IP.

Il server dell'applicazione e il database si trovano in Italia, su hardware gestito direttamente dal titolare.

## 6. Trasferimenti fuori dall'Unione europea

GitHub, Cloudflare e Google hanno sede negli Stati Uniti e possono trattare dati tecnici (in particolare l'indirizzo IP) anche fuori dall'UE. Le tre società aderiscono all'EU-U.S. Data Privacy Framework, riconosciuto adeguato dalla Commissione europea (decisione del 10 luglio 2023), e applicano inoltre le Clausole contrattuali standard approvate dalla Commissione.

## 7. Minori

Skedoo è pensato anche per studenti minorenni. Se hai **meno di 14 anni** puoi usare Skedoo solo con il permesso di un genitore o di chi esercita la responsabilità genitoriale. Chi ha almeno 14 anni può usarlo autonomamente (art. 2-quinquies del Codice privacy).

## 8. Sicurezza

Adottiamo misure tecniche e organizzative adeguate: connessioni cifrate (HTTPS), password mai scritte su disco e conservate in memoria solo cifrate con una chiave che il server non conserva, token firmati con scadenza, limiti ai tentativi di login, isolamento dei servizi in container con permessi minimi, accesso al server riservato al titolare. Nessun sistema è però sicuro al 100%: in caso di violazione dei dati che possa mettere a rischio i tuoi diritti, ti informeremo come previsto dalla legge.

## 9. I tuoi diritti

In ogni momento puoi chiedere di:

- **accedere** ai tuoi dati e riceverne copia (art. 15);
- **rettificarli** (art. 16) o **cancellarli** (art. 17);
- **limitarne** il trattamento (art. 18);
- riceverli in un formato leggibile (**portabilità**, art. 20);
- **opporti** ai trattamenti basati sul legittimo interesse (art. 21).

Usa il contatto indicato al punto 1, senza scrivere dati personali nell'issue: risponderemo entro un mese. Dato che Skedoo non archivia i tuoi dati scolastici, nella maggior parte dei casi basta uscire dall'app (logout) e cancellare i dati del sito dal browser per eliminare ogni traccia. Per i dati del registro elettronico devi rivolgerti alla tua scuola.

Hai inoltre il diritto di proporre **reclamo al Garante per la protezione dei dati personali** (www.garanteprivacy.it), Piazza Venezia 11, 00187 Roma.

## 10. Modifiche

Se l'informativa cambia in modo rilevante lo segnaleremo nell'app. La data dell'ultimo aggiornamento è indicata in alto.
