"""
Pipeline: immagine -> riquadri/righe -> lettura Qwen3-VL -> validazione -> JSON.

Un solo motore (Qwen3-VL via Ollama, una passata). La sicurezza dei dati viene dai
validatori: formato, elenchi di classi/aule, griglia degli orari, coerenza tra voci
(vedi validazione.py e _controlli_globali).
"""
import datetime
import re
import sys
import time
from pathlib import Path

import cv2

from . import parse as P
from .engines import EngineUnavailable, OllamaVLM
from .segment import righe_pannello, ritaglia_riga, segmenta_riquadri
from .validazione import ALTA, BASSA, MEDIA, Esito, livello_da_motivi, valuta

SCHEMA_VERSIONE = 2


def _log(log, message):
    """Scrive subito i progressi anche quando stdout e' bufferizzato."""
    log(message)
    for stream in (sys.stdout, sys.stderr):
        if stream is not None:
            stream.flush()


# ---------------------------------------------------------------------------
# Motore
# ---------------------------------------------------------------------------
def build_engine(cfg: dict, log=print) -> OllamaVLM:
    oc = cfg["ollama"]
    scale = oc.get("scale", 3)
    if isinstance(scale, list):          # vecchio config.json: una sola passata, si usa la prima
        scale = scale[0]
    try:
        return OllamaVLM(oc["host"], oc["model"], scale=scale,
                         num_ctx=oc.get("num_ctx", 4096),
                         timeout_s=oc.get("timeout_s", 900),
                         keep_alive=oc.get("keep_alive", "10m"),
                         think=oc.get("think"))
    except EngineUnavailable as e:
        raise SystemExit(f"[ERRORE] {e}")


# ---------------------------------------------------------------------------
# Lettura di un'unita'
# ---------------------------------------------------------------------------
class Unit:
    def __init__(self, uid, kind, crop, parse_fn, meta=None):
        self.uid = uid
        self.kind = kind              # tipo per il motore: riga | riquadro | info | titolo
        self.crop = crop
        self.parse_fn = parse_fn
        self.meta = meta or {}


class Lettura:
    """Esito della lettura di un'unita': testo, interpretazione, affidabilita'."""
    def __init__(self, lines, parsed, errore, esito):
        self.lines, self.parsed, self.errore, self.esito = lines, parsed, errore, esito


def leggi_unita(unit: Unit, engine, log=print) -> Lettura:
    lines, parsed, errore = [], None, None
    started = time.perf_counter()
    if not engine.supports(unit.kind):
        errore = "tipo_di_unita_non_supportato"
    else:
        try:
            lines = engine.read(unit.crop, unit.kind)
            parsed = unit.parse_fn(lines)
        except Exception as ex:     # noqa: BLE001
            errore = f"{type(ex).__name__}: {ex}"
            _log(log, f"[LETTURA] {unit.uid} | ERRORE dopo "
                 f"{time.perf_counter() - started:.1f}s: {errore}")
    return Lettura(lines, parsed, errore, None)


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


