"""
Parsing deterministico del testo trascritto da Qwen3-VL.

Il modello trascrive soltanto. Qui il testo viene convertito in campi strutturati
e controllato con regole rigide.

Ogni funzione parse_* restituisce un oggetto con:
  .key()      -> tupla dei campi critici (per confronti e test)
  .fatal      -> True se il testo non e' interpretabile
  .problems   -> problemi "duri": il dato non puo' essere accettato cosi' com'e'
  .warnings   -> anomalie "morbide" (es. classe fuori elenco): validazione.py le
                 traduce in affidabilita' media (o bassa per quelle gravi)
"""
import difflib
import re
from dataclasses import dataclass, field
from typing import Optional

from .config import core_aula

# ---------------------------------------------------------------------------
# Normalizzazione
# ---------------------------------------------------------------------------
_REPL = {
    "-": "-", "—": "-", "-": "-", "-": "-", "―": "-", "~": "-",
    "º": "°", "˚": "°", "⁰": "°",       # º ˚ ⁰ -> °
    "'": "'", "‘": "'", "`": "'", "´": "'",
    ":": ":", "+": "+", "": "", "﻿": "", " ": " ",
}


def norm(s: str) -> str:
    """Maiuscolo, trattini e apici unificati, spazi compattati."""
    if s is None:
        return ""
    for a, b in _REPL.items():
        s = s.replace(a, b)
    s = s.upper()
    s = re.sub(r"[ \t\r\f\v]+", " ", s)
    return s.strip()


