#!/usr/bin/env python3
"""
Legge ORARIO_CLASSI.pdf ed produce direttamente:
  orario_classi.json   -> dataset completo { "1A": {...}, "1B": {...}, ... }
  classi_index.json    -> lista leggera di tutte le classi
  classi/<ID>.json     -> file individuale per classe

Dipendenza: pip install pdfplumber
"""

import pdfplumber
import json
import re
import os
import copy
from pathlib import Path
from collections import defaultdict

HERE       = Path(__file__).parent
PDF_PATH   = HERE / "ORARIO_CLASSI.pdf"
API_PATH   = HERE / "orario_classi.json"
INDEX_PATH = HERE / "classi_index.json"
CLASSI_DIR = HERE / "classi"

# ─── Costanti estrazione PDF ──────────────────────────────────────────────────

TIME_LABELS  = ["8:10", "9:00", "9:50", "10:40", "11:45", "12:35", "13:25",
                "14:30", "15:20", "16:10", "17:10"]
TIME_MARKERS = ["8h10", "9h00", "9h50", "10h40", "11h45", "12h35", "13h25",
                "14h30", "15h20", "16h10", "17h10"]

DAY_LABELS   = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato"]
DAY_PREFIXES = ["lune", "mart", "merc", "giov", "vene", "saba"]

SKIP_WORDS   = {"©", "Index", "Education", "2025", "ORARIO", "VALIDO",
                "DA", "LUN.", "NOVEMBRE", "24"}

# ─── Costanti ristrutturazione ────────────────────────────────────────────────

TIME_LABELS_ORDERED = [
    "08:10", "09:00", "09:50", "10:40",
    "11:45", "12:35", "13:25",
    "14:30", "15:20", "16:10", "17:10"
]

TIME_NORMALIZE = {
    "8:10": "08:10", "9:00": "09:00", "9:50": "09:50",
    "10:40": "10:40", "11:45": "11:45", "12:35": "12:35", "13:25": "13:25",
    "14:30": "14:30", "15:20": "15:20", "16:10": "16:10", "17:10": "17:10",
}

# Coppie consecutive valide per propagazione materie a 2 ore.
# Non si propaga oltre il break pranzo (13:25 -> 14:30).
CONSECUTIVE_PAIRS = {
    ("08:10", "09:00"), ("09:00", "09:50"), ("09:50", "10:40"),
    ("10:40", "11:45"), ("11:45", "12:35"), ("12:35", "13:25"),
    ("14:30", "15:20"), ("15:20", "16:10"), ("16:10", "17:10"),
}

# Slot che nel PDF reale non vengono mai usati: non propagare mai verso di essi.
NEVER_USED_SLOTS = {"17:10"}

DAYS_ORDERED = [
    ("lunedi",    "lunedì"),
    ("martedi",   "martedì"),
    ("mercoledi", "mercoledì"),
    ("giovedi",   "giovedì"),
    ("venerdi",   "venerdì"),
    ("sabato",    "sabato"),
]

AFTERNOON_SLOTS = {"14:30", "15:20", "16:10", "17:10"}