# ---------------------------------------------------------------------------
# Pipeline principale
# ---------------------------------------------------------------------------
def processa_immagine(path, engine, cfg, outdir=None, log=print):
    if isinstance(engine, (list, tuple)):       # compatibilita': si usa il primo motore
        engine = engine[0]
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

    started = time.perf_counter()
    _log(log, f"[INFO] {path.name}: segmentazione immagine in corso")
    boxes = segmenta_riquadri(img)
    _log(log, f"[INFO] {path.name}: segmentazione completata in "
         f"{time.perf_counter() - started:.1f}s ({len(boxes)} riquadri)")
    units = []
    n = 0

    def nuovo_id(tag):
        nonlocal n
        n += 1
        return f"{stem}_{n:02d}_{tag}"

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
                units.append(Unit(nuovo_id(f"riga{i:02d}"), "riga", rc,
                                  lambda ls: P.parse_row(" ".join(ls), cfg),
                                  meta={"tipo": "riga", "sospetta": r.sospetta}))
            if not rows:
                units.append(Unit(nuovo_id("pannello_senza_righe"), "info", crop,
                                  lambda ls: P.parse_box(ls, "info", cfg),
                                  meta={"tipo": "info", "problema": "pannello_senza_righe"}))
        else:
            hint = {"giallo": "giallo", "chiaro": "chiaro", "bianco": "bianco"}.get(b.famiglia, "info")
            kind = "info" if hint == "info" else "riquadro"
            if kind == "info" and not cfg.get("leggi_note_libere", False):
                continue                # riquadri informativi (FSL, viaggi, ...): non servono, si risparmia una lettura
            units.append(Unit(nuovo_id("riquadro"), kind, crop,
                              (lambda h: (lambda ls: P.parse_box(ls, h, cfg)))(hint),
                              meta={"tipo": "box", "hint": hint}))

    res = {
        "schema_versione": SCHEMA_VERSIONE,
        "_source": path.name,
        "estratto_il": datetime.datetime.now().replace(microsecond=0).isoformat(),
        "motore": {"modello": getattr(engine, "model", engine.name),
                   "scala": getattr(engine, "scale", None)},
        "giorno": None, "data": None, "data_numero": None, "mese": None, "data_iso": None,
        "titolo_unit_id": None, "titolo_affidabilita": BASSA, "titolo_motivi": [],
        "titolo_verifica": "da_verificare",
        "entrate": [], "uscite": [], "senza_lezioni_pomeridiane": [],
        "cambi_aula": [], "note": [], "avvisi": [],
    }
    letti = {}          # unit_id -> (tipo, righe grezze lette dal modello)
    if not any(u.meta.get("tipo") == "titolo" for u in units):
        res["avvisi"].append("titolo_non_trovato")

    _log(log, f"[INFO] {path.name}: {len(units)} unita' da leggere con {engine.name}")
    total_started = time.perf_counter()
    for index, u in enumerate(units, 1):
        unit_started = time.perf_counter()
        _log(log, f"[UNITA] {index}/{len(units)} {u.uid} ({u.kind}) | lettura")
        let = leggi_unita(u, engine, log=log)
        if crops_dir is not None:
            cv2.imwrite(str(crops_dir / f"{u.uid}.png"),
                        cv2.resize(u.crop, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC))
        _applica(res, u, let, letti)
        _log(log, f"[UNITA] {index}/{len(units)} {u.uid} | affidabilita="
             f"{let.esito.affidabilita} | durata={time.perf_counter() - unit_started:.1f}s")

    _controlli_globali(res)
    _chiudi(res, letti, stem if crops_dir is not None else None)
    _log(log, f"[INFO] {path.name}: elaborazione completata in "
         f"{time.perf_counter() - total_started:.1f}s")
    return res


# ---------------------------------------------------------------------------
# Composizione del risultato
# ---------------------------------------------------------------------------
def _verifica(affidabilita):
    return "ok" if affidabilita == ALTA else "da_verificare"


def _voce(u, esito, **campi):
    """Voce del JSON: campi propri + unit_id + affidabilita'/motivi (+ 'verifica' per compatibilita')."""
    item = {"unit_id": u.uid, **campi,
            "affidabilita": esito.affidabilita, "motivi": list(esito.motivi),
            "verifica": _verifica(esito.affidabilita)}
    return item


def _abbassa(item, livello, motivo):
    e = Esito(item["affidabilita"], item["motivi"])
    e.abbassa(livello, motivo)
    item["affidabilita"], item["motivi"] = e.affidabilita, e.motivi
    item["verifica"] = _verifica(e.affidabilita)


def _tipo_nota(u, tipo):
    """Un riquadro colorato (entra/esce/no lez.) o un pannello senza righe che finisce tra le note
    NON e' una nota: e' un dato principale non letto, e deve restare tra le voci da verificare."""
    if u.meta.get("problema") or u.meta.get("hint", "info") != "info":
        return "riquadro_non_letto"
    return tipo


