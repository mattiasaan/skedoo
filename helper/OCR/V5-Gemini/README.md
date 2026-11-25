# Estrattore orari bacheca con Gemini (V5)

Stesso compito e **stesso JSON** della [V4](../V4-AI/README.md) (schema_versione 2), ma i ritagli li legge
l'API Gemini di Google AI Studio (piano gratuito) invece di Qwen3-VL su Ollama. Sul Raspberry non gira più
nessun modello: la CPU fa solo la segmentazione con OpenCV (pochi secondi), niente surriscaldamento.

## Come funziona
1. **Segmentazione della V4** (`../V4-AI/orario/segment.py`): riquadri e righe del pannello CAMBIO AULA,
   con gli stessi `unit_id` della V4.
2. **Una sola richiesta a Gemini per cartellone**: tutti i ritagli insieme (`u01`, `u02`, ...), risposta JSON
   vincolata da `responseSchema`. Il modello trascrive soltanto.
3. **Interpretazione e validatori della V4** (`parse.py`, `validazione.py`, controlli tra voci di `pipeline.py`):
   affidabilità `alta`/`media`/`bassa`, `da_verificare`, `stato`, come prima.

Il codice della V4 **non è copiato**: viene importato da `../V4-AI` (o da `OCR_V4_DIR`). Regole, elenchi di
classi/aule e griglia degli orari restano in un solo posto (`../V4-AI/config.json`, `../V4-AI/elenchi/`).
`tests/test_pipeline.py` controlla che, a parità di testo letto, il JSON sia identico a quello della V4.

Differenze rispetto alla V4: `motore.modello` (es. `gemini-flash-latest`) e `motore.scala`; i titoli con il giorno
abbreviato (`MER. 25 NOVEMBRE`) vengono riconosciuti; per i riquadri NO LEZ. POM. il colore non conta (la scuola li
stampa sia bianchi sia gialli), mentre per ENTRA/ESCE il controllo del colore resta.
Un ritaglio che Gemini non restituisce diventa una voce `bassa` (`lettura_fallita`), come un errore di lettura nella V4.

I riquadri informativi (FSL, viaggi, docenti assenti) con `"leggi_note_libere": false` (default della V4)
non vengono letti e quindi **non vengono inviati a Google**. Vengono inviati solo titolo, riquadri
ENTRA/ESCE/NO LEZ. e righe dei cambi aula.

## Chiave API
1. Vai su <https://aistudio.google.com/apikey> e crea una chiave (piano gratuito, senza carta).
2. Impostala in `GEMINI_API_KEY` (nel deploy: `deploy/.env`).

Il piano gratuito ha limiti bassi e variabili per modello (richieste al minuto e al giorno: controllali nella
pagina *Rate limit* di AI Studio). Per questo:
- un cartellone = **una** richiesta (fino a `max_unita_per_richiesta` ritagli);
- i limiti al minuto (429) e i 503 di Google ("model is overloaded", frequenti sul piano gratuito) vengono ritentati (5s, 10s, 20s); se il modello resta non disponibile si passa al successivo;
- quando la quota **giornaliera** di un modello è finita si passa al successivo di `models`;
- il backend mette in cache i risultati: un'immagine già letta non viene più inviata.

> Sul piano gratuito Google può usare i contenuti inviati per migliorare i suoi prodotti. I ritagli contengono
> classi, aule e orari (e le note dei riquadri ENTRA/ESCE); con un progetto a pagamento questo non avviene.

## Uso da riga di comando
```
pip install -r requirements.txt
$env:GEMINI_API_KEY="..."            # PowerShell   (Linux: export GEMINI_API_KEY=...)
python main.py ../V4-AI/test_images --out output
python main.py immagine.jpg --anno 2026 --html
python main.py immagine.jpg --modello gemini-flash-lite-latest
```
Output come la V4: `<nome>.json`, `<nome>_ritagli/`, `riepilogo.json`, `<nome>_revisione.html` con `--html`.

## Servizio HTTP (container)
`service.py` ha la stessa interfaccia del servizio della V4, il worker del backend non cambia:
`POST /ocr?nome=<file>` con `Authorization: Bearer <OCR_TOKEN>`, `GET /health`.
All'avvio verifica la chiave con l'elenco dei modelli (non consuma quota); finché non è valida `/health`
risponde `starting` e `/ocr` 503.

| Codice | Quando |
|--------|--------|
| 200 | JSON del cartellone |
| 401 / 411 / 413 / 422 | token, lunghezza, dimensione, immagine non valida |
| 502 | Gemini ha rifiutato la richiesta |
| 503 | chiave non ancora verificata, quota esaurita per tutti i modelli, oppure Gemini sovraccarico/irraggiungibile su tutti i modelli (`Retry-After`) |

Nel deploy: profilo `ocr-gemini` in `deploy/compose.yaml` (vedi `deploy/README.md`).
L'immagine si costruisce con contesto `helper/OCR`: `docker build -f V5-Gemini/Dockerfile helper/OCR`.

Variabili: `OCR_TOKEN`, `GEMINI_API_KEY`, `GEMINI_MODELS` (es. `gemini-flash-latest,gemini-flash-lite-latest`),
`OCR_MAX_IMAGE_MB`, `OCR_V4_DIR`.

## Configurazione (`config.json`)
- `base_config`: configurazione della V4 da cui prendere griglia orari, elenchi, `leggi_note_libere`, `anno`.
- `gemini.models`: modelli in ordine di preferenza. Gli alias `*-latest` seguono l'ultima versione di Google;
  per non avere sorprese puoi fissare una versione precisa (l'elenco è nella documentazione di Gemini).
- `gemini.scale`: ingrandimento dei ritagli prima dell'invio (2).
- `gemini.max_unita_per_richiesta` (40), `max_tentativi` (4), `max_attesa_s` (90), `timeout_s` (180).
- `gemini.generation_config`: campi aggiunti a `generationConfig`, ad esempio
  `{"temperature": 0}` o `{"thinkingConfig": {"thinkingBudget": 0}}` (dipendono dal modello: un campo non
  supportato fa rifiutare la richiesta con 400).

## Testare
```
python -m unittest discover -s tests -v     # nessuna rete e nessuna chiave necessaria
python main.py ../V4-AI/test_images         # lettura vera (serve GEMINI_API_KEY)
```