MATERIA_SHORT = {
    "Lingua e letteratura italiana":    "Italiano",
    "Lingua inglese":                   "Inglese",
    "Tedesco II Lingua":                "Tedesco",
    "Storia":                           "Storia",
    "Storia e geografia":               "Storia e Geografia",
    "Matematica":                       "Matematica",
    "Fisica":                           "Fisica",
    "Scienze integrate (Fisica)":       "Fisica",
    "Scienze integrate (Chimica)":      "Chimica",
    "Scienze integrate (Sci. e Bio)":   "Scienze e Biologia",
    "Scienze naturali":                 "Scienze Naturali",
    "Informatica":                      "Informatica",
    "Tecnologie informatiche":          "Tecnologie Informatiche",
    "Diritto ed economia":              "Diritto ed Economia",
    "Religione":                        "Religione",
    "Scienze motorie e sportive":       "Scienze Motorie",
    "Filosofia":                        "Filosofia",
    "Disegno e storia dell'arte":       "Disegno e Arte",
    "Tecno. e tecniche rappr. graf.":   "Tecn. e Tecniche Grafiche",
    "Meccanica, macchine e energia":    "Meccanica",
    "Sistemi ed automazione":           "Sistemi e Automazione",
    "Sistemi e reti":                   "Sistemi e Reti",
    "Sistemi automatici":               "Sistemi Automatici",
    "Tecnol. mec. di proc. e prod.":    "Tecn. Meccanica",
    "Tecnologie meccaniche ed appl.":   "Tecn. Meccanica",
    "Dis., progettaz. e org. ind.le":   "Disegno e Prog. Industriale",
    "Elettronica ed elettrotecnica":    "Elettronica",
    "Tec. e prog. sist. ele. e elee":   "Tec. Prog. Sistemi Elettr.",
    "Tec. e prog. sist. inf. e tel.":   "Tec. Prog. Sistemi Inf.",
    "Telecomunicazioni":                "Telecomunicazioni",
    "Complementi di matematica":        "Complementi di Matematica",
    "Chimica org. e biochimica":        "Chimica Organica",
    "Chimica analitica e strum.":       "Chimica Analitica",
    "Bio., micro. e tec. contr.amb.":   "Biologia Ambientale",
    "Bio., micro. e tec. contr.san.":   "Biologia Sanitaria",
    "Igiene, anat., fisiol., patol.":   "Igiene e Anatomia",
    "Anatomia, fisiologia, igiene":     "Anatomia e Fisiologia",
    "Fisica ambientale":                "Fisica Ambientale",
    "Scienze e tecnologie applicate":   "Scienze e Tecn. Applicate",
    "Lab. tecn. e esercitazioni":       "Lab. Tecn. ed Esercitazioni",
    "Tecnol. tecni. di inst. e man.":   "Tecn. di Installazione",
    "Tecn. elettri-elettro. e appl.":   "Tecn. Elettr. e Elettrotecnica",
    "Rappr. e modell. odontotecnica":   "Rappresentazione Odontotecnica",
    "Eser. di lab. odontotecnico":      "Lab. Odontotecnico",
    "Scienze dei mat. dent. e lab.":    "Scienze dei Materiali Dentali",
    "Gnatologia":                       "Gnatologia",
    "Legislazione sanitaria":           "Legislazione Sanitaria",
    "Dir. prat.com., leg. soc./san.":   "Diritto Sanitario",
    "Gest. progetto, org. di impresa":  "Gestione Progetto",
}


# ═══════════════════════════════════════════════════════════════════════════════
# FASE 1 — Estrazione dal PDF
# ═══════════════════════════════════════════════════════════════════════════════

def is_fully_doubled(text):
    if len(text) < 2 or len(text) % 2 != 0:
        return False
    return all(text[i] == text[i + 1] for i in range(0, len(text), 2))

def dedupe(text):
    return text[::2] if is_fully_doubled(text) else text

def is_room_word(word):
    return re.match(r'^(AULA|LAB\.|PAL\.|Aula|LAB$)', word) is not None

def has_uppercase_surname(words):
    skip = {'AULA', 'LAB.', 'PAL.', 'LAB', 'INF', 'FIS', 'CHI', 'ELE', 'MEC',
            'BIO', 'SCI', 'CAD', 'DIS', 'ODO', 'Q1', 'Q2', 'L.E.AP', 'M.U.',
            'M.M.E.', 'CONG.', 'SALD.', 'SIST.', 'AUT.', 'PNRR', 'AMB.', 'R.'}
    for w in words:
        if w.isupper() and len(w) > 2 and w not in skip \
                and not w.startswith('(') and not re.match(r'^[A-Z]\d', w):
            return True
    return False

