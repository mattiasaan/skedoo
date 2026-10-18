"""
Pipeline: immagine -> riquadri/righe -> letture di piu' motori -> consenso -> JSON.
"""
import re
from pathlib import Path

import cv2

from . import parse as P
from .config import find_tesseract
from .consensus import Reading, decide
from .engines import (Engine, EngineUnavailable, OllamaVLM, RapidOCREngine,
                      TesseractEngine)
from .segment import (righe_pannello, righe_testo, ritaglia_riga,
                      segmenta_riquadri)

PRIORITA = ["ollama", "rapidocr", "tesseract"]


# ---------------------------------------------------------------------------
# Motori
# ---------------------------------------------------------------------------
def build_engines(cfg: dict, log=print):
    engines, skipped = [], []
    for name in cfg.get("motori", []):
        try:
            if name == "ollama":
                oc = cfg["ollama"]
                scales = oc.get("scale", [3])
                scales = scales if isinstance(scales, list) else [scales]
                for sc in scales:
                    engines.append(OllamaVLM(oc["host"], oc["model"], scale=sc,
                                             num_ctx=oc.get("num_ctx", 4096),
                                             timeout_s=oc.get("timeout_s", 900),
                                             keep_alive=oc.get("keep_alive", "10m"),
                                             think=oc.get("think")))
            elif name == "rapidocr":
                engines.append(RapidOCREngine())
            elif name == "tesseract":
                engines.append(TesseractEngine(find_tesseract(cfg)))
            else:
                skipped.append((name, "motore sconosciuto"))
        except EngineUnavailable as e:
            skipped.append((name, str(e)))
    for n, why in skipped:
        log(f"[AVVISO] motore '{n}' non disponibile: {why}")
    fams = {e.family for e in engines}
    if not engines:
        raise SystemExit("Nessun motore disponibile: impossibile procedere.")
    if len(fams) < cfg.get("voti_minimi", 2):
        log(f"[AVVISO] solo {len(fams)} famiglia/e di motori disponibili "
            f"({', '.join(sorted(fams))}): senza verifica incrociata nulla sara' "
            "marcato 'ok' e tutto andra' in revisione.")
    return engines


# ---------------------------------------------------------------------------
# Lettura di un'unita'
# ---------------------------------------------------------------------------
class Unit:
    def __init__(self, uid, kind, crop, parse_fn, same_fn=None, meta=None, crop_stretto=None):
        self.uid = uid
        self.kind = kind              # tipo per i motori: riga | riquadro | info | titolo
        self.crop = crop
        self.crop_stretto = crop_stretto if crop_stretto is not None else crop
        self.parse_fn = parse_fn
        self.same_fn = same_fn
        self.meta = meta or {}


def leggi_unita(unit: Unit, engines, cfg):
    readings = []
    for e in engines:
        if not e.supports(unit.kind):
            continue
        rd = Reading(engine=e.name, family=e.family)
        try:
            rd.lines = e.read(unit.crop_stretto if getattr(e, 'stretto', False) else unit.crop,
                              unit.kind)
            rd.parsed = unit.parse_fn(rd.lines)
        except Exception as ex:     # noqa: BLE001
            rd.error = f"{type(ex).__name__}: {ex}"
        readings.append(rd)
    dec = decide(readings, PRIORITA, cfg.get("voti_minimi", 2),
                 cfg.get("politica", "maggioranza"), unit.same_fn)
    return dec


# ---------------------------------------------------------------------------
# Classificazione note
# ---------------------------------------------------------------------------
def classifica_nota(testo: str) -> str:
    up = testo.upper()
    if "F.S.L" in up or "FSL" in up or "FORMAZIONE SCUOLA" in up or "SCUOLA LAVORO" in up:
        return "FSL"
    if "DOCENTI" in up and "ASSENT" in up:
        return "docenti_assenti"
    if any(k in up for k in ("VIAGGIO", "VISITA", "LAGO", "SETTIMANA", "GITA", "USCITA")):
        return "uscita_didattica"
    if any(k in up for k in ("TORNEO", "TROFEO", "PROGETTO")):
        return "attivita"
    return "generico"


def _letture_txt(dec):
    out = {}
    for rd in dec.readings:
        if rd.error:
            out[rd.engine] = f"[errore] {rd.error}"
        elif rd.parsed is not None and hasattr(rd.parsed, "short"):
            out[rd.engine] = rd.parsed.short() if not getattr(rd.parsed, "fatal", False) \
                else " / ".join(rd.lines) + "  [non interpretabile]"
        else:
            out[rd.engine] = " / ".join(rd.lines)
    return out


