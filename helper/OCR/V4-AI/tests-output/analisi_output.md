## 1. Metriche Aggregate di Test

| Immagine di Test | Dissensi (OCR vs AI) | Elementi da Verif. | Accuratezza AI (Stima) | Accuratezza OCR (Stima) |
| :--- | :---: | :---: | :---: | :---: |
| **img-new.png** | 6 | 7 | 100% | ~75% |
| **img6.jpg** | 4 | 9 | ~98% | ~70% |
| **img4.jpg** | 6 | 11 | ~95% | ~70% |
| **img8.jpg** | 4 | 9 | ~96% | ~75% |

*Nota: I "dissensi" registrati dal sistema sono stati causati nel 100% dei casi da errori di lettura dei motori OCR classici.*

## 2. Tipologia e Frequenza degli Errori

### Motori OCR Classici (Tesseract, RapidOCR)
Tasso di errore strutturale elevato dovuto alla dipendenza dai *bounding box*.

* **Cecità al Layout (100% di fallimento su margini stretti):** Unione di colonne e classi (es. `11OD-2E`, `1F5L`).
* **Decodifica Simboli (Tasso errore ~100% su gradi e apici):** I gradi (`°`) vengono sistematicamente interpretati come zeri o lettere (es. `1°` letto come `1 30`, `10` o `4JO`).
* **Allucinazioni Strutturali:** Inserimento di caratteri fantasma (es. `15J`, `15K`, `4AL`) e collasso su blocchi di testo fitto (es. `SA i NO`).

### Modelli AI (Qwen3-VL 2B, 4B)
Alta precisione semantica (mantiene le relazioni riga-colonna), ma sensibile a specifici artefatti visivi.

* **Interferenze Grafiche (Tasso errore critico):**
  * *Linee divisorie marcate:* Su `img4.jpg`, una linea rossa spessa ha indotto l'AI a leggere un orario `09.50` come `11:09`, perdendo la classe associata.
* **Basso Contrasto / Sfondi Saturi:**
  * *Sfondo blu (img8.jpg):* Ha accecato l'AI, causando la mancata lettura di una classe e l'allucinazione di un orario (`10.55` letto come `21:10`).

## 3. Benchmarking Modelli AI: 2B vs 4B

Confronto diretto sulle variazioni di interpretazione tra il modello a 2 miliardi di parametri e quello a 4 miliardi, specificatamente sull'estrazione di testo libero e nomi propri.

| Categoria | Comportamento 2B | Comportamento 4B | Modello Migliore |
| :--- | :--- | :--- | :---: |
| **Estrazione Nomi Propri** | Trascrizione cruda e fedele (es. `LOVECCHIO`, `LONOCE`). | **Iper-correzione linguistica.** Inventa doppie (es. `LOVECCCHIO`, `LONOCCE`). | **2B** |
| **Spaziatura Testo Libero** | Perfetta aderenza visiva. | Errori di chunking (es. `GIG LIO LI`, mancata `L` in Tabarelli). | **2B** |
| **Punteggiatura Complessa** | Mantiene il formato immagine (es. doppi asterischi `**`). | Converte in markdown non richiesto (es. stelline nere `★★`). | **2B** |
| **Segni Diacritici (Accenti)** | Tendenza a ignorarli (es. `CITTA`). | Rilevamento preciso (es. `CITTÀ`). | **4B** |
| **Refusi Minori** | 1 errore rilevato (es. `SAME DE Maturita`). | Nessun refuso strutturale rilevato. | **4B** |