def parse_cell(entries):
    if not entries:
        return None

    lines = []
    current_line = []
    current_y = None
    for (wy, wx, wt) in sorted(entries, key=lambda e: (e[0], e[1])):
        if wt in SKIP_WORDS or wt.startswith('©') \
                or (wt.isdigit() and len(wt) == 4 and int(wt) > 2000):
            continue
        if current_y is None or abs(wy - current_y) <= 4:
            current_line.append((wx, wt))
            current_y = wy if current_y is None else (current_y + wy) / 2
        else:
            if current_line:
                lines.append([wt for _, wt in sorted(current_line)])
            current_line = [(wx, wt)]
            current_y = wy
    if current_line:
        lines.append([wt for _, wt in sorted(current_line)])

    subject_lines, teacher_lines, room_lines = [], [], []
    for line in lines:
        if not line or line in (['Q1'], ['Q2']):
            continue
        if is_room_word(line[0]):
            room_lines.append(" ".join(line))
        elif has_uppercase_surname(line):
            teacher_lines.append(" ".join(line))
        else:
            subject_lines.append(" ".join(line))

    materia = " ".join(subject_lines).strip() or None
    aula    = " ".join(room_lines).strip() or None

    docenti = []
    for tl in teacher_lines:
        for part in [p.strip() for p in tl.split(",") if p.strip()]:
            tokens = part.split()
            subteachers, current = [], []
            for i, tok in enumerate(tokens):
                if i == 0:
                    current.append(tok)
                elif tok.isupper() and len(tok) > 2 and tok not in SKIP_WORDS:
                    if current and not current[-1].isupper():
                        subteachers.append(" ".join(current))
                        current = [tok]
                    else:
                        current.append(tok)
                else:
                    current.append(tok)
            if current:
                subteachers.append(" ".join(current))
            docenti.extend([t.strip() for t in subteachers if t.strip()])

    if not materia and not docenti and not aula:
        return None
    result = {"materia": materia, "docenti": docenti}
    if aula:
        result["aula"] = aula
    return result

