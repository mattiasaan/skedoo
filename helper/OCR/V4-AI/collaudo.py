#!/usr/bin/env python3
"""
Collaudo: esegue TUTTE le immagini una alla volta e poi confronta i risultati per capire
quali sono i veri errori (e quali solo falsi allarmi).

Uso:
  python collauda.py                          # immagini in test_images/, risultati in collaudo/
  python collauda.py cartella --out collaudo --anno 2026
  python collauda.py --solo-confronto         # NON rilegge le immagini: analizza i JSON gia' in collaudo/

Cosa produce (in <out>/): un <immagine>.json per immagine, report.md e report.json.

Il report distingue:
  ERRORE SILENZIOSO   valore sbagliato (rispetto a ground_truth/) marcato 'alta'   -> il problema vero
  errore intercettato valore sbagliato ma segnalato media/bassa                     -> il sistema ha funzionato
  falso allarme       valore giusto ma segnalato media/bassa                        -> rumore (elenchi incompleti, ...)
  mancante            presente nella trascrizione di riferimento, assente dall'output
  differenze tra immagini della stessa data (utile anche dove non c'e' ground_truth)

Codice di uscita: 1 se ci sono errori silenziosi, altrimenti 0.
"""
import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
QUI = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# Esecuzione (una immagine alla volta)
# ---------------------------------------------------------------------------
def esegui(immagini, out: Path, cfg, engine=None, log=print):
    from orario.pipeline import build_engine, processa_immagine
    engine = engine or build_engine(cfg)
    ok, errori = [], {}
    for i, img in enumerate(immagini, 1):
        t0 = time.perf_counter()
        log(f"[{i}/{len(immagini)}] {img.name} ...")
        try:
            res = processa_immagine(img, engine, cfg, outdir=out, log=lambda *_: None)
        except Exception as e:      # noqa: BLE001   un'immagine rotta non ferma le altre
            errori[img.stem] = f"{type(e).__name__}: {e}"
            log(f"    ERRORE: {errori[img.stem]}")
            continue
        (out / f"{img.stem}.json").write_text(json.dumps(res, ensure_ascii=False, indent=2),
                                              encoding="utf-8")
        ok.append(img.stem)
        log(f"    {res['stato']} | alta={res['n_alta']} media={res['n_media']} bassa={res['n_bassa']} "
            f"| {time.perf_counter() - t0:.0f}s")
    return ok, errori


# ---------------------------------------------------------------------------
# Voci confrontabili
# ---------------------------------------------------------------------------
def voci(res):
    """{chiave: dettaglio} per le voci principali (stesse chiavi di evaluate.py)."""
    letto = {d["id"]: d.get("letto") for d in res.get("da_verificare", [])}
    out = {}

    def add(chiave, it):
        out[chiave] = {"aff": it.get("affidabilita") or ("alta" if it.get("verifica") in ("ok", "verificato") else "bassa"),
                       "motivi": it.get("motivi", []), "unit_id": it.get("unit_id"),
                       "letto": letto.get(it.get("unit_id"))}

    for r in res["cambi_aula"]:
        add(("riga", r["classe"], r["orario"], r["aula"]), r)
    for k in ("entrate", "uscite"):
        for e in res[k]:
            add((k, e["ora"], tuple(e["classi"])), e)
    for e in res["senza_lezioni_pomeridiane"]:
        add(("nolez", tuple(e["classi"])), e)
    return out


def voci_gt(gt):
    out = set()
    for r in gt["cambi_aula"]:
        out.add(("riga", r["classe"], r["orario"], r["aula"]))
    for k in ("entrate", "uscite"):
        for e in gt[k]:
            out.add((k, e["ora"], tuple(e["classi"])))
    for e in gt["senza_lezioni_pomeridiane"]:
        out.add(("nolez", tuple(e["classi"])))
    return out


def fmt(k):
    if k[0] == "riga":
        return f"riga {k[1] or '?'} {k[2]} {k[3]}"
    if k[0] in ("entrate", "uscite"):
        return f"{'entra' if k[0] == 'entrate' else 'esce'} {k[1]}: {' + '.join(k[2])}"
    return f"nolez: {' + '.join(k[1])}"


# ---------------------------------------------------------------------------
# Confronto con la trascrizione di riferimento
# ---------------------------------------------------------------------------
def confronta_gt(res, gt):
    got, ref = voci(res), voci_gt(gt)
    r = {"attesi": len(ref), "giusti_alta": [], "falsi_allarmi": [], "silenziosi": [],
         "intercettati": [], "mancanti": [k for k in ref if k not in got]}
    for k, d in got.items():
        giusto = k in ref
        if giusto and d["aff"] in ("alta", "verificata"):
            r["giusti_alta"].append(k)
        elif giusto:
            r["falsi_allarmi"].append((k, d))
        elif d["aff"] in ("alta", "verificata"):
            r["silenziosi"].append((k, d))
        else:
            r["intercettati"].append((k, d))
    r["titolo_ok"] = ((res.get("giorno"), res.get("data_numero"), res.get("mese")) ==
                      (gt["giorno"], gt["numero"], gt["mese"]))
    r["titolo_silenzioso"] = (not r["titolo_ok"]) and res.get("titolo_affidabilita") in ("alta", "verificata")
    return r