# ---------------------------------------------------------------------------
# Pipeline principale
# ---------------------------------------------------------------------------
def processa_immagine(path, engines, cfg, outdir=None, log=print):
    path = Path(path)
    img = cv2.imread(str(path))
    if img is None:
        raise FileNotFoundError(f"Impossibile aprire l'immagine: {path}")
    stem = path.stem
    outdir = Path(outdir) if outdir else None
    crops_dir = None
    if outdir and cfg.get("salva_ritagli", True):
        crops_dir = outdir / f"{stem}_ritagli"
        crops_dir.mkdir(parents=True, exist_ok=True)

    boxes = segmenta_riquadri(img)
    units = []        # (Unit, destinazione)
    n = 0

    def nuovo_id(tag):
        nonlocal n
        n += 1
        return f"{stem}_{n:02d}_{tag}"

    # -------- titolo
    titoli = [b for b in boxes if b.famiglia == "titolo"]
    # -------- riquadri
    for b in boxes:
        crop = b.crop(img)
        if b.famiglia == "titolo":
            units.append(Unit(nuovo_id("titolo"), "titolo", crop,
                              lambda ls: P.parse_title(" ".join(ls), cfg),
                              meta={"tipo": "titolo"}))
        elif b.famiglia == "cambio_aula":
            rows = righe_pannello(crop)
            for i, r in enumerate(rows):
                rc = ritaglia_riga(crop, r)
                rt = ritaglia_riga(crop, r, stretto=True)
                units.append(Unit(nuovo_id(f"riga{i:02d}"), "riga", rc,
                                  lambda ls: P.parse_row(" ".join(ls), cfg),
                                  meta={"tipo": "riga", "sospetta": r.sospetta},
                                  crop_stretto=rt))
            if not rows:
                units.append(Unit(nuovo_id("pannello_senza_righe"), "info", crop,
                                  lambda ls: P.parse_box(ls, "info", cfg), P.box_same,
                                  meta={"tipo": "info", "problema": "pannello_senza_righe"}))
        else:
            hint = {"giallo": "giallo", "chiaro": "chiaro", "bianco": "bianco"}.get(b.famiglia, "info")
            kind = "info" if hint == "info" else "riquadro"
            units.append(Unit(nuovo_id("riquadro"), kind, crop,
                              (lambda h: (lambda ls: P.parse_box(ls, h, cfg)))(hint),
                              P.box_same, meta={"tipo": "box", "hint": hint}))

    res = {
        "_source": path.name, "giorno": None, "data": None, "data_numero": None, "mese": None,
        "entrate": [], "uscite": [], "senza_lezioni_pomeridiane": [],
        "cambi_aula": [], "note": [], "avvisi": [], "controllo": [],
    }
    if not titoli:
        res["avvisi"].append("titolo_non_trovato")

    log(f"[INFO] {path.name}: {len(units)} unita' da leggere con "
        f"{', '.join(e.name for e in engines)}")

    for u in units:
        dec = leggi_unita(u, engines, cfg)
        if crops_dir is not None:
            cv2.imwrite(str(crops_dir / f"{u.uid}.png"),
                        cv2.resize(u.crop, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC))
        _applica(res, u, dec, crops_dir)

    _controlli_globali(res)
    res["n_da_verificare"] = sum(1 for c in res["controllo"] if c["stato"] == "revisione")
    res["n_dissensi"] = sum(1 for c in res["controllo"] if c["stato"] == "dissenso")
    res["stato"] = "completo" if res["n_da_verificare"] == 0 else "da_verificare"
    return res


# ---------------------------------------------------------------------------
# Composizione del risultato
# ---------------------------------------------------------------------------
def _verifica(dec):
    return {"ok": "ok", "dissenso": "ok", "revisione": "da_verificare"}[dec.status]


def _registra(res, u, dec, crops_dir, tipo):
    if dec.status == "ok":
        return
    res["controllo"].append({
        "id": u.uid, "tipo": tipo, "stato": dec.status, "motivi": dec.reasons,
        "ritaglio": str(crops_dir / f"{u.uid}.png") if crops_dir else None,
        "letture": _letture_txt(dec),
        "voti": dec.votes,
    })