def extract_page(page):
    words = page.extract_words(x_tolerance=3, y_tolerance=3)
    if not words:
        return None

    header_words = [(dedupe(w['text']), w['x0'], w['top']) for w in words if w['top'] < 68]
    texts = [t for t, x, y in header_words]

    classe, coordinatore = None, None
    try:
        ci = texts.index("CLASSE")
        parts = []
        for t in texts[ci + 1:]:
            if t in ("Docente", "coordinatore", ":") or t.lower().startswith(DAY_PREFIXES[0][:4]):
                break
            parts.append(t)
        classe = " ".join(parts).strip()
    except ValueError:
        pass

    try:
        col_i = texts.index(":")
        coordinatore = " ".join(texts[col_i + 1:]).strip()
        for day in DAY_LABELS:
            coordinatore = coordinatore.replace(day, "").strip()
    except ValueError:
        pass

    if not classe:
        return None

    # Colonne giorni
    day_headers = []
    for w in words:
        if 60 <= w['top'] <= 68:
            txt = w['text'].lower().replace("ì", "i").replace("à", "a")
            for i, pref in enumerate(DAY_PREFIXES):
                if txt.startswith(pref):
                    day_headers.append((DAY_LABELS[i], (w['x0'] + w['x1']) / 2))
                    break
    day_headers.sort(key=lambda x: x[1])

    col_bounds = []
    for i, (dname, center) in enumerate(day_headers):
        prev_c = day_headers[i - 1][1] if i > 0 else 0
        next_c = day_headers[i + 1][1] if i < len(day_headers) - 1 else page.width
        col_bounds.append((dname, (prev_c + center) / 2, (center + next_c) / 2))

    # Righe orari
    slot_markers = []
    for w in words:
        if w['text'] in TIME_MARKERS:
            slot_markers.append((TIME_LABELS[TIME_MARKERS.index(w['text'])], w['top']))
    slot_markers.sort(key=lambda x: x[1])

    slot_bounds = []
    for i, (label, ytop) in enumerate(slot_markers):
        ybot = slot_markers[i + 1][1] if i + 1 < len(slot_markers) else page.height
        slot_bounds.append((label, ytop, ybot))

    if not slot_bounds:
        return None

    # Assegna parole alle celle
    first_slot_y = slot_bounds[0][1]
    cell_dict = defaultdict(list)
    for w in words:
        wx, wy, wt = w['x0'], w['top'], w['text']
        if wy < first_slot_y or wt in TIME_MARKERS or wt in SKIP_WORDS or wt.startswith('©'):
            continue
        day_name = next((d for d, cx0, cx1 in col_bounds if cx0 <= wx < cx1), None)
        slot_label = next((l for l, sy, ey in slot_bounds if sy <= wy < ey), None)
        if day_name and slot_label:
            cell_dict[(day_name, slot_label)].append((wy, wx, wt))

    # Costruisce schedule
    schedule = {day: {} for day in DAY_LABELS}
    for day in DAY_LABELS:
        for slot_label, _, _ in slot_bounds:
            schedule[day][slot_label] = parse_cell(cell_dict.get((day, slot_label), []))

    # Merge celle orfane (solo aula/docente senza materia) nello slot precedente
    for day in DAY_LABELS:
        slot_seq = [l for l, _, _ in slot_bounds]
        for i in range(1, len(slot_seq)):
            cur = slot_seq[i]
            entry = schedule[day].get(cur)
            if entry is None:
                continue
            is_orphan = not entry.get("materia") and (
                not entry.get("docenti") or entry.get("aula")
            )
            if is_orphan:
                for j in range(i - 1, -1, -1):
                    prev_entry = schedule[day].get(slot_seq[j])
                    if prev_entry is not None:
                        if not prev_entry.get("aula") and entry.get("aula"):
                            prev_entry["aula"] = entry["aula"]
                        for d in entry.get("docenti", []):
                            if d not in prev_entry.get("docenti", []):
                                prev_entry.setdefault("docenti", []).append(d)
                        schedule[day][cur] = None
                        break

    has_afternoon = any(
        schedule[day].get(slot) is not None
        for day in DAY_LABELS for slot in AFTERNOON_SLOTS
    )

    result = {"classe": classe, "docente_coordinatore": coordinatore,
              "pomeriggio": has_afternoon, "orario": {}}
    for day in DAY_LABELS:
        result["orario"][day] = {}
        for slot_label, _, _ in slot_bounds:
            if slot_label in AFTERNOON_SLOTS and not has_afternoon:
                continue
            result["orario"][day][slot_label] = schedule[day].get(slot_label)
    return result

def extract_pdf(pdf_path):
    raw_classes = []
    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            try:
                data = extract_page(page)
                if data:
                    raw_classes.append(data)
                    print(f"  [{i+1:2d}/{total}] {data['classe']}")
                else:
                    print(f"  [{i+1:2d}/{total}] SKIP")
            except Exception as e:
                print(f"  [{i+1:2d}/{total}] ERRORE: {e}")
    return raw_classes


# ═══════════════════════════════════════════════════════════════════════════════
# FASE 2 — Ristrutturazione per API
# ═══════════════════════════════════════════════════════════════════════════════

def make_class_id(nome):
    nome = re.sub(r'<[^>]+>\s*', '', nome)
    return nome.replace(" ", "")

def normalize_ora(entry):
    if entry is None:
        return None
    materia_raw   = (entry.get("materia") or "").strip()
    materia_short = MATERIA_SHORT.get(materia_raw, materia_raw) if materia_raw else None
    docenti = [d.strip() for d in (entry.get("docenti") or []) if d.strip()]
    aula    = (entry.get("aula") or "").strip() or None
    if not materia_short and not docenti:
        return None
    result = {}
    if materia_short:
        result["materia"] = materia_short
    if materia_raw and materia_raw != materia_short:
        result["materia_completa"] = materia_raw
    if docenti:
        result["docenti"] = docenti
    if aula:
        result["aula"] = aula
    return result

