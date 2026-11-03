#!/usr/bin/env python3
"""
Estrazione affidabile degli orari scolastici da immagini (Qwen3-VL + validatori).

Uso:
  python main.py immagine.jpg
  python main.py cartella_immagini --out output
  python main.py test_images/img-new.png --anno 2026
  python main.py immagine.jpg --html

Per ogni immagine produce in <out>/:
  <nome>.json               risultato (ogni voce ha 'affidabilita' alta|media|bassa)
  <nome>_ritagli/           ritagli usati per la lettura
  <nome>_revisione.html     solo con --html e solo se ci sono voci da verificare
  riepilogo.json            una riga per immagine
"""
import argparse
import json
import sys
from pathlib import Path

from orario.config import load_config
from orario.pipeline import build_engine, processa_immagine
from orario.report import scrivi_report

EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("percorso", help="immagine o cartella di immagini")
    ap.add_argument("--config", default=None, help="file config.json")
    ap.add_argument("--out", default="output", help="cartella di output")
    ap.add_argument("--modello", default=None, help="modello Ollama (default: config.json)")
    ap.add_argument("--anno", type=int, default=None,
                    help="anno dell'immagine (default: data piu' vicina a oggi)")
    ap.add_argument("--html", action="store_true",
                    help="genera la pagina di revisione manuale per le voci da verificare")
    a = ap.parse_args(argv)

    cfg = load_config(a.config)
    if a.modello:
        cfg["ollama"]["model"] = a.modello
    if a.anno:
        cfg["anno"] = a.anno

    p = Path(a.percorso)
    imgs = sorted(x for x in p.iterdir() if x.suffix.lower() in EXT) if p.is_dir() else [p]
    if not imgs:
        print("Nessuna immagine trovata.")
        return 1
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    engine = build_engine(cfg)
    riepilogo = []
    for img in imgs:
        try:
            res = processa_immagine(img, engine, cfg, outdir=out)
        except Exception as e:      # noqa: BLE001
            print(f"[ERRORE] {img.name}: {e}")
            riepilogo.append({"file": img.name, "errore": str(e)})
            continue
        (out / f"{img.stem}.json").write_text(
            json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
        if a.html and res["da_verificare"]:
            scrivi_report(res, out / f"{img.stem}_revisione.html")
        riepilogo.append({"file": img.name, "stato": res["stato"], "data_iso": res["data_iso"],
                          "voci": res["n_voci"], "alta": res["n_alta"], "media": res["n_media"],
                          "bassa": res["n_bassa"], "avvisi": len(res["avvisi"])})
        print(f"  -> {res['giorno']} {res['data']} | stato={res['stato']} | voci={res['n_voci']} "
              f"(alta={res['n_alta']} media={res['n_media']} bassa={res['n_bassa']}) | "
              f"avvisi={len(res['avvisi'])}")
    (out / "riepilogo.json").write_text(json.dumps(riepilogo, ensure_ascii=False, indent=2),
                                        encoding="utf-8")
    daver = sum(r.get("media", 0) + r.get("bassa", 0) for r in riepilogo)
    print(f"\nFatto. Voci con affidabilita' media/bassa: {daver}. Output in: {out.resolve()}")
    return 2 if any("errore" in r for r in riepilogo) else 0


if __name__ == "__main__":
    sys.exit(main())
