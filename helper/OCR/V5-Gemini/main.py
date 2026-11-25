#!/usr/bin/env python3
"""
Estrazione degli orari dalle immagini della bacheca con l'API Gemini (stesso JSON della V4).

Uso:
  set GEMINI_API_KEY=...            (PowerShell: $env:GEMINI_API_KEY="...", Linux: export GEMINI_API_KEY=...)
  python main.py immagine.jpg
  python main.py test_images --out output
  python main.py immagine.jpg --anno 2026 --html
  python main.py immagine.jpg --modello gemini-flash-lite-latest

Per ogni immagine produce in <out>/:
  <nome>.json               risultato (ogni voce ha 'affidabilita' alta|media|bassa)
  <nome>_ritagli/           ritagli inviati a Gemini
  <nome>_revisione.html     solo con --html e solo se ci sono voci da verificare
  riepilogo.json            una riga per immagine
"""
import argparse
import json
import os
import sys
from pathlib import Path

from gemini_ocr.config import load_config, parse_models
from gemini_ocr.engine import GeminiEngine, GeminiError
from gemini_ocr.pipeline import processa_immagine

EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("percorso", help="immagine o cartella di immagini")
    ap.add_argument("--config", default=None, help="file config.json (default: quello di questa cartella)")
    ap.add_argument("--out", default="output", help="cartella di output")
    ap.add_argument("--modello", default=None,
                    help="modello/i Gemini separati da virgola (default: GEMINI_MODELS o config.json)")
    ap.add_argument("--anno", type=int, default=None, help="anno dell'immagine (default: data piu' vicina a oggi)")
    ap.add_argument("--html", action="store_true", help="pagina di revisione per le voci da verificare")
    a = ap.parse_args(argv)

    cfg = load_config(a.config)
    models = parse_models(a.modello or os.environ.get("GEMINI_MODELS", ""))
    if models:
        cfg["gemini"]["models"] = models
    if a.anno:
        cfg["anno"] = a.anno

    p = Path(a.percorso)
    imgs = sorted(x for x in p.iterdir() if x.suffix.lower() in EXT) if p.is_dir() else [p]
    if not imgs:
        print("Nessuna immagine trovata.")
        return 1
    try:
        engine = GeminiEngine.from_config(cfg, os.environ.get("GEMINI_API_KEY", ""), log=print)
    except GeminiError as e:
        raise SystemExit(f"[ERRORE] {e}")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    riepilogo = []
    for img in imgs:
        try:
            res = processa_immagine(img, engine, cfg, outdir=out)
        except Exception as e:      # noqa: BLE001
            print(f"[ERRORE] {img.name}: {e}")
            riepilogo.append({"file": img.name, "errore": str(e)})
            continue
        (out / f"{img.stem}.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
        if a.html and res["da_verificare"]:
            from orario.report import scrivi_report  # pagina di revisione della V4 (orario/)
            scrivi_report(res, out / f"{img.stem}_revisione.html")
        riepilogo.append({"file": img.name, "stato": res["stato"], "data_iso": res["data_iso"],
                          "modello": res["motore"]["modello"], "voci": res["n_voci"], "alta": res["n_alta"],
                          "media": res["n_media"], "bassa": res["n_bassa"], "avvisi": len(res["avvisi"])})
        print(f"  -> {res['giorno']} {res['data']} | stato={res['stato']} | voci={res['n_voci']} "
              f"(alta={res['n_alta']} media={res['n_media']} bassa={res['n_bassa']}) | avvisi={len(res['avvisi'])}")
    (out / "riepilogo.json").write_text(json.dumps(riepilogo, ensure_ascii=False, indent=2), encoding="utf-8")
    daver = sum(r.get("media", 0) + r.get("bassa", 0) for r in riepilogo)
    print(f"\nFatto. Voci con affidabilita' media/bassa: {daver}. Output in: {out.resolve()}")
    return 2 if any("errore" in r for r in riepilogo) else 0


if __name__ == "__main__":
    sys.exit(main())
