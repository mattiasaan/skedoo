# Vecchie versioni

Codice che funzionava ma che il progetto non usa più. Resta qui come riferimento: niente lo importa, il deploy non
lo costruisce e non viene più aggiornato. La versione in uso dell'OCR è [helper/OCR/V5-Gemini](../helper/OCR/V5-Gemini/README.md).

| Cartella | Cosa | Sostituita da |
|---|---|---|
| [OCR/V3-tessercat](OCR/V3-tessercat) | OCR dei cartelloni con OpenCV + **Tesseract** (`orario_scolastico_ocr.py`) e script di diagnosi dei colori | V4: Tesseract sbagliava troppo |
| [OCR/V4-AI](OCR/V4-AI/README.md) | Segmentazione OpenCV + **Qwen3-VL su Ollama**, validatori e affidabilità delle voci; servizio HTTP (`service.py`) usato dal vecchio profilo `ocr` del deploy | V5: minuti di CPU al 100% per cartellone sul Raspberry |

La V5 contiene una **copia** del pacchetto `orario/` della V4 (segmentazione, parser, validatori), insieme a
`elenchi/` e `schema/`: le correzioni vanno fatte lì, non qui.

## Rilanciarle

- **V3**: serve Tesseract installato (il percorso è fisso in `orario_scolastico_ocr.py`, `C:\Program Files\Tesseract-OCR`)
  e `pip install -r requirements.txt`; poi `python orario_scolastico_ocr.py ../V4-AI/test_images`.
- **V4**: serve Ollama con il modello di `config.json` (`ollama pull qwen3-vl:2b-instruct`) e
  `pip install -r requirements.txt`; poi `python main.py test_images --out output`.
  I test (`tests/`) sono solo in locale, esclusi da git.
