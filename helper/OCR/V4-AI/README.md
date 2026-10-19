# Estrattore orari bacheca (v4)

Legge le immagini degli orari (entrate/uscite, cambi aula, note) e produce un JSON in cui
**ogni dato è verificato oppure esplicitamente segnalato**. Nessun dato incerto passa come buono.

## Idea in breve
1. **OpenCV** divide l'immagine in riquadri (taglio sullo sfondo in legno + colore) e il pannello rosso in righe.
2. Ogni riquadro/riga viene **trascritto da più motori indipendenti**:
   Qwen3-VL (via Ollama), RapidOCR e Tesseract. I motori non decidono nulla: trascrivono.
3. Il testo viene interpretato dal codice (`orario/parse.py`) con **regole rigide** (formato di classi, aule, orari, coerenza orari/colori/data).
4. Un dato è `ok` solo se è valido **e** almeno 2 famiglie di motori diverse leggono la stessa cosa (`orario/consensus.py`).
   Se i motori dissentono, il valore scelto per maggioranza viene mostrato ma resta
   `da_verificare`: non viene più considerato verificato automaticamente.
5. La pagina `*_revisione.html` permette di correggere/confermare e scarica il JSON finale `verificato`.

## Uso
```
python main.py test_images --out output
python main.py immagine.jpg --motori ollama,rapidocr      # scegli i motori
python main.py test_images --unanime                      # tutti i motori devono concordare
```
Per ogni immagine in `output/`: `<nome>.json`, `<nome>_revisione.html` (solo se serve), `<nome>_ritagli/`, e `riepilogo.json`.

### Come leggere il JSON
- `stato`: `completo` (tutto verificato) oppure `da_verificare` (apri la pagina di revisione).
- Ogni voce ha `verifica`: `ok` | `da_verificare` (dopo la revisione: `verificato`).
- Un dissenso tra motori è sempre `da_verificare`, anche con politica `maggioranza`.
- `avvisi`: controlli di coerenza (stessa classe in due aule con orari sovrapposti, ecc.).
- `cambi_aula[].classe` è `null` quando nell'immagine originale la classe manca: succede in alcune righe
  di img1/img3 e non è recuperabile da nessun lettore, quindi viene sempre segnalata.
- `marcatori` (`*`, `°`) legano le classi alle note del riquadro.
- Novità rispetto al vecchio script: `senza_lezioni_pomeridiane` (riquadro "NO LEZ. POM."), `stato`, `verifica`.

## Configurazione (`config.json`)
- `motori`: ordine/famiglie. I motori non disponibili vengono saltati con un avviso.
  Con una sola famiglia disponibile nulla può essere `ok` (nessuna verifica incrociata possibile).
- `ollama.scale`: ingrandimenti con cui leggere, es. `[3]`. Ogni riga è letta dal modello sul ritaglio ingrandito.
- `politica`: `maggioranza` (default: 2 famiglie concordi, il dissenso viene mostrato e richiede verifica)
  oppure `unanime`.
- `autonomia`: per i job senza operatore, un risultato Ollama formalmente valido può essere
  accettato anche senza consenso solo se tutti gli OCR disponibili hanno prodotto letture valide
  ma diverse. Il risultato viene comunque registrato in `avvisi`; errori, valori fuori regola o
  motori senza lettura non attivano questo fallback.
- `classi_file` / `aule_file` / `orari_noti` / `aule_nominali`: elenchi dei valori ammessi.
  Un valore **fuori elenco** non viene bloccato, ma e' accettato solo se **tutti** i motori disponibili
  concordano (altrimenti va in revisione) e compare tra gli `avvisi`.
  - `elenchi/classi.json`: l'elenco ufficiale delle classi (formato lista di oggetti con `id`, come il tuo file).
    Sono accettati anche i sotto-gruppi con cifra finale (`1MAQ1` se esiste `1MAQ`) e le classi articolate
    (`3C/T` se esistono `3C` e `3T`).
  - `elenchi/aule.json`: **non va scritto a mano**. Parte con le aule viste nelle immagini di test e cresce
    con `python apprendi.py cartella_json_verificati` (usa solo i JSON `verificato` scaricati dalla pagina di revisione).
    `AULA D205` e `LAB. D205` contano come la stessa aula.

## Misurare l'accuratezza
`ground_truth/` contiene la trascrizione verificata a mano delle 7 immagini di test.
```
python main.py test_images --out output
python evaluate.py output ground_truth
```
La metrica che conta è **ERRORI_SILENZIOSI** (valori sbagliati marcati `ok`): deve essere 0.

## Limiti noti
- Se due motori sbagliano allo stesso modo la stessa lettura valida, l'errore passa: per questo conviene
  tenere gli elenchi di classi/aule aggiornati e usare `ollama` + almeno un OCR.
- L'elenco classi fornito non contiene alcune classi presenti nelle immagini di test (3C, 3J, 3MAT, 3P, 4N, 5B, 5C, 5G, 5K):
  e' probabilmente di un altro anno scolastico. Quelle letture vengono accettate solo con accordo totale dei motori.
- I riquadri informativi (FSL, viaggi, docenti assenti) si confrontano in modo approssimato sul testo
  (cifre identiche + somiglianza ≥ 93%); le cifre sono sempre controllate esattamente.
- La pagina di revisione mostra un valore precompilato: la conferma va data guardando il ritaglio.
