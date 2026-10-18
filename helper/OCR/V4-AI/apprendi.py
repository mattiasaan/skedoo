#!/usr/bin/env python3
"""
Arricchisce l'elenco delle aule (elenchi/aule.json) con le aule dei JSON VERIFICATI,
cosi' non devi scriverle a mano: dopo ogni revisione l'elenco cresce da solo.

Uso:
  python apprendi.py cartella_con_json_verificati          # solo file con stato 'verificato'
  python apprendi.py cartella --tutti                      # qualsiasi JSON (es. ground_truth/)
  python apprendi.py cartella --anche-completi             # include 'completo' (verificati dai motori)
"""
import argparse
import json
from pathlib import Path

from orario.config import core_aula

DEST = Path(__file__).resolve().parent / "elenchi" / "aule.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cartella")
    ap.add_argument("--tutti", action="store_true")
    ap.add_argument("--anche-completi", action="store_true")
    a = ap.parse_args()
    esistenti = json.loads(DEST.read_text(encoding="utf-8")) if DEST.exists() else []
    nuove = set(esistenti)
    n_file = 0
    for f in sorted(Path(a.cartella).glob("*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:      # noqa: BLE001
            continue
        if not isinstance(d, dict) or "cambi_aula" not in d:
            continue
        stato = d.get("stato")
        if not (a.tutti or stato == "verificato" or (a.anche_completi and stato == "completo")):
            continue
        n_file += 1
        for r in d["cambi_aula"]:
            if r.get("aula") and r.get("verifica") in (None, "ok", "verificato"):
                nuove.add(r["aula"].strip().upper())
    # un'aula e' identificata dal codice: tieni una sola forma per codice
    per_core = {}
    for x in sorted(nuove):
        per_core.setdefault(core_aula(x), x)
    out = sorted(per_core.values())
    DEST.parent.mkdir(exist_ok=True)
    DEST.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"File letti: {n_file}. Aule in elenco: {len(esistenti)} -> {len(out)} ({DEST})")


if __name__ == "__main__":
    main()