def fill_consecutive_slots(slots_clean):
    """
    Propaga la materia dello slot precedente in quello successivo vuoto,
    ma SOLO dagli slot originali (non da slot già propagati) per evitare
    la cascata A→B→C. Inoltre non propaga mai verso slot mai usati (17:10).
    """
    original_slots = set(slots_clean.keys())
    for i in range(1, len(TIME_LABELS_ORDERED)):
        prev_slot = TIME_LABELS_ORDERED[i - 1]
        curr_slot = TIME_LABELS_ORDERED[i]
        if (prev_slot, curr_slot) not in CONSECUTIVE_PAIRS:
            continue
        if curr_slot in NEVER_USED_SLOTS:
            continue
        if curr_slot not in slots_clean and prev_slot in original_slots:
            slots_clean[curr_slot] = copy.deepcopy(slots_clean[prev_slot])
    return slots_clean

def build_class_object(raw):
    classe_nome    = raw["classe"].strip()
    classe_display = re.sub(r'<[^>]+>\s*', '', classe_nome).strip()
    classe_id      = make_class_id(classe_nome)

    orario_clean = {}
    for day_key, day_label in DAYS_ORDERED:
        raw_day = raw["orario"].get(day_label, {})
        if not raw_day:
            continue
        slots_clean = {}
        for raw_time, norm_time in TIME_NORMALIZE.items():
            ora = normalize_ora(raw_day.get(raw_time))
            if ora:
                slots_clean[norm_time] = ora
        slots_clean = fill_consecutive_slots(slots_clean)
        if slots_clean:
            # Ordina per orario crescente
            ordered = {t: slots_clean[t] for t in TIME_LABELS_ORDERED if t in slots_clean}
            orario_clean[day_key] = ordered

    has_afternoon = any(
        slot in day_slots
        for day_slots in orario_clean.values()
        for slot in AFTERNOON_SLOTS
    )
    day_order     = {k: i for i, (k, _) in enumerate(DAYS_ORDERED)}
    giorni_attivi = sorted(orario_clean.keys(), key=lambda d: day_order.get(d, 99))

    return {
        "id": classe_id,
        "nome": classe_display,
        "docente_coordinatore": (raw.get("docente_coordinatore") or "").strip(),
        "pomeriggio": has_afternoon,
        "giorni_attivi": giorni_attivi,
        "orario": orario_clean,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print(f"Lettura PDF: {PDF_PATH}\n")
    raw_classes = extract_pdf(PDF_PATH)
    print(f"\nEstrazione completata: {len(raw_classes)} classi\n")

    classes = [build_class_object(r) for r in raw_classes]
    os.makedirs(CLASSI_DIR, exist_ok=True)

    # orario_classi.json
    api_dict = {c["id"]: c for c in classes}
    with open(API_PATH, "w", encoding="utf-8") as f:
        json.dump(api_dict, f, ensure_ascii=False, indent=2)
    print(f"Scritto: {API_PATH}")

    # classi_index.json
    index = [
        {"id": c["id"], "nome": c["nome"],
         "docente_coordinatore": c["docente_coordinatore"],
         "pomeriggio": c["pomeriggio"], "giorni_attivi": c["giorni_attivi"]}
        for c in classes
    ]
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print(f"Scritto: {INDEX_PATH}")

    # classi/<ID>.json
    for c in classes:
        with open(CLASSI_DIR / f"{c['id']}.json", "w", encoding="utf-8") as f:
            json.dump(c, f, ensure_ascii=False, indent=2)
    print(f"Scritti: {len(classes)} file in {CLASSI_DIR}/")

    print(f"\nFatto. {len(classes)} classi elaborate.")

if __name__ == "__main__":
    main()