def _applica(res, u, let, letti):
    p, t = let.parsed, u.meta.get("tipo")
    righe = list(let.lines or [])
    if let.errore:
        righe = [f"[errore] {let.errore}"]

    if t == "titolo":
        e = valuta(p, let.errore)
        if p is not None and not p.fatal:
            res["giorno"], res["data_numero"], res["mese"] = p.giorno, p.numero, p.mese
            res["data"] = f"{p.numero:02d} {p.mese}"
            res["data_iso"] = p.iso
        res["titolo_unit_id"] = u.uid
        res["titolo_affidabilita"], res["titolo_motivi"] = e.affidabilita, e.motivi
        res["titolo_verifica"] = _verifica(e.affidabilita)
        letti[u.uid] = ("titolo", righe)
        let.esito = e
        return

    if t == "riga":
        if p is not None and not p.fatal and p.is_header:
            let.esito = Esito()
            return                                  # intestazione "CAMBIO AULA": non e' un dato
        e = valuta(p, let.errore)
        if u.meta.get("sospetta"):
            e.abbassa(MEDIA, "ritaglio_riga_stimato")
        campi = {"classe": None, "orario": None, "aula": None}
        if p is not None and not p.fatal and not p.is_header:
            campi.update(classe=p.classe, orario=f"{p.da} - {p.a}", aula=p.aula)
            if p.marker:
                campi["marcatore"] = p.marker
        res["cambi_aula"].append(_voce(u, e, **campi))
        letti[u.uid] = ("riga", righe)
        let.esito = e
        return

    # --- riquadri
    if p is None or getattr(p, "fatal", False):
        e = valuta(p, let.errore)
        res["note"].append(_voce(u, e, tipo=_tipo_nota(u, "generico"), testo=None))
        letti[u.uid] = ("info", righe)
        let.esito = e
        return

    if p.kind in ("entra", "esce", "nolez"):
        nota = " ".join(p.note_lines)
        e = valuta(p, let.errore, testo_libero=nota if nota.strip() else None)
        campi = {}
        if p.kind != "nolez":
            campi["ora"] = p.ora
        campi["classi"] = [c.classe for c in p.classi]
        campi["note"] = nota
        marc = {c.classe: c.marker for c in p.classi if c.marker}
        if marc:
            campi["marcatori"] = marc
        chiave = {"entra": "entrate", "esce": "uscite", "nolez": "senza_lezioni_pomeridiane"}[p.kind]
        res[chiave].append(_voce(u, e, **campi))
        letti[u.uid] = (p.kind, righe)
    else:
        e = valuta(p, let.errore, testo_libero=p.testo)
        res["note"].append(_voce(u, e, tipo=_tipo_nota(u, classifica_nota(p.testo)), testo=p.testo))
        letti[u.uid] = ("info", righe)
    let.esito = e


# ---------------------------------------------------------------------------
# Controlli di coerenza TRA unita' diverse
# ---------------------------------------------------------------------------
def _minuti(t):
    return int(t[:2]) * 60 + int(t[3:])


def _chiave_classe(c):
    m = re.match(r"^(\d)([A-Z]+)(\d?)", c or "")
    return (int(m.group(1)), m.group(2), m.group(3)) if m else None


def _fuori_ordine(chiavi):
    """Indici di elementi che rompono l'ordine non decrescente: quelli esclusi dalla piu'
    lunga sottosequenza ordinata + entrambi gli elementi di ogni inversione adiacente."""
    n = len(chiavi)
    if n < 2:
        return set()
    best, prev = [1] * n, [-1] * n
    for i in range(n):
        for j in range(i):
            if chiavi[j] <= chiavi[i] and best[j] + 1 > best[i]:
                best[i], prev[i] = best[j] + 1, j
    i = max(range(n), key=lambda k: best[k])
    dentro = set()
    while i != -1:
        dentro.add(i)
        i = prev[i]
    fuori = set(range(n)) - dentro
    for i in range(n - 1):
        if chiavi[i] > chiavi[i + 1]:
            fuori |= {i, i + 1}
    return fuori


