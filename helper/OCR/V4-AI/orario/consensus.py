"""
Consenso tra motori indipendenti.

Principio: un dato entra nel risultato "verificato" solo se
  1. e' formalmente valido (regole rigide), e
  2. almeno `voti_minimi` motori di FAMIGLIA DIVERSA lo leggono allo stesso modo.
Altrimenti finisce in revisione umana, con il ritaglio dell'immagine.
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class Reading:
    engine: str                    # es. 'ollama:qwen3-vl:4b@3x'
    family: str                    # es. 'ollama' | 'rapidocr' | 'tesseract'
    lines: list = field(default_factory=list)
    parsed: Any = None
    error: Optional[str] = None


@dataclass
class Decision:
    value: Any                     # oggetto parsed scelto (o None)
    status: str                    # 'ok' | 'dissenso' | 'revisione'
    votes: int = 0
    reasons: list = field(default_factory=list)
    readings: list = field(default_factory=list)
    n_motori: int = 0


def decide(readings, priority, voti_minimi=2, politica="maggioranza",
           same: Optional[Callable] = None) -> Decision:
    """
    readings : lista di Reading
    priority : lista di famiglie, dalla piu' alla meno affidabile
    same     : funzione (a,b)->bool per confrontare due parsed; default key()==key()
    """
    if same is None:
        def same(a, b):
            return a.key() == b.key()

    def prio(rd):
        try:
            return priority.index(rd.family)
        except ValueError:
            return len(priority)

    usable = sorted([r for r in readings if r.parsed is not None and r.error is None], key=prio)
    families_total = len({r.family for r in readings})
    dec = Decision(value=None, status="revisione", readings=readings, n_motori=families_total)

    if not usable:
        dec.reasons.append("nessun_motore_ha_prodotto_una_lettura")
        return dec

    # clustering greedy in ordine di priorita'
    clusters = []     # lista di liste di Reading
    for rd in usable:
        for cl in clusters:
            if same(cl[0].parsed, rd.parsed):
                cl.append(rd)
                break
        else:
            clusters.append([rd])

    def cluster_votes(cl):
        return len({r.family for r in cl})

    def cluster_ok(cl):
        p = cl[0].parsed
        return (not p.fatal) and not p.problems

    # cluster migliore: validi per primi, poi piu' voti, poi priorita'
    clusters.sort(key=lambda cl: (not cluster_ok(cl), -cluster_votes(cl), prio(cl[0])))
    best = clusters[0]
    rep = best[0].parsed
    dec.value = rep
    dec.votes = cluster_votes(best)

    # -- motivi di blocco
    if rep.fatal:
        dec.reasons.append("lettura_non_interpretabile")
    for p in rep.problems:
        dec.reasons.append(p)

    soglia = voti_minimi
    if families_total < voti_minimi:
        # meno motori disponibili del minimo richiesto: non e' possibile verificare
        soglia = families_total
        dec.reasons.append(f"verifica_incrociata_impossibile_motori={families_total}")
        # con un solo motore nessun dato e' mai 'ok'
        if families_total <= 1:
            dec.status = "revisione"
            return dec

    if dec.votes < soglia:
        dec.reasons.append(f"accordo_insufficiente_{dec.votes}_su_{soglia}")
    if rep.warnings and dec.votes < max(2, families_total):
        dec.reasons.append("avviso_richiede_accordo_totale:" + ",".join(rep.warnings))

    bloccato = any(not r.startswith(("verifica_incrociata_impossibile", )) for r in dec.reasons)
    if bloccato:
        dec.status = "revisione"
        return dec

    # -- dissensi (motori che leggono altro)
    altri = [r for cl in clusters[1:] for r in cl]
    if altri:
        dec.reasons.append("dissenso:" + "; ".join(
            f"{r.family}='{getattr(r.parsed, 'short', lambda: '?')()}'" for r in altri))
        if politica == "unanime":
            dec.status = "revisione"
            return dec
        dec.status = "dissenso"
        return dec

    for p in rep.warnings:
        dec.reasons.append("avviso:" + p)
    dec.status = "ok"
    return dec
