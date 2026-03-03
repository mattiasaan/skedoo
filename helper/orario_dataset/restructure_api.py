import json
import re
import os

INPUT_PATH  = "/mnt/user-data/outputs/orario_classi.json"
OUTPUT_DIR  = "/mnt/user-data/outputs"
API_PATH    = os.path.join(OUTPUT_DIR, "orario_api.json")
INDEX_PATH  = os.path.join(OUTPUT_DIR, "classi_index.json")
CLASSI_DIR  = os.path.join(OUTPUT_DIR, "classi")

# Mapping normalizzazione

TIME_LABELS_ORDERED = [
    "08:10", "09:00", "09:50", "10:40",
    "11:45", "12:35", "13:25",
    "14:30", "15:20", "16:10", "17:10"
]

TIME_NORMALIZE = {
    "8:10":  "08:10",
    "9:00":  "09:00",
    "9:50":  "09:50",
    "10:40": "10:40",
    "11:45": "11:45",
    "12:35": "12:35",
    "13:25": "13:25",
    "14:30": "14:30",
    "15:20": "15:20",
    "16:10": "16:10",
    "17:10": "17:10",
}

# Giorni in ordine, con chiave normalizzata (senza accenti) e display label
DAYS_ORDERED = [
    ("lunedi",     "lunedì"),
    ("martedi",    "martedì"),
    ("mercoledi",  "mercoledì"),
    ("giovedi",    "giovedì"),
    ("venerdi",    "venerdì"),
    ("sabato",     "sabato"),
]

DAY_NORMALIZE = {
    "lunedì":    "lunedi",
    "martedì":   "martedi",
    "mercoledì": "mercoledi",
    "giovedì":   "giovedi",
    "venerdì":   "venerdi",
    "sabato":    "sabato",
}

AFTERNOON_SLOTS = {"14:30", "15:20", "16:10", "17:10"}

MATERIA_SHORT = {
    "Lingua e letteratura italiana":              "Italiano",
    "Lingua inglese":                             "Inglese",
    "Tedesco II Lingua":                          "Tedesco",
    "Storia":                                     "Storia",
    "Storia e geografia":                         "Storia e Geografia",
    "Matematica":                                 "Matematica",
    "Fisica":                                     "Fisica",
    "Scienze integrate (Fisica)":                 "Fisica",
    "Scienze integrate (Chimica)":                "Chimica",
    "Scienze integrate (Sci. e Bio)":             "Scienze e Biologia",
    "Scienze naturali":                           "Scienze Naturali",
    "Informatica":                                "Informatica",
    "Tecnologie informatiche":                    "Tecnologie Informatiche",
    "Diritto ed economia":                        "Diritto ed Economia",
    "Religione":                                  "Religione",
    "Scienze motorie e sportive":                 "Scienze Motorie",
    "Filosofia":                                  "Filosofia",
    "Disegno e storia dell'arte":                 "Disegno e Arte",
    "Tecno. e tecniche rappr. graf.":             "Tecn. e Tecniche Grafiche",
    "Meccanica, macchine e energia":              "Meccanica",
    "Sistemi ed automazione":                     "Sistemi e Automazione",
    "Sistemi e reti":                             "Sistemi e Reti",
    "Sistemi automatici":                         "Sistemi Automatici",
    "Tecnol. mec. di proc. e prod.":              "Tecn. Meccanica",
    "Tecnologie meccaniche ed appl.":             "Tecn. Meccanica",
    "Dis., progettaz. e org. ind.le":             "Disegno e Prog. Industriale",
    "Elettronica ed elettrotecnica":              "Elettronica",
    "Tec. e prog. sist. ele. e elee":             "Tec. Prog. Sistemi Elettr.",
    "Tec. e prog. sist. inf. e tel.":             "Tec. Prog. Sistemi Inf.",
    "Telecomunicazioni":                          "Telecomunicazioni",
    "Complementi di matematica":                  "Complementi di Matematica",
    "Chimica org. e biochimica":                  "Chimica Organica",
    "Chimica analitica e strum.":                 "Chimica Analitica",
    "Bio., micro. e tec. contr.amb.":             "Biologia Ambientale",
    "Bio., micro. e tec. contr.san.":             "Biologia Sanitaria",
    "Igiene, anat., fisiol., patol.":             "Igiene e Anatomia",
    "Anatomia, fisiologia, igiene":               "Anatomia e Fisiologia",
    "Fisica ambientale":                          "Fisica Ambientale",
    "Scienze e tecnologie applicate":             "Scienze e Tecn. Applicate",
    "Lab. tecn. e esercitazioni":                 "Lab. Tecn. ed Esercitazioni",
    "Tecnol. tecni. di inst. e man.":             "Tecn. di Installazione",
    "Tecn. elettri-elettro. e appl.":             "Tecn. Elettr. e Elettrotecnica",
    "Rappr. e modell. odontotecnica":             "Rappresentazione Odontotecnica",
    "Eser. di lab. odontotecnico":                "Lab. Odontotecnico",
    "Scienze dei mat. dent. e lab.":              "Scienze dei Materiali Dentali",
    "Gnatologia":                                 "Gnatologia",
    "Legislazione sanitaria":                     "Legislazione Sanitaria",
    "Dir. prat.com., leg. soc./san.":             "Diritto Sanitario",
    "Gest. progetto, org. di impresa":            "Gestione Progetto",
}