def _controlli_globali(res):
    """Controlli di coerenza tra voci diverse. Abbassano l'affidabilita' delle voci coinvolte
    e aggiungono una riga a 'avvisi'."""
    from collections import defaultdict
    righe = res["cambi_aula"]
    per_id = {r["unit_id"]: r for r in righe}

    # 0) un marcatore (*, °) puo' avere la sua nota in un altro riquadro (es. nel riquadro
    #    del torneo: "° GLI STUDENTI CHE NON PARTECIPANO..."): in quel caso non e' un problema
    righe_note = {ln.strip()[:1] for n in res["note"] for ln in (n.get("testo") or "").splitlines()}
    for chiave in ("entrate", "uscite", "senza_lezioni_pomeridiane"):
        for e in res[chiave]:
            if "marcatore_senza_nota" in e["motivi"] and all(
                    m[:1] in righe_note for m in e.get("marcatori", {}).values()):
                e["motivi"].remove("marcatore_senza_nota")
                e["affidabilita"] = livello_da_motivi(e["motivi"])
                e["verifica"] = _verifica(e["affidabilita"])

    # 1) il pannello CAMBIO AULA e' in ordine alfabetico di classe (vero in tutte le immagini
    #    di riferimento): una classe letta male di solito rompe l'ordine
    con_classe = [r for r in righe if _chiave_classe(r["classe"])]
    for i in _fuori_ordine([_chiave_classe(r["classe"]) for r in con_classe]):
        r = con_classe[i]
        _abbassa(r, MEDIA, "classe_fuori_ordine_alfabetico")
        res["avvisi"].append(f"{r['unit_id']}: classe {r['classe']} fuori dall'ordine alfabetico del pannello")

    # 2) stessa classe in due aule con orari sovrapposti
    per_classe = defaultdict(list)
    for r in righe:
        if r["classe"] and r["orario"]:
            a, b = r["orario"].split(" - ")
            per_classe[r["classe"]].append((_minuti(a), _minuti(b), r["aula"], r["unit_id"]))
    for cl, lst in per_classe.items():
        lst.sort()
        for i in range(len(lst)):
            for j in range(i + 1, len(lst)):
                if lst[j][0] < lst[i][1] and lst[i][2] != lst[j][2]:
                    res["avvisi"].append(f"classe {cl}: orari sovrapposti in aule diverse "
                                         f"({lst[i][2]} / {lst[j][2]})")
                    for k in (i, j):
                        _abbassa(per_id[lst[k][3]], MEDIA, "orari_sovrapposti_aule_diverse")

    # 3) righe duplicate
    viste = {}
    for r in righe:
        k = (r["classe"], r["orario"], r["aula"])
        if r["classe"] and k in viste:
            res["avvisi"].append(f"riga duplicata: {k}")
            _abbassa(r, MEDIA, "riga_duplicata")
        viste[k] = True

    # 4) stesso tipo+orario ripetuto (solo avviso)
    for chiave in ("entrate", "uscite"):
        visti = set()
        for e in res[chiave]:
            if e.get("ora") in visti:
                res["avvisi"].append(f"{chiave}: orario {e['ora']} ripetuto")
            visti.add(e.get("ora"))

    # 5) stessa classe sia in entrata che in uscita alla stessa ora
    for e in res["entrate"]:
        for u in res["uscite"]:
            if e.get("ora") and e.get("ora") == u.get("ora"):
                comuni = set(e["classi"]) & set(u["classi"])
                if comuni:
                    res["avvisi"].append(
                        f"classi {sorted(comuni)} sia in entrata che in uscita alle {e['ora']}")
                    _abbassa(e, MEDIA, "classe_in_entrata_e_uscita_stessa_ora")
                    _abbassa(u, MEDIA, "classe_in_entrata_e_uscita_stessa_ora")

    # 6) classe "senza lezioni pomeridiane" con un cambio aula nel pomeriggio
    nolez = {c for x in res["senza_lezioni_pomeridiane"] for c in x["classi"]}
    for r in righe:
        if r["classe"] in nolez and r["orario"] and _minuti(r["orario"].split(" - ")[1]) > _minuti("14:30"):
            res["avvisi"].append(f"classe {r['classe']}: senza lezioni pomeridiane ma cambio aula "
                                 f"alle {r['orario']}")
            _abbassa(r, MEDIA, "cambio_aula_pomeridiano_con_no_lezioni_pomeridiane")


def _chiudi(res, letti, stem_ritagli):
    """Conteggi, elenco 'da_verificare' (con ritaglio e testo letto) e stato finale."""
    tutte = []
    if res["titolo_unit_id"]:
        tutte.append(("titolo", res["titolo_unit_id"], res["titolo_affidabilita"], res["titolo_motivi"]))
    for chiave, tipo in (("cambi_aula", "riga"), ("entrate", "entra"), ("uscite", "esce"),
                         ("senza_lezioni_pomeridiane", "nolez")):
        for it in res[chiave]:
            tutte.append((tipo, it["unit_id"], it["affidabilita"], it["motivi"]))
    # note libere (presenti solo con leggi_note_libere): sono dati come gli altri
    for it in res["note"]:
        tipo = "riquadro_non_letto" if it["tipo"] == "riquadro_non_letto" else "info"
        tutte.append((tipo, it["unit_id"], it["affidabilita"], it["motivi"]))
    res["da_verificare"] = [
        {"id": uid, "tipo": tipo, "affidabilita": aff, "motivi": list(motivi),
         "letto": letti.get(uid, (tipo, []))[1],
         "ritaglio": f"{stem_ritagli}_ritagli/{uid}.png" if stem_ritagli else None}
        for tipo, uid, aff, motivi in tutte if aff != ALTA]
    res["da_verificare"].sort(key=lambda x: (x["affidabilita"] != BASSA, x["id"]))
    res["n_voci"] = len(tutte)
    res["n_alta"] = sum(1 for x in tutte if x[2] == ALTA)
    res["n_media"] = sum(1 for x in tutte if x[2] == MEDIA)
    res["n_bassa"] = sum(1 for x in tutte if x[2] == BASSA)
    res["n_da_verificare"] = res["n_media"] + res["n_bassa"]
    res["stato"] = "completo" if res["n_da_verificare"] == 0 and res["titolo_unit_id"] else "da_verificare"