# ---------------------------------------------------------------------------
# Confronto tra immagini della stessa data
# ---------------------------------------------------------------------------
def confronta_tra_immagini(risultati):
    gruppi = defaultdict(list)
    for nome, res in risultati.items():
        if res.get("data_numero"):
            gruppi[f"{res.get('giorno')} {res.get('data')}"].append(nome)
    out = []
    for data, nomi in sorted(gruppi.items()):
        if len(nomi) < 2:
            continue
        v = {n: voci(risultati[n]) for n in nomi}
        tutte = set().union(*[set(x) for x in v.values()])
        diff = []
        for k in sorted(tutte, key=str):
            chi = [n for n in nomi if k in v[n]]
            if len(chi) < len(nomi):
                diff.append((k, chi))
        out.append({"data": data, "immagini": nomi, "differenze": diff})
    return out


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def analizza(out: Path, gt_dir: Path, nomi=None):
    risultati = {}
    for f in sorted(out.glob("*.json")):
        if f.stem in ("riepilogo", "report"):
            continue
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:       # noqa: BLE001
            continue
        if isinstance(d, dict) and "cambi_aula" in d and (nomi is None or f.stem in nomi):
            risultati[f.stem] = d
    per_img, tot = {}, Counter()
    for nome, res in risultati.items():
        g = gt_dir / f"{nome}.json"
        entry = {"stato": res["stato"], "alta": res["n_alta"], "media": res["n_media"], "bassa": res["n_bassa"],
                 "data_iso": res.get("data_iso"), "titolo_aff": res.get("titolo_affidabilita"), "gt": None}
        if g.is_file():
            c = confronta_gt(res, json.loads(g.read_text(encoding="utf-8")))
            entry["gt"] = c
            tot.update(attesi=c["attesi"], giusti_alta=len(c["giusti_alta"]), falsi_allarmi=len(c["falsi_allarmi"]),
                       intercettati=len(c["intercettati"]), silenziosi=len(c["silenziosi"]) + int(c["titolo_silenzioso"]),
                       mancanti=len(c["mancanti"]))
        per_img[nome] = entry
    return risultati, per_img, tot, confronta_tra_immagini(risultati)


def _riga_voce(k, d):
    mot = ", ".join(d["motivi"]) or "-"
    lt = f"  | letto: {' / '.join(d['letto'])}" if d.get("letto") else ""
    return f"- `{fmt(k)}` [{d['aff']}: {mot}]{lt}"