def _applica(res, u, dec, crops_dir):
    p = dec.value
    t = u.meta.get("tipo")
    if dec.status in ("ok", "dissenso"):
        for rs in dec.reasons:
            if rs.startswith("avviso:"):
                res["avvisi"].append(f"{u.uid}: {rs[7:]} (accettato: tutti i motori concordano)")

    if t == "titolo":
        if p is not None and not p.fatal:
            res["giorno"], res["data_numero"], res["mese"] = p.giorno, p.numero, p.mese
            res["data"] = f"{p.numero:02d} {p.mese}"
        res["titolo_unit_id"] = u.uid
        res["titolo_verifica"] = _verifica(dec)
        _registra(res, u, dec, crops_dir, "titolo")
        return

    if t == "riga":
        sosp = u.meta.get("sospetta")
        usabili = [r.parsed for r in dec.readings if r.parsed is not None and not r.parsed.fatal]
        solo_header = (not any(not x.is_header for x in usabili)) and any(x.is_header for x in usabili)
        if solo_header:
            return
        item = {"unit_id": u.uid, "classe": None, "orario": None, "aula": None,
                "verifica": _verifica(dec)}
        if p is not None and not p.fatal and not p.is_header:
            item["classe"] = p.classe
            item["orario"] = f"{p.da} - {p.a}"
            item["aula"] = p.aula
            if p.marker:
                item["marcatore"] = p.marker
        elif dec.status == "ok":      # non dovrebbe accadere
            item["verifica"] = "da_verificare"
        if sosp and dec.status == "ok":
            dec.reasons.append("avviso:ritaglio_riga_stimato")
        res["cambi_aula"].append(item)
        _registra(res, u, dec, crops_dir, "riga")
        return

    # --- riquadri
    if p is None or getattr(p, "fatal", False):
        res["note"].append({"unit_id": u.uid, "tipo": "generico", "testo": None,
                            "verifica": "da_verificare"})
        _registra(res, u, dec, crops_dir, "info")
        return

    if p.kind in ("entra", "esce"):
        item = {"unit_id": u.uid, "ora": p.ora,
                "classi": [c.classe for c in p.classi],
                "note": " ".join(p.note_lines), "verifica": _verifica(dec)}
        marc = {c.classe: c.marker for c in p.classi if c.marker}
        if marc:
            item["marcatori"] = marc
        res["entrate" if p.kind == "entra" else "uscite"].append(item)
        _registra(res, u, dec, crops_dir, p.kind)
    elif p.kind == "nolez":
        item = {"unit_id": u.uid, "classi": [c.classe for c in p.classi],
                "note": " ".join(p.note_lines), "verifica": _verifica(dec)}
        marc = {c.classe: c.marker for c in p.classi if c.marker}
        if marc:
            item["marcatori"] = marc
        res["senza_lezioni_pomeridiane"].append(item)
        _registra(res, u, dec, crops_dir, "nolez")
    else:
        res["note"].append({"unit_id": u.uid, "tipo": classifica_nota(p.testo),
                            "testo": p.testo, "verifica": _verifica(dec)})
        _registra(res, u, dec, crops_dir, "info")


def _controlli_globali(res):
    """Controlli di coerenza tra unita' diverse (solo avvisi)."""
    from collections import defaultdict

    def minuti(t):
        return int(t[:2]) * 60 + int(t[3:])

    # stessa classe in due aule con orari sovrapposti
    per_classe = defaultdict(list)
    for r in res["cambi_aula"]:
        if r["classe"] and r["orario"]:
            a, b = r["orario"].split(" - ")
            per_classe[r["classe"]].append((minuti(a), minuti(b), r["aula"], r["unit_id"]))
    for cl, lst in per_classe.items():
        lst.sort()
        for i in range(len(lst)):
            for j in range(i + 1, len(lst)):
                if lst[j][0] < lst[i][1] and lst[i][2] != lst[j][2]:
                    res["avvisi"].append(
                        f"classe {cl}: orari sovrapposti in aule diverse "
                        f"({lst[i][2]} / {lst[j][2]})")
    # righe duplicate
    viste = {}
    for r in res["cambi_aula"]:
        k = (r["classe"], r["orario"], r["aula"])
        if k in viste and r["classe"]:
            res["avvisi"].append(f"riga duplicata: {k}")
        viste[k] = True
    # stesso tipo+orario ripetuto
    for chiave in ("entrate", "uscite"):
        visti = set()
        for e in res[chiave]:
            if e["ora"] in visti:
                res["avvisi"].append(f"{chiave}: orario {e['ora']} ripetuto")
            visti.add(e["ora"])
    # stessa classe sia in entrata che in uscita allo stesso orario
    for e in res["entrate"]:
        for u in res["uscite"]:
            if e["ora"] == u["ora"]:
                comuni = set(e["classi"]) & set(u["classi"])
                if comuni:
                    res["avvisi"].append(
                        f"classi {sorted(comuni)} sia in entrata che in uscita alle {e['ora']}")
