# Skedoo

**Skedoo** è una webapp che centralizza **orari scolastici, comunicazioni e modifiche giornaliere** in un'unica app moderna per studenti e professori.
Il progetto nasce per risolvere un problema comune nelle scuole: informazioni frammentate tra **PDF statici, immagini nella bacheca e notifiche poco chiare**.
Skedoo trasforma questi dati in un sistema **interattivo, aggiornato e notificabile in tempo reale**.

# Cosa Fa
Skedoo permette di:
* 📅 Visualizzare l'orario scolastico in formato **digitale e interattivo**
* 🔄 Ricevere **modifiche automatiche** (assenze docenti, supplenze, cambi aula)
* 🔔 Ricevere **notifiche mirate**
* 📊 Evidenziare differenze tra **orario standard e modifiche giornaliere**
* 💬 Accedere a una **community scolastica interna**
* 🏆 Utilizzare un sistema di **gamification per engagement**

# ⚙️ Come Funziona
Skedoo raccoglie e normalizza le informazioni scolastiche provenienti da:

* PDF degli orari
* comunicazioni pubblicate su ClasseViva

### Processo

1. Parsing del **PDF dell'orario scolastico**
2. Conversione in **struttura dati**
3. Salvataggio nel **database**
4. Sincronizzazione delle **modifiche giornaliere**
5. Confronto automatico con l'orario base

# Tech Stack

## Backend

* **Python**
* **FastAPI**
* **PostgreSQL**
* **SQLAlchemy**
* **JWT Authentication**

Integrazione con:

* `Classeviva.py` per accesso alle API di ClasseViva

## Frontend

* **React**
* **Responsive UI**
* **Push Notifications**

# Sicurezza

* Autenticazione tramite ClasseViva
* JWT authentication
* Validazione input
* Rate limiting
* Moderazione contenuti (forse)

# Stato del Progetto

**Work in Progress**

Skedoo è attualmente in fase di sviluppo come progetto scolastico.