def scrivi_report(out: Path, risultati, per_img, tot, tra, errori_esecuzione=None):
    L = ["# Collaudo\n"]
    L.append("## Riepilogo per immagine\n")
    L.append("| immagine | data | stato | alta | media | bassa | vs riferimento |")
    L.append("|---|---|---|---:|---:|---:|---|")
    for n, e in per_img.items():
        c = e["gt"]
        if c:
            conf = (f"{len(c['giusti_alta'])}/{c['attesi']} giusti `alta`, {len(c['falsi_allarmi'])} falsi allarmi, "
                    f"{len(c['intercettati'])} errori intercettati, **{len(c['silenziosi']) + int(c['titolo_silenzioso'])} silenziosi**, "
                    f"{len(c['mancanti'])} mancanti")
        else:
            conf = "(nessuna trascrizione di riferimento)"
        L.append(f"| {n} | {e['data_iso'] or '?'} | {e['stato']} | {e['alta']} | {e['media']} | {e['bassa']} | {conf} |")
    for n, m in (errori_esecuzione or {}).items():
        L.append(f"| {n} | - | **ERRORE** | - | - | - | {m} |")
    if tot:
        L.append(f"\n**Totale (immagini con riferimento):** attesi {tot['attesi']}, giusti `alta` {tot['giusti_alta']}, "
                 f"falsi allarmi {tot['falsi_allarmi']}, errori intercettati {tot['intercettati']}, "
                 f"**errori silenziosi {tot['silenziosi']}**, mancanti {tot['mancanti']}.\n")

    L.append("## Veri errori\n")
    qualcuno = False
    for n, e in per_img.items():
        c = e["gt"]
        if not c:
            continue
        righe = []
        if c["titolo_silenzioso"]:
            righe.append("- **TITOLO SBAGLIATO marcato `alta`**")
        elif not c["titolo_ok"]:
            righe.append("- titolo sbagliato (segnalato)")
        righe += [f"- **SILENZIOSO** " + _riga_voce(k, d)[2:] for k, d in c["silenziosi"]]
        righe += [f"- intercettato " + _riga_voce(k, d)[2:] for k, d in c["intercettati"]]
        righe += [f"- mancante `{fmt(k)}`" for k in c["mancanti"]]
        if righe:
            qualcuno = True
            L.append(f"### {n}\n" + "\n".join(righe) + "\n")
    if not qualcuno:
        L.append("Nessun errore rispetto alle trascrizioni di riferimento.\n")

    L.append("## Falsi allarmi (valore giusto ma non `alta`)\n")
    from orario.config import load_config
    from orario.parse import classe_valida
    valide = load_config().get("classi_valide") or []
    motivi, classi, aule = Counter(), Counter(), Counter()
    for n, e in per_img.items():
        c = e["gt"]
        if not c:
            continue
        for k, d in c["falsi_allarmi"]:
            for m in d["motivi"]:
                motivi[m.split(":")[0]] += 1
            if "classe_fuori_elenco" in d["motivi"]:
                for cl in (k[2] if k[0] in ("entrate", "uscite") else k[1] if k[0] == "nolez" else [k[1]]):
                    if cl and not classe_valida(cl, valide):
                        classi[cl] += 1
            if "aula_fuori_elenco" in d["motivi"] and k[0] == "riga":
                aule[k[3]] += 1
    if motivi:
        L.append("Per motivo: " + ", ".join(f"{m} x{n}" for m, n in motivi.most_common()) + "\n")
        if classi:
            L.append(f"Classi fuori elenco (da verificare e aggiungere a `elenchi/classi.json`): {', '.join(sorted(classi))}\n")
        if aule:
            L.append(f"Aule fuori elenco (da verificare e aggiungere a `elenchi/aule.json`): {', '.join(sorted(aule))}\n")
    else:
        L.append("Nessuno.\n")

    L.append("## Immagini senza riferimento: voci a bassa affidabilita'\n")
    trovato = False
    for n, res in risultati.items():
        if per_img[n]["gt"]:
            continue
        basse = [(k, d) for k, d in voci(res).items() if d["aff"] == "bassa"]
        if basse:
            trovato = True
            L.append(f"### {n}\n" + "\n".join(_riga_voce(k, d) for k, d in basse) + "\n")
    if not trovato:
        L.append("Nessuna.\n")

    L.append("## Confronto tra immagini della stessa data\n")
    if not tra:
        L.append("Nessuna data con piu' di un'immagine.\n")
    for g in tra:
        L.append(f"### {g['data']}: {', '.join(g['immagini'])}\n")
        if not g["differenze"]:
            L.append("Identiche.\n")
            continue
        L.append("Voci non presenti in tutte le immagini (puo' essere un errore di lettura oppure un orario aggiornato):\n")
        for k, chi in g["differenze"]:
            L.append(f"- `{fmt(k)}` solo in: {', '.join(chi)}")
        L.append("")
    testo = "\n".join(L)
    (out / "report.md").write_text(testo, encoding="utf-8")
    sintesi = {"totali": dict(tot), "per_immagine": {n: {k: v for k, v in e.items() if k != "gt"} for n, e in per_img.items()},
               "errori_esecuzione": errori_esecuzione or {}}
    (out / "report.json").write_text(json.dumps(sintesi, ensure_ascii=False, indent=2), encoding="utf-8")
    return testo


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("immagini", nargs="?", default=str(QUI / "test_images"), help="cartella delle immagini")
    ap.add_argument("--out", default="collaudo", help="cartella dei risultati e del report")
    ap.add_argument("--gt", default=str(QUI / "ground_truth"), help="cartella delle trascrizioni di riferimento")
    ap.add_argument("--config", default=None)
    ap.add_argument("--anno", type=int, default=None, help="anno delle immagini (default: piu' vicino a oggi)")
    ap.add_argument("--solo-confronto", action="store_true", help="non rilegge le immagini: analizza i JSON gia' in --out")
    a = ap.parse_args(argv)

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    errori, nomi = {}, None
    if not a.solo_confronto:
        from orario.config import load_config
        cfg = load_config(a.config)
        if a.anno:
            cfg["anno"] = a.anno
        cartella = Path(a.immagini)
        imgs = sorted(x for x in cartella.iterdir() if x.suffix.lower() in EXT)
        if not imgs:
            print("Nessuna immagine trovata.")
            return 1
        ok, errori = esegui(imgs, out, cfg)
        nomi = set(ok)
    risultati, per_img, tot, tra = analizza(out, Path(a.gt), nomi)
    testo = scrivi_report(out, risultati, per_img, tot, tra, errori)
    print("\n" + testo)
    print(f"Report: {out / 'report.md'}")
    return 1 if tot.get("silenziosi") else 0


if __name__ == "__main__":
    sys.exit(main())