def alnum(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", norm(s))


# ---------------------------------------------------------------------------
# Orari
# ---------------------------------------------------------------------------
_DIGITLIKE = {"O": "0", "I": "1", "L": "1", "S": "5", "|": "1"}
_TIME_RE = re.compile(
    r"(?<![0-9A-Z])([0-2OILS|]?[0-9OILS|])\s*[.:,;]\s*([0-5OILS|][0-9OILS|])(?![0-9])"
)


def _fix_digits(t: str):
    changed = False
    out = []
    for ch in t:
        if ch in _DIGITLIKE:
            out.append(_DIGITLIKE[ch])
            changed = True
        else:
            out.append(ch)
    return "".join(out), changed


def canon_time(h: str, m: str):
    """('9','50') -> ('09:50', riparato?) oppure (None, riparato) se non valido."""
    h2, c1 = _fix_digits(h)
    m2, c2 = _fix_digits(m)
    try:
        hh, mm = int(h2), int(m2)
    except ValueError:
        return None, c1 or c2
    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        return None, c1 or c2
    return f"{hh:02d}:{mm:02d}", c1 or c2


_TIME_STRICT = re.compile(r"(?<![0-9A-Z])([0-2]?[0-9])\s*[.:,;]\s*([0-5][0-9])(?![0-9])")
_COMPACT_RE = re.compile(r"(?<![0-9A-Z])([0-2][0-9OILS])([0-5][0-9OILS])(?![0-9])")


def find_times(text: str):
    """Tutti gli orari trovati: lista di (orario 'HH:MM'|None, riparato, start, end).
    Prima cerca orari con soli numeri; poi la forma compatta '1145' (separatore perso
    dall'OCR); solo se ne mancano, ammette lettere simili a cifre (O, I, L, S)."""
    t = norm(text)
    out = []

    def libero(m):
        return not any(a < m.end() and m.start() < b for _, _, a, b in out)

    for m in _TIME_STRICT.finditer(t):
        tt, rep = canon_time(m.group(1), m.group(2))
        out.append((tt, rep, m.start(), m.end()))
    for m in _COMPACT_RE.finditer(t):
        if libero(m):
            tt, _ = canon_time(m.group(1), m.group(2))
            if tt:
                out.append((tt, True, m.start(), m.end()))
    if len(out) < 2:
        for m in _TIME_RE.finditer(t):
            if libero(m):
                tt, rep = canon_time(m.group(1), m.group(2))
                out.append((tt, True, m.start(), m.end()))
    out.sort(key=lambda x: x[2])
    return out


def _min(t: str) -> int:
    return int(t[:2]) * 60 + int(t[3:])


# ---------------------------------------------------------------------------
# Classi
# ---------------------------------------------------------------------------
CLASS_RE = re.compile(r"^([1-5])([A-Z]{1,3}\d?)(?:/([A-Z]))?$")
_MARKERS = "*°"


@dataclass
class ClassTok:
    classe: Optional[str]
    marker: str = ""
    repaired: bool = False
    valid: bool = True


def canon_class(s: str) -> ClassTok:
    """'4 J*' -> ClassTok('4J','*'). Se non valida: valid=False."""
    s = norm(s)
    s = re.sub(r"\s+", "", s)
    marker = ""
    m = re.search(r"([*°]+)$", s)
    if m:
        marker = m.group(1)
        s = s[: m.start()]
    s = s.strip(":;.,-")
    repaired = False
    if s and s[0] in "IL|":              # '1' letto come I / L / |
        s = "1" + s[1:]
        repaired = True
    if not CLASS_RE.match(s):
        # confusioni tipiche: 'I'->'1' e 'O'->'0' nella parte di lettere
        alt = s[:1] + s[1:].replace("1", "I").replace("0", "O") if s else s
        alt = re.sub(r"(?<=[A-Z])I(?=\d$)", "I", alt)
        if alt != s and CLASS_RE.match(alt):
            return ClassTok(alt, marker, True, True)
        return ClassTok(s or None, marker, repaired, False)
    return ClassTok(s, marker, repaired, True)


# ---------------------------------------------------------------------------
# Aule
# ---------------------------------------------------------------------------
_CODE_RE = re.compile(r"^[A-Z]\d{3}$")


def canon_aula(s: str, aule_nominali=()):
    """
    -> (aula canonica | None, riparata?, nominale?)
    Forme ammesse: 'AULA D205', 'LAB. B119', 'AULA 201', 'AULA MAGNA', 'TALVERA'
    """
    s = norm(s).strip(" :;,-")
    if not s:
        return None, False, False
    m = re.match(r"^(AULA|LAB\.?|LABORATORIO)\s*(.*)$", s)
    prefix, rest = ("", s)
    if m:
        prefix = "AULA" if m.group(1) == "AULA" else "LAB."
        rest = m.group(2)
    rest = rest.strip(" .:;,-")
    compact = rest.replace(" ", "")
    repaired = False
    # codice: una lettera + 3 cifre, oppure 3 cifre
    if re.match(r"^[A-Z][0-9OIL|]{3}$", compact) or re.match(r"^[0-9OIL|]{3}$", compact):
        fixed = compact
        head = ""
        if compact[0].isalpha() and not re.match(r"^[0-9OIL|]{3}$", compact):
            head, fixed = compact[0], compact[1:]
        else:
            head = ""
        fixed2, ch = _fix_digits(fixed)
        compact = head + fixed2
        repaired = ch
        nominale = False
        rest = compact
    else:
        nominale = True
        rest = re.sub(r"\s+", " ", rest)
    if not rest:
        return None, repaired, False
    return (f"{prefix} {rest}".strip() if prefix else rest), repaired, nominale


# ---------------------------------------------------------------------------
# RIGA "CAMBIO AULA"
# ---------------------------------------------------------------------------
@dataclass
class RowRead:
    aule: list = field(default_factory=list)   # una o piu' aule (aula composta: 'B309+LAB.A306', 'D204/5')
    raw: str = ""
    is_header: bool = False
    classe: Optional[str] = None
    marker: str = ""
    da: Optional[str] = None
    a: Optional[str] = None
    aula: Optional[str] = None
    repaired: bool = False
    fatal: bool = False
    problems: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def key(self):
        if self.is_header:
            return ("HEADER",)
        return (self.classe, self.da, self.a, self.aula)

    def short(self):
        if self.is_header:
            return "[intestazione]"
        c = (self.classe or "?") + self.marker
        return f"{c} : {self.da} - {self.a}  {self.aula}"


_JUNK = re.compile(r"[|\[\]{}!\u00a6_]")


_CLASSE_I_RE = re.compile(
    r"^\s*([1-5])1\s*:\s*(?=\d{1,2}\s*[.:]\s*[0-5]\d\s*-\s*\d{1,2}\s*[.:]\s*[0-5]\d)")


def parse_row(text: str, cfg: dict) -> RowRead:
    r = RowRead(raw=text)
    t = norm(_JUNK.sub(" ", text or ""))
    if re.search(r"CAMBIO", t) or difflib.SequenceMatcher(None, alnum(t), "CAMBIOAULA").ratio() > 0.75:
        if not find_times(t):
            r.is_header = True
            return r
    # Qwen 2B legge spesso la lettera I come cifra 1 ("1 I : 09.50 - 10.40" -> "11:09.50 - 10.40"):
    # "N1:" seguito da DUE orari completi e' una classe NI, non un orario (11:09 non esiste in griglia).
    m = _CLASSE_I_RE.match(t)
    if m:
        t = f"{m.group(1)}I : {t[m.end():].strip()}"
        r.repaired = True
    times = find_times(t)
    if len(times) < 2:
        r.fatal = True
        r.problems.append("orari_non_trovati")
        return r
    (t1, rep1, s1, e1), (t2, rep2, s2, e2) = times[0], times[1]
    r.repaired = r.repaired or rep1 or rep2
    if t1 is None or t2 is None:
        r.fatal = True
        r.problems.append("orario_non_valido")
        return r
    r.da, r.a = t1, t2
    if _min(t1) >= _min(t2):
        r.problems.append("orario_inizio_non_precede_fine")

    # classe = testo prima del primo orario
    cls_txt = t[:s1].strip(" :;.,-")
    if not cls_txt:
        r.classe = None
        r.problems.append("classe_assente")
    else:
        ct = canon_class(cls_txt)
        r.marker = ct.marker
        r.repaired = r.repaired or ct.repaired
        if ct.valid:
            r.classe = ct.classe
        else:
            r.classe = ct.classe
            r.problems.append("classe_non_valida")
    # aula = testo dopo il secondo orario
    aula, rep, nominale = canon_aula(t[e2:], cfg.get("aule_nominali", ()))
    r.repaired = r.repaired or rep
    r.aula = aula
    if aula is None:
        r.problems.append("aula_assente")
    else:
        _check_aula(r, aula, nominale, cfg)
    _check_orari_noti(r, cfg)
    _check_classe_valida(r, cfg)
    return r


def classe_valida(c: str, valide) -> bool:
    """Nell'elenco? Accetta anche sotto-gruppi con cifra finale (1MAQ1 -> 1MAQ)
    e classi articolate (3C/T -> 3C e 3T; 5G/N -> 5G e 5N)."""
    if c in valide:
        return True
    if c and c[-1].isdigit() and c[:-1] in valide:
        return True
    if "/" in c:
        base, alt = c.split("/", 1)
        return classe_valida(base, valide) and classe_valida(base[0] + alt, valide)
    return False


def split_aule(aula):
    """'AULA B309+LAB. A306' -> ['AULA B309', 'LAB. A306'];  'AULA D204/5' -> ['AULA D204', 'AULA D205'];
    'LAB. B120/1' -> ['LAB. B120', 'LAB. B121']. Aula semplice -> [aula]."""
    out = []
    for parte in re.split(r"\s*\+\s*", aula or ""):
        parte = re.sub(r"^LAB\.?\s*", "LAB. ", re.sub(r"^AULA\s*", "AULA ", parte.strip()))
        m = re.match(r"^((?:AULA|LAB\.) )?([A-Z]?\d{2,3})\s*/\s*(\d{1,3})$", parte)
        if m:
            pre, a, b = m.group(1) or "", m.group(2), m.group(3)
            seconda = a[:len(a) - len(b)] + b if len(b) < len(a) else b
            out += [pre + a, pre + seconda]
        elif parte:
            out.append(parte)
    return out


def _check_aula(r, aula, nominale, cfg):
    parti = split_aule(aula)
    if len(parti) > 1:
        # aula composta: ogni parte deve essere un'aula nota; e' comunque un formato raro -> avviso
        r.aule = parti
        r.warnings.append("aula_composta")
        valide = cfg.get("_aule_core")
        if valide and any(core_aula(x) not in valide for x in parti):
            r.warnings.append("aula_fuori_elenco")
        return
    r.aule = [aula]
    core = aula.split(" ", 1)[1] if aula.split(" ", 1)[0] in ("AULA", "LAB.") and " " in aula else aula
    valide = cfg.get("_aule_core")
    if valide:
        if core not in valide:
            r.warnings.append("aula_fuori_elenco")
        # il formato va comunque rispettato
        if not nominale and not (_CODE_RE.match(core) or re.match(r"^\d{3}$", core)):
            r.problems.append("aula_formato_non_valido")
        return
    if nominale:
        noti = [n.upper() for n in cfg.get("aule_nominali", [])]
        if core not in noti:
            r.warnings.append("aula_nominale_sconosciuta")
    elif not (_CODE_RE.match(core) or re.match(r"^\d{3}$", core)):
        r.problems.append("aula_formato_non_valido")


def _check_orari_noti(r, cfg):
    noti = set(cfg.get("orari_noti") or [])
    if noti:
        for t in (r.da, r.a):
            if t and t not in noti:
                r.warnings.append(f"orario_fuori_elenco:{t}")


def _check_classe_valida(r, cfg):
    valide = cfg.get("classi_valide")
    if valide and r.classe and not classe_valida(r.classe, valide):
        r.warnings.append("classe_fuori_elenco")


# ---------------------------------------------------------------------------
# TITOLO
# ---------------------------------------------------------------------------
GIORNI = ["LUNEDÌ", "MARTEDÌ", "MERCOLEDÌ", "GIOVEDÌ", "VENERDÌ", "SABATO", "DOMENICA"]
MESI = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", "LUGLIO",
        "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]


@dataclass
class TitleRead:
    raw: str = ""
    giorno: Optional[str] = None
    numero: Optional[int] = None
    mese: Optional[str] = None
    fatal: bool = False
    problems: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    repaired: bool = False
    anno: Optional[int] = None
    iso: Optional[str] = None          # 'YYYY-MM-DD' se il giorno della settimana torna

    def key(self):
        return (self.giorno, self.numero, self.mese)

    def short(self):
        return f"{self.giorno} {self.numero} {self.mese}"


def _closest(word, vocab, cutoff=0.8):
    w = word.replace("Ì", "I").replace("I'", "I")
    best, score = None, 0.0
    for v in vocab:
        s = difflib.SequenceMatcher(None, w, v.replace("Ì", "I")).ratio()
        if s > score:
            best, score = v, s
    return (best, score) if score >= cutoff else (None, score)


def parse_title(text: str, cfg=None) -> TitleRead:
    r = TitleRead(raw=text)
    t = norm(text)
    words = re.findall(r"[A-ZÀ-Ü']+|\d+", t)
    k = next((i for i, w in enumerate(words) if w.isdigit()), None)
    if k is None or k == 0 or k == len(words) - 1:
        r.fatal = True
        r.problems.append("titolo_non_interpretabile")
        return r
    nums = [words[k]]
    giorno_txt = "".join(w for w in words[:k] if not w.isdigit())
    mese_txt = "".join(w for w in words[k + 1:] if not w.isdigit())
    g, sg = _closest(giorno_txt, GIORNI)
    m, sm = _closest(mese_txt, MESI)
    if not g or not m:
        r.fatal = True
        r.problems.append("giorno_o_mese_non_riconosciuto")
        return r
    if norm(giorno_txt).replace("Ì", "I") != g.replace("Ì", "I") or norm(mese_txt) != m:
        r.repaired = True
    r.giorno, r.mese = g, m
    n = int(nums[0])
    if not (1 <= n <= 31):
        r.fatal = True
        r.problems.append("giorno_numero_non_valido")
        return r
    r.numero = n
    import datetime
    oggi = datetime.date.today()
    # Anno: quello configurato, altrimenti la data piu' vicina a oggi. Una finestra piu'
    # larga renderebbe il controllo inutile (13 MAGGIO e' martedi' nel 2025, mercoledi'
    # nel 2026, giovedi' nel 2027: ogni giorno della settimana sembrerebbe valido).
    anni = [int(cfg["anno"])] if cfg and cfg.get("anno") else [oggi.year - 1, oggi.year, oggi.year + 1]
    date = []
    for anno in anni:
        try:
            date.append(datetime.date(anno, MESI.index(m) + 1, n))
        except ValueError:
            continue
    if date:
        d = min(date, key=lambda x: abs((x - oggi).days))
        if GIORNI[d.weekday()] == g:
            r.anno, r.iso = d.year, d.isoformat()
        else:
            altre = [x for x in date if GIORNI[x.weekday()] == g]
            if altre and not (cfg and cfg.get("anno")):
                # la data torna con un altro anno (immagine d'archivio?): usabile ma da controllare
                d = min(altre, key=lambda x: abs((x - oggi).days))
                r.anno, r.iso = d.year, d.isoformat()
                r.warnings.append(f"data_di_altro_anno:{d.year}")
            else:
                # giorno della settimana e data non possono coesistere: uno dei due e' letto male
                r.problems.append("giorno_settimana_incoerente_con_data")
    else:
        r.problems.append("data_non_esistente")
    return r


# ---------------------------------------------------------------------------
# RIQUADRI: ENTRA / ESCE / NO LEZ. POM. / INFO
# ---------------------------------------------------------------------------
@dataclass
class BoxRead:
    raw_lines: list = field(default_factory=list)
    kind: str = "info"                 # entra | esce | nolez | info
    ora: Optional[str] = None
    classi: list = field(default_factory=list)      # lista di ClassTok
    note_lines: list = field(default_factory=list)
    testo: str = ""                    # per info
    repaired: bool = False
    fatal: bool = False
    problems: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def key(self):
        if self.kind == "info":
            return ("info", alnum(self.testo))
        return (self.kind, self.ora, tuple(c.classe for c in self.classi))

    def short(self):
        if self.kind == "info":
            return self.testo.replace("\n", " / ")
        cl = " + ".join((c.classe or "?") + c.marker for c in self.classi)
        n = (" | " + " / ".join(self.note_lines)) if self.note_lines else ""
        return f"{self.kind} {self.ora or ''}: {cl}{n}"


_HEADER_RE = re.compile(r"^([A-Z']{2,8})\s*ALLE\s*([0-2OILS|]?[0-9OILS|])\s*[.:,;]\s*([0-5OILS|][0-9OILS|])")
_NOLEZ_RE = re.compile(r"^N[O0]\s*L[EF]Z")


def _kind_from_word(word: str):
    cand = {"ENTRA": "entra", "ESCE": "esce"}
    best, score = None, 0.0
    for k in cand:
        s = difflib.SequenceMatcher(None, word, k).ratio()
        if s > score:
            best, score = k, s
    return cand[best] if score >= 0.6 else None


def _split_class_tokens(line: str):
    """Spezza 'A + B + C' sui '+'. None se la riga non e' una lista di classi."""
    parts = [p.strip() for p in re.split(r"\+", line) if p.strip()]
    if not parts:
        return None
    toks = [canon_class(p) for p in parts]
    return toks


def _looks_like_note(line: str) -> bool:
    return line[:1] in ("*", "°") or bool(re.match(r"^[*°]", line))


def parse_box(lines, color_hint: str, cfg: dict) -> BoxRead:
    """
    lines: righe di testo trascritte (intestazione, classi, note).
    color_hint: 'giallo' | 'chiaro' | 'bianco' | 'info' (dal colore del riquadro)
    """
    r = BoxRead(raw_lines=list(lines))
    ls = [norm(x) for x in lines if norm(x)]
    if not ls:
        r.fatal = True
        r.problems.append("riquadro_vuoto")
        return r

    # --- intestazione ENTRA/ESCE ALLE hh.mm oppure NO LEZ. POM.
    first = ls[0].replace(" ", "")
    header_kind, ora = None, None
    mh = _HEADER_RE.match(re.sub(r"\s+", " ", ls[0]))
    if mh is None:
        mh = _HEADER_RE.match(re.sub(r"\s+", "", ls[0]).replace("ALLE", " ALLE "))
    if color_hint != "info" and mh:
        header_kind = _kind_from_word(mh.group(1))
        ora, rep = canon_time(mh.group(2), mh.group(3))
        r.repaired = r.repaired or rep
        if header_kind is None:
            r.fatal = True
            r.problems.append("intestazione_non_riconosciuta")
            r.kind = "info"
            return r
        if ora is None:
            r.fatal = True
            r.problems.append("orario_intestazione_non_valido")
            return r
    elif color_hint != "info" and _NOLEZ_RE.match(first):
        header_kind = "nolez"

    if header_kind is None:
        # riquadro informativo (FSL, viaggi, docenti assenti, ...)
        r.kind = "info"
        r.testo = "\n".join(lines_clean(lines))
        if color_hint == "giallo":
            r.problems.append("riquadro_giallo_senza_intestazione")
        return r

    r.kind, r.ora = header_kind, ora
    # incrocio con il colore: giallo = ENTRA, chiaro = ESCE, bianco = NO LEZ
    atteso = {"giallo": "entra", "chiaro": "esce", "bianco": "nolez"}.get(color_hint)
    if atteso and atteso != header_kind:
        r.problems.append(f"colore_{color_hint}_incoerente_con_{header_kind}")

    # --- righe di classi, poi note
    in_notes = False
    for ln in ls[1:]:
        if not in_notes and not _looks_like_note(ln):
            toks = _split_class_tokens(ln)
            if toks is not None and all(t.valid for t in toks):
                r.classi.extend(toks)
                continue
            if toks is not None and any(t.valid for t in toks) and "+" in ln:
                r.classi.extend(toks)
                r.problems.append("classe_non_valida")
                continue
            in_notes = True
        r.note_lines.append(ln)
    # le note si riprendono dal testo originale (maiuscole/minuscole)
    orig = [x.strip() for x in lines if x.strip()]
    r.note_lines = orig[len(orig) - len(r.note_lines):] if r.note_lines else []

    if not r.classi:
        r.problems.append("nessuna_classe")
    for c in r.classi:
        if c.repaired:
            r.repaired = True
        if not c.valid:
            r.problems.append("classe_non_valida")
    classi = [c.classe for c in r.classi if c.classe]
    if len(set(classi)) != len(classi):
        r.problems.append("classe_duplicata")
    valide = cfg.get("classi_valide")
    if valide and any(not classe_valida(c, valide) for c in classi):
        r.warnings.append("classe_fuori_elenco")
    noti = set(cfg.get("orari_noti") or [])
    if noti and r.ora and r.kind in ("entra", "esce") and r.ora not in noti:
        r.warnings.append(f"orario_fuori_elenco:{r.ora}")
    _check_note(r, cfg)
    # i marcatori (*, °) devono avere una nota corrispondente
    marks = {c.marker[:1] for c in r.classi if c.marker}
    note_marks = {n.strip()[:1] for n in r.note_lines}
    if marks - note_marks:
        r.warnings.append("marcatore_senza_nota")
    return r


_NOTA_ORE_RE = re.compile(r"\b(POSTICIPA|ANTICIPA)\s+(?:A\s+)?(\d)\s*°?\s*AL?\s*(\d)")
_NOTA_AULA_RE = re.compile(r"\(\s*([A-Z]?\d{3})\s*\)")


def _check_note(r, cfg):
    """Note tipo '* ROSSI posticipa 1° a 3° (B104)': le ore devono avere senso
    (posticipare = ora piu' tardi, anticipare = piu' presto) e l'aula deve esistere.
    """
    valide = cfg.get("_aule_core")
    for ln in r.note_lines:
        t = norm(ln)
        m = _NOTA_ORE_RE.search(t)
        if m:
            da, a = int(m.group(2)), int(m.group(3))
            if not (1 <= da <= 9 and 1 <= a <= 9) or da == a:
                r.problems.append("nota_ora_non_valida")
            elif (m.group(1) == "POSTICIPA") != (a > da):
                r.problems.append("nota_posticipa_anticipa_incoerente")
        for code in _NOTA_AULA_RE.findall(t):
            if valide and code not in valide:
                r.warnings.append("aula_fuori_elenco")


# caratteri ammessi nel testo libero: Qwen 4B trasformava '*' in '★' e inventava markdown
_TESTO_OK = re.compile(r"^[A-Za-zÀ-ÿ0-9\s.,:;'\"()\[\]/+\-*°º^¹²³&%!?#@_=<>]*$")


def caratteri_sospetti(testo: str) -> bool:
    return not _TESTO_OK.match(testo or "")


def lines_clean(lines):
    return [re.sub(r"[ \t]+", " ", x).strip() for x in lines if x and x.strip()]


# similarita' tra due letture di riquadri informativi / note ------------------
def digit_signature(s: str) -> str:
    return "".join(re.findall(r"\d", s))


def text_same(a: str, b: str, min_ratio=0.93) -> bool:
    """Due testi liberi sono 'uguali' se le cifre coincidono e il testo e' molto simile."""
    if digit_signature(a) != digit_signature(b):
        return False
    return difflib.SequenceMatcher(None, alnum(a), alnum(b)).ratio() >= min_ratio


def box_same(a: BoxRead, b: BoxRead) -> bool:
    if a.kind != b.kind:
        return False
    if a.kind == "info":
        return text_same(a.testo, b.testo)
    if a.key() != b.key():
        return False
    # note: stesse cifre/codici e testo simile
    na, nb = " ".join(a.note_lines), " ".join(b.note_lines)
    if (na or nb) and not text_same(na, nb, 0.85):
        return False
    return True
