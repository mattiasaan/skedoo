# Estrattore orari bacheca (v5)

Legge le immagini degli orari (entrate/uscite, cambi aula, note) e produce un JSON in cui
**ogni voce ha un'affidabilità** (`alta` / `media` / `bassa`) con i motivi. Nessun dato dubbio passa come buono.

## Cosa viene letto
Tutto: titolo/data, entrate, uscite, senza lezioni pomeridiane, cambi aula, con le note dei riquadri (`posticipa/anticipa`, marcatori `*`/`°`).
Gli unici dati opzionali sono i **riquadri informativi** (FSL, viaggi, docenti assenti, ...): `"leggi_note_libere": false` in `config.json`
li salta (una lettura in meno per riquadro, immagine più veloce); con `true` finiscono in `note[]` e contano per `stato` e `da_verificare` come gli altri dati.

**Regola per la webapp:** usa automaticamente solo le voci con `affidabilita == "alta"`; `media`/`bassa` vanno controllate o escluse.
Il 100% non si può garantire con un solo lettore (vedi "Limiti"): lo si ottiene con questa regola + controllo delle voci non `alta`.

## Idea in breve
1. **OpenCV** divide l'immagine in riquadri (taglio sullo sfondo in legno + colore) e il pannello rosso in righe.
2. **Un solo motore: Qwen3-VL (Ollama), una sola passata.** Trascrive soltanto: non decide nulla.
   (RapidOCR e Tesseract sono stati rimossi: nei test sbagliavano nel 100% dei dissensi.)
3. Il codice interpreta il testo (`orario/parse.py`) e lo controlla con **validatori** (`orario/validazione.py`, `orario/pipeline.py`):
   - formato di classi, aule, orari; orario inizio < fine
   - **griglia degli orari** (`orari_noti`): un orario fuori griglia = errore (es. `09.50` letto `11:09`, `10.55` letto `21:10`)
   - **elenchi** di classi e aule (`elenchi/`)
   - colore del riquadro coerente con ENTRA/ESCE/NO LEZ.
   - titolo: giorno della settimana coerente con la data (e calcolo di `data_iso`)
   - note `posticipa/anticipa N° a M° (aula)`: ore sensate (posticipa = ora più tardi) e aula esistente
   - testo libero: caratteri sospetti (es. `★` al posto di `*`)
   - **tra voci**: pannello in ordine alfabetico di classe, stessa classe in due aule con orari sovrapposti,
     righe duplicate, classe sia in entrata che in uscita alla stessa ora, classe "senza lezioni pomeridiane" con cambio aula pomeridiano
4. Il risultato è un JSON pronto per un altro programma.

## Uso
```
python main.py test_images --out output
python main.py immagine.jpg --anno 2026     # immagine di un anno diverso da quello corrente
python main.py immagine.jpg --html          # (opzionale) pagina di revisione manuale
```
Per ogni immagine in `output/`: `<nome>.json`, `<nome>_ritagli/`, `riepilogo.json` (e `<nome>_revisione.html` con `--html`).
Codice di uscita: `2` se almeno un'immagine è andata in errore, altrimenti `0`.

> Il controllo giorno/data usa l'anno **più vicino a oggi**. Per immagini d'archivio passa `--anno`
> (o `"anno"` in `config.json`), altrimenti il titolo risulta `bassa` con motivo `giorno_settimana_incoerente_con_data`.

## Il JSON (schema_versione 2, `schema/orario.schema.json`)
Le chiavi sono quelle della v4; sono state **aggiunte** `schema_versione`, `data_iso`, `affidabilita`, `motivi`, `da_verificare`, contatori.
```
schema_versione, _source, estratto_il, motore{modello,scala}
giorno, data, data_numero, mese, data_iso            titolo (+ titolo_affidabilita, titolo_motivi)
entrate[]  / uscite[]   {unit_id, ora, classi[], note, marcatori?, affidabilita, motivi[], verifica}
senza_lezioni_pomeridiane[] {unit_id, classi[], note, marcatori?, ...}
cambi_aula[]            {unit_id, classe, orario "HH:MM - HH:MM", aula, marcatore?, ...}
note[]                  {unit_id, tipo, testo, ...}
avvisi[]                messaggi di coerenza (stringhe)
da_verificare[]         {id, tipo, affidabilita, motivi[], letto[], ritaglio}  media + bassa, le basse per prime
n_voci, n_alta, n_media, n_bassa, n_da_verificare, stato ("completo" | "da_verificare")
```
Come usarlo nell'altro progetto:
- `affidabilita == "alta"` → usabile senza controllo (`verifica == "ok"`, campo mantenuto per compatibilità).
- `media` → formalmente valido ma anomalo (classe/aula non in elenco, riga stimata, ordine alfabetico rotto, …): usabile con cautela.
- `bassa` → non fidarti: classe assente, orario fuori griglia, lettura fallita, …
- `stato == "completo"` solo se **tutto** è `alta`.
- `classe` è `null` quando nell'immagine manca o il modello non la legge (sempre `bassa`).
- `data_iso` è `null` se giorno e data non tornano.

## Configurazione (`config.json`)
- `ollama`: `host`, `model`, `scale` (ingrandimento del ritaglio), `num_ctx`, `timeout_s`, `keep_alive`, `think`.
- `anno`: anno delle immagini (`null` = più vicino a oggi).
- `orari_noti`: griglia degli orari; **fuori griglia = `bassa`**. Aggiornala se la scuola cambia orario.
- `classi_file`, `aule_file`, `aule_nominali`: elenchi ammessi; fuori elenco = `media`.
  - `elenchi/classi.json`: elenco ufficiale delle classi. **Se è di un altro anno scolastico (mancano 3C, 3J, 5B, 5C, 5G, 5K, 3P, 4N…) molte classi vere risultano `media`: aggiornalo.**
  - `elenchi/aule.json`: cresce con `python apprendi.py cartella_json_verificati` (JSON scaricati dalla revisione, `stato: verificato`).

## Limiti noti (senza un secondo lettore)
- Un valore **sbagliato ma valido e coerente** (es. `1I` letto `1D`, con entrambe in elenco e ordine rispettato) non è riconoscibile: nella simulazione
  (`python tests/simula_vlm.py test_images 0.1 8`, ~10% di letture sbagliate) 3 errori su 85 sono rimasti `alta`. Tieni gli elenchi aggiornati: restringono lo spazio di questi errori.
- Il testo libero (nomi, FSL, viaggi) è controllato solo su caratteri e struttura, non sui nomi.
- Per ridurre le voci `media`: aggiorna `elenchi/classi.json` (classi mancanti = `media`) e le aule con `apprendi.py`.
- Una sola passata: il modello è deterministico (temperature 0), rileggere non aggiungerebbe informazione.

## Misurare / testare
```
python -m unittest discover -s tests -v          # nessun modello necessario
python tests/simula_vlm.py test_images 0.1 8      # finto Qwen con errori iniettati
python main.py test_images --out output && python evaluate.py output ground_truth
```
In `evaluate.py` **ERRORI_SILENZIOSI** = valori sbagliati marcati `alta`.

## download modelli
  - ollama pull qwen3-vl:2b-instruct # circa 2 minuti a immagine, 8 - 10s a ritaglio 
  - ollama pull qwen3-vl:4b-instruct # circa 3,5 minuti a immagine, 15-20s a ritaglio
  - ollama pull qwen3-vl:8b-instruct # circa 10 minuti a immagine, 50s a ritaglio
  - ollama pull qwen3-vl:30b-instruct # da testare
