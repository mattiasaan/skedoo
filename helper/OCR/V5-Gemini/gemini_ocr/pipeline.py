"""Pipeline: immagine -> riquadri/righe (OpenCV, V4) -> lettura Gemini (una richiesta) -> validazione (V4) -> JSON.

Il JSON è quello di orario.pipeline.processa_immagine della V4 (schema_versione 2): stessi unit_id, stesse
voci, stessi controlli. Cambiano solo il motore (`motore.modello` = modello Gemini usato) e il fatto che
tutti i ritagli vengono letti insieme invece che uno alla volta. Unica aggiunta: i giorni abbreviati nel
titolo (MER. 25 NOVEMBRE) vengono espansi prima del parser della V4 (espandi_giorno), e per i riquadri
NO LEZ. POM. il colore non conta (parse_riquadro).

La costruzione delle unità ricalca il ciclo di processa_immagine della V4: se cambia lì, va aggiornata qui
(i test di test_pipeline.py confrontano le due uscite con lo stesso testo letto).
"""
from __future__ import annotations

import datetime
import re
import time
from pathlib import Path

import cv2

from .v4 import parse as P
from .v4 import pipeline as V4
from .v4 import righe_pannello, ritaglia_riga, segmenta_riquadri


_PAROLA_INIZIALE = re.compile(r"^\s*([A-Za-zÀ-ÿ']+)\.?\s*")


def espandi_giorno(testo: str) -> str:
    """'MER. 25 NOVEMBRE' -> 'MERCOLEDÌ 25 NOVEMBRE'. Il parser della V4 riconosce solo i giorni scritti per
    intero; il cartellone a volte li abbrevia. Si espande solo un prefisso di almeno 3 lettere che indica un
    solo giorno (MAR -> MARTEDÌ, MER -> MERCOLEDÌ); il controllo giorno/data della V4 resta valido."""
    m = _PAROLA_INIZIALE.match(testo or "")
    if not m:
        return testo
    parola = P.norm(m.group(1)).replace("Ì", "I").rstrip("'")
    if len(parola) < 3:
        return testo
    giorni = [g for g in P.GIORNI if g.replace("Ì", "I").startswith(parola)]
    if len(giorni) != 1 or giorni[0].replace("Ì", "I") == parola:
        return testo
    return f"{giorni[0]} {testo[m.end():]}".strip()


def parse_riquadro(lines, hint: str, cfg: dict):
    """parse_box della V4, ma per NO LEZ. POM. il colore del riquadro non conta: la scuola lo stampa sia
    bianco sia giallo, e l'intestazione "NO LEZ." non si confonde con ENTRA/ESCE. Per ENTRA/ESCE il controllo
    del colore resta (scambiarli sposterebbe classi in entrata/uscita)."""
    r = P.parse_box(lines, hint, cfg)
    if r.kind == "nolez":
        r.problems = [p for p in r.problems if not (p.startswith("colore_") and p.endswith("_incoerente_con_nolez"))]
    return r


def costruisci_unita(img, stem: str, cfg: dict) -> list:
    """Ritagli da leggere, con lo stesso ordine e gli stessi id della V4."""
    units, n = [], 0

    def nuovo_id(tag):
        nonlocal n
        n += 1
        return f"{stem}_{n:02d}_{tag}"

    for b in segmenta_riquadri(img):
        crop = b.crop(img)
        if b.famiglia == "titolo":
            units.append(V4.Unit(nuovo_id("titolo"), "titolo", crop,
                                 lambda ls: P.parse_title(espandi_giorno(" ".join(ls)), cfg),
                                 meta={"tipo": "titolo"}))
        elif b.famiglia == "cambio_aula":
            rows = righe_pannello(crop)
            for i, r in enumerate(rows):
                units.append(V4.Unit(nuovo_id(f"riga{i:02d}"), "riga", ritaglia_riga(crop, r),
                                     lambda ls: P.parse_row(" ".join(ls), cfg),
                                     meta={"tipo": "riga", "sospetta": r.sospetta}))
            if not rows:
                units.append(V4.Unit(nuovo_id("pannello_senza_righe"), "info", crop,
                                     lambda ls: P.parse_box(ls, "info", cfg),
                                     meta={"tipo": "info", "problema": "pannello_senza_righe"}))
        else:
            hint = {"giallo": "giallo", "chiaro": "chiaro", "bianco": "bianco"}.get(b.famiglia, "info")
            kind = "info" if hint == "info" else "riquadro"
            if kind == "info" and not cfg.get("leggi_note_libere", False):
                continue    # riquadri informativi (FSL, viaggi, docenti assenti): non letti e non inviati a Google
            units.append(V4.Unit(nuovo_id("riquadro"), kind, crop,
                                 (lambda h: (lambda ls: parse_riquadro(ls, h, cfg)))(hint),
                                 meta={"tipo": "box", "hint": hint}))
    return units


