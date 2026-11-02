"""
Validazione di una lettura di Qwen (nessun altro motore: la sicurezza viene dai controlli).

Ogni unita' letta riceve un'AFFIDABILITA':

  alta   superati tutti i controlli: formato, elenchi (classi, aule), griglia degli orari,
         coerenza interna (orari, colore del riquadro, titolo, note)
  media  formalmente valida ma con un elemento anomalo: classe o aula non in elenco,
         lettura "riparata" dal parser, caratteri strani nel testo libero
  bassa  non interpretabile, regola dura violata (classe assente, orario fuori griglia,
         inizio dopo la fine, ...) o nessuna lettura

L'affidabilita' puo' essere abbassata ancora dai controlli *tra* unita' (pipeline.py):
ordine alfabetico, sovrapposizioni, duplicati.

Limite onesto: un valore sbagliato ma formalmente valido e coerente (es. 3H letto 3F, con 3F
in elenco) non puo' essere riconosciuto da nessun controllo senza un secondo lettore.
"""
from dataclasses import dataclass, field

ALTA, MEDIA, BASSA = "alta", "media", "bassa"
_ORDINE = {ALTA: 0, MEDIA: 1, BASSA: 2}

# Avvisi del parser che, con un solo lettore, valgono come errore e non come semplice anomalia:
# la griglia degli orari e' chiusa, e un giorno della settimana incoerente con la data
# e' sempre un errore di lettura (o un anno sbagliato: vedi --anno).
_AVVISI_GRAVI = ("orario_fuori_elenco", "giorno_settimana_incoerente_con_data")


@dataclass
class Esito:
    affidabilita: str = ALTA
    motivi: list = field(default_factory=list)

    def abbassa(self, livello: str, motivo: str):
        if motivo not in self.motivi:
            self.motivi.append(motivo)
        if _ORDINE[livello] > _ORDINE[self.affidabilita]:
            self.affidabilita = livello


def peggiore(a: str, b: str) -> str:
    return a if _ORDINE[a] >= _ORDINE[b] else b


def valuta(parsed, errore=None, testo_libero=None) -> Esito:
    """
    parsed       : oggetto restituito da parse_row / parse_title / parse_box (o None)
    errore       : stringa se il motore ha fallito
    testo_libero : per i riquadri informativi, il testo letto (controllo dei caratteri)
    """
    e = Esito()
    if errore:
        e.abbassa(BASSA, "lettura_fallita")
        return e
    if parsed is None:
        e.abbassa(BASSA, "nessuna_lettura")
        return e
    if getattr(parsed, "fatal", False):
        e.abbassa(BASSA, "lettura_non_interpretabile")
    for p in parsed.problems:
        e.abbassa(BASSA, p)
    for w in parsed.warnings:
        grave = any(w.startswith(g) for g in _AVVISI_GRAVI)
        e.abbassa(BASSA if grave else MEDIA, w)
    # Qwen scrive cifre, non lettere simili: se il parser ha dovuto riparare qualcosa e' strano.
    # Per il titolo la "riparazione" e' solo il ripristino dell'accento: non conta.
    if getattr(parsed, "repaired", False) and not hasattr(parsed, "giorno"):
        e.abbassa(MEDIA, "lettura_riparata")
    if testo_libero is not None:
        from .parse import caratteri_sospetti
        if not testo_libero.strip():
            e.abbassa(BASSA, "testo_vuoto")
        elif caratteri_sospetti(testo_libero):
            e.abbassa(MEDIA, "caratteri_sospetti_nel_testo")
    return e


# Motivi "morbidi" (affidabilita' media). Tutti gli altri valgono come bassa.
_MOTIVI_MEDI = ("classe_fuori_elenco", "aula_fuori_elenco", "aula_nominale_sconosciuta",
                "marcatore_senza_nota", "lettura_riparata", "caratteri_sospetti_nel_testo",
                "ritaglio_riga_stimato", "classe_fuori_ordine_alfabetico",
                "orari_sovrapposti_aule_diverse", "riga_duplicata",
                "classe_in_entrata_e_uscita_stessa_ora",
                "cambio_aula_pomeridiano_con_no_lezioni_pomeridiane",
                "aula_composta", "classe_dedotta_da_riga_precedente")


def livello_da_motivi(motivi) -> str:
    """Affidabilita' risultante da una lista di motivi (per ricalcolarla dopo averne tolto uno)."""
    if not motivi:
        return ALTA
    return MEDIA if all(m in _MOTIVI_MEDI for m in motivi) else BASSA