def make_class_id(nome):
    """'1 A' → '1A',  '<3 C/T> 3 C' → '3C',  '1 MAQ1' → '1MAQ1'"""
    # Remove angle-bracket prefixes like <3 C/T>
    nome = re.sub(r'<[^>]+>\s*', '', nome)
    # Remove all spaces
    nome = nome.replace(" ", "")
    return nome


def normalize_ora(entry):
    """Convert a raw slot entry to clean API format."""
    if entry is None:
        return None

    materia_raw = (entry.get("materia") or "").strip()
    materia_short = MATERIA_SHORT.get(materia_raw, materia_raw) if materia_raw else None

    docenti_raw = entry.get("docenti") or []
    docenti = []
    for d in docenti_raw:
        d = d.strip()
        if d and d not in docenti:
            docenti.append(d)

    aula_raw = (entry.get("aula") or "").strip()
    # Normalize aula: "AULA B 104" -> "B104", "LAB. INF 1 (B 208)" -> keep clean
    aula = aula_raw if aula_raw else None

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


def build_class_object(raw):
    """Build the clean API class object from raw parsed data."""
    classe_nome = raw["classe"].strip()
    # Remove angle-bracket class-group prefix
    classe_display = re.sub(r'<[^>]+>\s*', '', classe_nome).strip()
    classe_id = make_class_id(classe_nome)

    orario_clean = {}

    for day_key, day_label in DAYS_ORDERED:
        raw_day = raw["orario"].get(day_label, {})
        if not raw_day:
            continue

        slots_clean = {}
        has_any = False

        for raw_time, norm_time in TIME_NORMALIZE.items():
            entry = raw_day.get(raw_time)
            ora = normalize_ora(entry)
            if ora:
                slots_clean[norm_time] = ora
                has_any = True

        if has_any:
            orario_clean[day_key] = slots_clean

    # Compute pomeriggio: does any day have afternoon slots?
    has_afternoon = any(
        slot in day_slots
        for day_slots in orario_clean.values()
        for slot in AFTERNOON_SLOTS
    )

    # Build giorni_attivi list (sorted by week order)
    day_order = {k: i for i, (k, _) in enumerate(DAYS_ORDERED)}
    giorni_attivi = sorted(orario_clean.keys(), key=lambda d: day_order.get(d, 99))

    return {
        "id": classe_id,
        "nome": classe_display,
        "docente_coordinatore": (raw.get("docente_coordinatore") or "").strip(),
        "pomeriggio": has_afternoon,
        "giorni_attivi": giorni_attivi,
        "orario": orario_clean,
    }


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    with open(INPUT_PATH, encoding="utf-8") as f:
        raw_data = json.load(f)

    classes = [build_class_object(r) for r in raw_data]

    os.makedirs(CLASSI_DIR, exist_ok=True)

    # ── 1. orario_api.json: full dataset indexed by class ID ──────────────
    api_dict = {c["id"]: c for c in classes}

    with open(API_PATH, "w", encoding="utf-8") as f:
        json.dump(api_dict, f, ensure_ascii=False, indent=2)
    print(f"Scritto: {API_PATH}  ({len(api_dict)} classi)")

    # ── 2. classi_index.json: lightweight index ───────────────────────────
    index = [
        {
            "id":                   c["id"],
            "nome":                 c["nome"],
            "docente_coordinatore": c["docente_coordinatore"],
            "pomeriggio":           c["pomeriggio"],
            "giorni_attivi":        c["giorni_attivi"],
        }
        for c in classes
    ]

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print(f"Scritto: {INDEX_PATH}")

    # ── 3. classi/<ID>.json: one file per class ───────────────────────────
    for c in classes:
        path = os.path.join(CLASSI_DIR, f"{c['id']}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(c, f, ensure_ascii=False, indent=2)

    print(f"Scritti: {len(classes)} file in {CLASSI_DIR}/")

    # ── Stats ──────────────────────────────────────────────────────────────
    total_ore = sum(
        len(slots)
        for c in classes
        for slots in c["orario"].values()
    )
    with_two_teachers = sum(
        1
        for c in classes
        for slots in c["orario"].values()
        for ora in slots.values()
        if ora and len(ora.get("docenti", [])) >= 2
    )
    print(f"\nStatistiche:")
    print(f"  Classi totali:        {len(classes)}")
    print(f"  Ore lezione totali:   {total_ore}")
    print(f"  Ore con 2+ docenti:   {with_two_teachers}")
    print(f"  Classi con pomeriggio:{sum(1 for c in classes if c['pomeriggio'])}")

    # ── Sample output ──────────────────────────────────────────────────────
    sample = classes[0]
    print(f"\n{'='*62}")
    print(f"SAMPLE: {sample['id']}  ({sample['nome']})")
    print(f"  Coord: {sample['docente_coordinatore']}")
    print(f"  Giorni attivi: {sample['giorni_attivi']}")
    print(f"  Pomeriggio: {sample['pomeriggio']}")

    for day in sample['giorni_attivi'][:2]:
        print(f"\n  [{day}]")
        for slot, ora in sample['orario'][day].items():
            docs  = ", ".join(ora.get("docenti", []))
            mat   = ora.get("materia", "?")
            aula  = ora.get("aula", "—")
            print(f"    {slot}  {mat:<38}  {docs}  [{aula}]")


if __name__ == "__main__":
    main()
