# Analisi degli Errori dei Modelli Qwen-VL (2B e 4B)

Questo documento traccia esclusivamente gli errori commessi dalle intelligenze artificiali (Qwen3-VL 2B e 4B) durante i test di estrazione OCR sulle tabelle scolastiche, filtrando i falsi positivi causati dai motori classici.

## Immagine 1
**Modelli testati:** 2B, 4B
* **Errori AI:** Nessuno.
* **Esito:** Trascrizione perfetta al 100%. Sia il 2B che il 4B hanno gestito senza problemi gradi, spaziature e formattazione.

## Immagine 6
**Modelli testati:** 2B, 4B
* **Errori Modello 2B:** Nessuno. Trascrizione perfetta.
* **Errori Modello 4B:** 
    * Imprecisioni ortografiche nei testi liberi: "PALLA VOLO" (spaziato male), "GIG LIO LI" (spezzato), "TABARELLI" (manca la 'L' finale).

## Immagine 4
**Modelli testati:** 2B, 4B
* **Errori Comuni (2B e 4B):**
    * **Interferenza grafica:** La spessa linea rossa verticale ha alterato la lettura della riga `AULA B207`. Entrambi i modelli hanno perso il nome della classe e letto erroneamente l'orario `09.50` come `11:09`.
* **Errori specifici Modello 4B:**
    * Invenzione di consonanti nei nomi: "LOVECCCHIO" (invece di LOVECCHIO), "LONOCCE" (invece di LONOCE).
* **Errori specifici Modello 2B:**
    * Mancanza di un accento: "CITTA" (invece di CITTÀ).

## Immagine 8
**Modelli testati:** 2B, 4B
* **Errori Comuni (2B e 4B):**
    * **Sfondi scuri e basso contrasto:** Nella riga con evidenziazione blu scura (`AULA CALABRONE`), entrambi i modelli hanno fallito il rilevamento della classe `2 I` e allucinato l'orario `10.55` leggendolo come `21:10`.
    * **Classi implicite:** Hanno segnalato una "classe assente" nella riga gialla (`11.45 - 13.25 AULA B206`), non riuscendo a dedurre che l'orario si riferisse alla classe `3 L` della riga precedente.
* **Errori specifici Modello 4B:**
    * Sostituzione di simboli: ha convertito gli asterischi `**` nella nota di SCIBELLI in stelline piene `★★`.
* **Errori specifici Modello 2B:**