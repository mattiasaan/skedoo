#!/usr/bin/env python3
"""
Estrazione affidabile degli orari scolastici da immagini.

Uso:
  python main.py immagine.jpg
  python main.py cartella_immagini --out output
  python main.py immagine.jpg --motori ollama,rapidocr --unanime

Per ogni immagine produce in <out>/:
  <nome>.json               risultato (con 'stato' e 'verifica' per ogni voce)
  <nome>_revisione.html     pagina di revisione (solo se serve)
  <nome>_ritagli/           ritagli usati per la lettura
"""
import argparse
import json
import sys
from pathlib import Path

from orario.config import load_config
from orario.pipeline import build_engines, processa_immagine
from orario.report import scrivi_report

EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("percorso", help="immagine o cartella di immagini")
    ap.add_argument("--config", default=None, help="file config.json")
    ap.add_argument("--out", default="output", help="cartella di output")
    ap.add_argument("--motori", default=None, help="es. ollama,rapidocr,tesseract")
    ap.add_argument("--unanime", action="store_true",
                    help="richiede che TUTTI i motori concordino (altrimenti revisione)")
    a = ap.parse_args(argv)

    cfg = load_config(a.config)
    if a.motori:
        cfg["motori"] = [m.strip() for m in a.motori.split(",") if m.strip()]
    if a.unanime:
        cfg["politica"] = "unanime"

    p = Path(a.percorso)
    imgs = sorted(x for x in p.iterdir() if x.suffix.lower() in EXT) if p.is_dir() else [p]
    if not imgs:
        print("Nessuna immagine trovata.")
        return 1
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    engines = build_engines(cfg)
    riepilogo = []
    for img in imgs:
        try:
            res = processa_immagine(img, engines, cfg, outdir=out)
        except Exception as e:      # noqa: BLE001
            print(f"[ERRORE] {img.name}: {e}")
            riepilogo.append({"file": img.name, "errore": str(e)})
            continue
        (out / f"{img.stem}.json").write_text(
            json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
        if res["controllo"] or res["avvisi"]:
            scrivi_report(res, out / f"{img.stem}_revisione.html")
        riepilogo.append({"file": img.name, "stato": res["stato"],
                          "da_verificare": res["n_da_verificare"],
                          "dissensi": res["n_dissensi"], "avvisi": len(res["avvisi"])})
        print(f"  -> {res['giorno']} {res['data']} | stato={res['stato']} | "
              f"da verificare={res['n_da_verificare']} | dissensi={res['n_dissensi']} | "
              f"avvisi={len(res['avvisi'])}")
    (out / "riepilogo.json").write_text(json.dumps(riepilogo, ensure_ascii=False, indent=2),
                                        encoding="utf-8")
    daver = sum(r.get("da_verificare", 0) for r in riepilogo)
    print(f"\nFatto. Voci da verificare a mano: {daver}. Output in: {out.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
