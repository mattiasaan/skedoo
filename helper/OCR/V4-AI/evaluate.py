#!/usr/bin/env python3
"""
Confronta i JSON prodotti con la trascrizione di riferimento (ground_truth/).

Metrica chiave: ERRORI SILENZIOSI = valori sbagliati marcati 'ok' (non segnalati).
Obiettivo: 0. Gli errori segnalati 'da_verificare' non sono silenziosi: li corregge la revisione.

Uso:  python evaluate.py output ground_truth
"""
import json
import sys
from pathlib import Path


def _items(res):
    """Insiemi confrontabili: {chiave: verifica}"""
    out = {}
    for r in res["cambi_aula"]:
        out[("riga", r["classe"], r["orario"], r["aula"])] = r.get("verifica")
    for k in ("entrate", "uscite"):
        for e in res[k]:
            out[(k, e["ora"], tuple(e["classi"]))] = e.get("verifica")
    for e in res["senza_lezioni_pomeridiane"]:
        out[("nolez", tuple(e["classi"]))] = e.get("verifica")
    return out


def _gt_items(gt):
    out = set()
    for r in gt["cambi_aula"]:
        out.add(("riga", r["classe"], r["orario"], r["aula"]))
    for k in ("entrate", "uscite"):
        for e in gt[k]:
            out.add((k, e["ora"], tuple(e["classi"])))
    for e in gt["senza_lezioni_pomeridiane"]:
        out.add(("nolez", tuple(e["classi"])))
    return out


def valuta(res, gt):
    got = _items(res)
    ref = _gt_items(gt)
    ok_giusti = [k for k, v in got.items() if k in ref and v in ("ok", "verificato")]
    segn_giusti = [k for k, v in got.items() if k in ref and v == "da_verificare"]
    silenziosi = [k for k, v in got.items() if k not in ref and v in ("ok", "verificato")]
    segn_errati = [k for k, v in got.items() if k not in ref and v == "da_verificare"]
    mancanti = [k for k in ref if k not in got]
    titolo_ok = ((res.get("giorno"), res.get("data_numero"), res.get("mese")) ==
                 (gt["giorno"], gt["numero"], gt["mese"]))
    titolo_silenzioso = (not titolo_ok) and res.get("titolo_verifica") == "ok"
    n_note = len(res["note"])
    return {
        "attesi": len(ref), "ok_giusti": len(ok_giusti),
        "segnalati_giusti": len(segn_giusti), "segnalati_errati": len(segn_errati),
        "ERRORI_SILENZIOSI": len(silenziosi) + (1 if titolo_silenzioso else 0),
        "mancanti": len(mancanti), "titolo_ok": titolo_ok,
        "note_attese": gt.get("n_note"), "note_trovate": n_note,
        "dettaglio_silenziosi": silenziosi, "dettaglio_mancanti": mancanti,
        "dettaglio_segnalati_errati": segn_errati,
    }


def main(out_dir, gt_dir, verbose=True):
    tot = {"attesi": 0, "ok_giusti": 0, "segnalati_giusti": 0, "segnalati_errati": 0,
           "ERRORI_SILENZIOSI": 0, "mancanti": 0}
    for f in sorted(Path(out_dir).glob("img*.json")):
        if f.stem.endswith("_verificato") or f.stem == "riepilogo":
            continue
        g = Path(gt_dir) / f"{f.stem}.json"
        if not g.exists():
            continue
        r = valuta(json.loads(f.read_text(encoding="utf-8")), json.loads(g.read_text(encoding="utf-8")))
        for k in tot:
            tot[k] += r[k]
        print(f"{f.stem}: attesi={r['attesi']} ok_giusti={r['ok_giusti']} "
              f"segnalati(giusti/errati)={r['segnalati_giusti']}/{r['segnalati_errati']} "
              f"SILENZIOSI={r['ERRORI_SILENZIOSI']} mancanti={r['mancanti']} "
              f"titolo={'ok' if r['titolo_ok'] else 'ERRATO'} note={r['note_trovate']}/{r['note_attese']}")
        if verbose:
            for k in r["dettaglio_silenziosi"]:
                print("   !! SILENZIOSO:", k)
            for k in r["dettaglio_mancanti"]:
                print("   -- mancante:", k)
    print("\nTOTALE:", tot)
    n = tot["attesi"] or 1
    print(f"Automatici corretti: {tot['ok_giusti']}/{n} ({100*tot['ok_giusti']/n:.0f}%) | "
          f"da verificare a mano: {tot['segnalati_giusti']+tot['segnalati_errati']} | "
          f"ERRORI SILENZIOSI: {tot['ERRORI_SILENZIOSI']}")
    return tot["ERRORI_SILENZIOSI"]


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1], sys.argv[2]) else 0)