def _leggi(units, engine, log):
    """Tutte le unità in una lettura; per ognuna una V4.Lettura (errore se il modello non l'ha restituita)."""
    da_leggere = [u for u in units if engine.supports(u.kind)]
    letti = engine.read_batch([(u.uid, u.kind, u.crop) for u in da_leggere]) if da_leggere else {}
    out = []
    for u in units:
        lines, parsed, errore = [], None, None
        if not engine.supports(u.kind):
            errore = "tipo_di_unita_non_supportato"
        elif u.uid not in letti:
            errore = "unita_assente_nella_risposta"
        else:
            lines = letti[u.uid]
            try:
                parsed = u.parse_fn(lines)
            except Exception as ex:     # noqa: BLE001 - come la V4: la voce diventa 'bassa'
                errore = f"{type(ex).__name__}: {ex}"
        if errore:
            V4._log(log, f"[LETTURA] {u.uid} | ERRORE: {errore}")
        out.append(V4.Lettura(lines, parsed, errore, None))
    return out


def processa_array(img, nome: str, engine, cfg: dict, outdir=None, log=print) -> dict:
    """Come processa_immagine, ma dall'immagine già decodificata (il servizio non scrive file)."""
    stem = Path(nome).stem
    outdir = Path(outdir) if outdir else None
    crops_dir = None
    if outdir and cfg.get("salva_ritagli", True):
        crops_dir = outdir / f"{stem}_ritagli"
        crops_dir.mkdir(parents=True, exist_ok=True)

    started = time.perf_counter()
    units = costruisci_unita(img, stem, cfg)
    V4._log(log, f"[INFO] {nome}: segmentazione in {time.perf_counter() - started:.1f}s, "
            f"{len(units)} unita' da leggere con Gemini")

    read_started = time.perf_counter()
    letture = _leggi(units, engine, log)
    V4._log(log, f"[INFO] {nome}: lettura Gemini ({engine.model}) in {time.perf_counter() - read_started:.1f}s")

    res = {
        "schema_versione": V4.SCHEMA_VERSIONE,
        "_source": nome,
        "estratto_il": datetime.datetime.now().replace(microsecond=0).isoformat(),
        "motore": {"modello": engine.model, "scala": engine.scale},
        "giorno": None, "data": None, "data_numero": None, "mese": None, "data_iso": None,
        "titolo_unit_id": None, "titolo_affidabilita": V4.BASSA, "titolo_motivi": [],
        "titolo_verifica": "da_verificare",
        "entrate": [], "uscite": [], "senza_lezioni_pomeridiane": [],
        "cambi_aula": [], "note": [], "avvisi": [],
    }
    raw = {}
    if not any(u.meta.get("tipo") == "titolo" for u in units):
        res["avvisi"].append("titolo_non_trovato")
    for u, let in zip(units, letture):
        if crops_dir is not None:
            cv2.imwrite(str(crops_dir / f"{u.uid}.png"),
                        cv2.resize(u.crop, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC))
        V4._applica(res, u, let, raw, cfg)

    V4._controlli_globali(res, note_lette=bool(cfg.get("leggi_note_libere", False)))
    V4._chiudi(res, raw, stem if crops_dir is not None else None)
    V4._log(log, f"[INFO] {nome}: completato in {time.perf_counter() - started:.1f}s | stato={res['stato']} "
            f"voci={res['n_voci']} (alta={res['n_alta']} media={res['n_media']} bassa={res['n_bassa']})")
    return res


def processa_immagine(path, engine, cfg: dict, outdir=None, log=print) -> dict:
    path = Path(path)
    img = cv2.imread(str(path))
    if img is None:
        raise FileNotFoundError(f"Impossibile aprire l'immagine: {path}")
    return processa_array(img, path.name, engine, cfg, outdir=outdir, log=log)
