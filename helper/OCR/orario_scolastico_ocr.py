import cv2
import numpy as np
import pytesseract
import re
import json
import os
import sys
from pathlib import Path
from dataclasses import dataclass, field, asdict

# ---------------------------------------------------------------------------
# CONFIGURAZIONE TESSERACT
# ---------------------------------------------------------------------------
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Users\matti\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
)

TESSERACT_CONFIG = (
    "--oem 3 "
    "--psm 6 "
    "-l ita+eng"
)

# ---------------------------------------------------------------------------
# RANGE HSV — calibrati sull'immagine reale (analisi pixel automatica)
#
#  Titolo  : H=108-135  S>150  V>130   (blu/ciano saturo)
#  Giallo  : H= 18- 42  S>100  V>150   (giallo brillante → entrate)
#  Rosso   : H=  0- 15  S>100  V> 80   (rosso → cambio aula)
#            H=163-180  S>100  V> 80   (rosso wraparound HSV)
#  Ciano   : H=100-135  S= 30-180 V>190 (azzurro chiaro → blocco ESCE)
#  Beige   : H= 10- 35  S= 10- 90 V>180 (crema → FSL/note speciali)
# ---------------------------------------------------------------------------
COLOR_RANGES = {
    "titolo": [
        (np.array([108, 150, 130]), np.array([135, 255, 255])),
    ],
    "giallo": [
        (np.array([18, 100, 150]), np.array([42, 255, 255])),
    ],
    "rosso": [
        (np.array([0,  100,  80]), np.array([15, 255, 255])),
        (np.array([163, 100, 80]), np.array([180, 255, 255])),
    ],
    "ciano": [
        (np.array([100, 30, 190]), np.array([135, 180, 255])),
    ],
    "beige": [
        (np.array([10, 10, 180]), np.array([35, 90, 255])),
    ],
}

MIN_BLOCK_AREA = 2500


# ===========================================================================
# DATA CLASSES
# ===========================================================================

@dataclass
class EntratUscita:
    ora: str
    classi: list = field(default_factory=list)
    note: str = ""

@dataclass
class CambioAula:
    classe: str
    orario: str
    aula: str

@dataclass
class NotaSpeciale:
    tipo: str
    testo: str

@dataclass
class ScheduleDay:
    giorno: str = ""
    data: str = ""
    entrate: list = field(default_factory=list)
    uscite:  list = field(default_factory=list)
    cambi_aula: list = field(default_factory=list)
    note: list = field(default_factory=list)
    raw_blocks: dict = field(default_factory=dict)


# ===========================================================================
# 1. PREPROCESSING
# ===========================================================================

def load_and_resize(path: str, max_width: int = 1600) -> np.ndarray:
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"Impossibile aprire: {path}")
    h, w = img.shape[:2]
    if w > max_width:
        scale = max_width / w
        img = cv2.resize(img, (int(w * scale), int(h * scale)),
                         interpolation=cv2.INTER_LANCZOS4)
    return img


def enhance_for_ocr(region: np.ndarray) -> np.ndarray:
    h, w = region.shape[:2]
    scale = max(1.0, 180 / (min(h, w) + 1e-5))
    if scale > 1.1:
        region = cv2.resize(region, (int(w * scale), int(h * scale)),
                            interpolation=cv2.INTER_CUBIC)
    gray   = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    gray   = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7,
                                      searchWindowSize=21)
    binary = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, blockSize=21, C=8
    )
    binary = cv2.copyMakeBorder(binary, 10, 10, 10, 10,
                                cv2.BORDER_CONSTANT, value=255)
    return binary


# ===========================================================================
# 2. RILEVAMENTO BLOCCHI COLORATI
# ===========================================================================

def get_color_mask(hsv: np.ndarray, color_name: str) -> np.ndarray:
    mask   = np.zeros(hsv.shape[:2], dtype=np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    for lo, hi in COLOR_RANGES.get(color_name, []):
        mask |= cv2.inRange(hsv, lo, hi)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel, iterations=1)
    return mask


def find_blocks(img: np.ndarray, color_name: str,
                min_area: int = MIN_BLOCK_AREA) -> list:
    hsv      = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask     = get_color_mask(hsv, color_name)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
    blocks = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w * h < min_area:
            continue
        blocks.append((x, y, w, h, img[y:y+h, x:x+w]))
    blocks.sort(key=lambda b: (b[1], b[0]))
    return blocks


# ===========================================================================
# 3. OCR
# ===========================================================================

def ocr_region(crop: np.ndarray) -> str:
    prepared = enhance_for_ocr(crop)
    raw      = pytesseract.image_to_string(prepared, config=TESSERACT_CONFIG)
    return normalize_text(raw)


def normalize_text(text: str) -> str:
    text = text.upper()
    text = re.sub(r"[^\w\s.\-:/+*àèéìòùÀÈÉÌÒÙ]", " ", text)
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r"\bO(?=\d)", "0", text)
    text = re.sub(r"(?<=\d)O\b", "0", text)
    text = re.sub(r"\bl(?=\d)", "1", text)
    return text.strip()


# ===========================================================================
# 4. PARSING
# ===========================================================================

RE_TIME   = re.compile(r"\b(\d{1,2}[.:]\d{2})\s*[-–]\s*(\d{1,2}[.:]\d{2})\b")
RE_CLASS  = re.compile(r"\b(\d\s*[A-Z]{1,3}(?:/[A-Z])?)\b")
RE_AULA   = re.compile(
    r"\b((?:AULA|LAB\.?|LABORATORIO)\s+[A-Z0-9]{1,10}(?:\s+[A-Z0-9]{1,10})?)\b"
)
RE_ENTRY  = re.compile(
    r"ENTRA\s+ALLE\s+(\d{1,2}[.:]\d{2})(.*?)(?=ENTRA\s+ALLE|ESCE\s+ALLE|\Z)",
    re.DOTALL
)
RE_EXIT   = re.compile(
    r"ESCE\s+ALLE\s+(\d{1,2}[.:]\d{2})(.*?)(?=ENTRA\s+ALLE|ESCE\s+ALLE|\Z)",
    re.DOTALL
)


def fmt_time(s: str) -> str:
    return s.replace(".", ":")

def extract_classes(text: str) -> list:
    seen, out = set(), []
    for m in RE_CLASS.finditer(text):
        c = m.group(1).replace(" ", "")
        if c not in seen and len(c) <= 5:
            seen.add(c); out.append(c)
    return out

def extract_aula(text: str) -> str:
    m = RE_AULA.search(text)
    return m.group(1).strip() if m else ""

def extract_orario(text: str) -> str:
    m = RE_TIME.search(text)
    return f"{fmt_time(m.group(1))} - {fmt_time(m.group(2))}" if m else ""

def parse_title(text: str):
    days = ["LUNEDÌ","MARTEDÌ","MERCOLEDÌ","GIOVEDÌ","VENERDÌ","SABATO","DOMENICA"]
    giorno = next((d for d in days if d in text), "")
    data   = text.replace(giorno, "").strip() if giorno else text.strip()
    # Pulisci caratteri non alfabetici all'inizio della data
    data   = re.sub(r"^[^0-9A-Z]+", "", data).strip()
    return giorno, data

def parse_entry_exit(text: str, kind: str) -> list:
    pattern = RE_ENTRY if kind == "entrate" else RE_EXIT
    results = []
    for m in pattern.finditer(text):
        ora    = fmt_time(m.group(1))
        body   = m.group(2)
        classi = extract_classes(body)
        nota_m = re.search(r"\*\s*(.+)", body)
        nota   = nota_m.group(1).strip() if nota_m else ""
        results.append(EntratUscita(ora=ora, classi=classi, note=nota))
    return results

def parse_cambi_aula(text: str) -> list:
    cambi = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        orario      = extract_orario(line)
        aula        = extract_aula(line)
        classe_part = re.split(r"[:\s]\d{1,2}[.:]\d{2}", line)[0]
        classi      = extract_classes(classe_part)
        if classi and orario:
            cambi.append(CambioAula(
                classe=" ".join(classi),
                orario=orario,
                aula=aula
            ))
    return cambi

def classify_note(text: str) -> NotaSpeciale:
    if "F.S.L" in text or "FSL" in text:
        tipo = "FSL"
    elif "LAB" in text:
        tipo = "laboratorio"
    elif "GITA" in text or "LICEO" in text:
        tipo = "gita"
    else:
        tipo = "generico"
    return NotaSpeciale(tipo=tipo, testo=text)


# ===========================================================================
# 5. PIPELINE PRINCIPALE
# ===========================================================================

def process_image(path: str, debug: bool = False) -> dict:
    img    = load_and_resize(path)
    result = ScheduleDay()

    if debug:
        os.makedirs("debug", exist_ok=True)
        _save_debug_masks(img, path)

    # --- TITOLO ---
    title_blocks = find_blocks(img, "titolo")
    if title_blocks:
        title_text = ocr_region(title_blocks[0][4])
    else:
        title_text = ocr_region(img[0:max(50, img.shape[0]//8), :])
    result.giorno, result.data = parse_title(title_text)
    result.raw_blocks["titolo"] = title_text

    # --- GIALLO (entrate, ed eventuali uscite miste) ---
    yellow_texts = []
    for i, (x, y, w, h, crop) in enumerate(find_blocks(img, "giallo")):
        t = ocr_region(crop)
        yellow_texts.append(t)
        if debug: cv2.imwrite(f"debug/giallo_{i}.png", crop)
    full_yellow = "\n".join(yellow_texts)
    result.raw_blocks["giallo"] = full_yellow
    result.entrate = parse_entry_exit(full_yellow, "entrate")
    result.uscite  = parse_entry_exit(full_yellow, "uscite")

    # --- CIANO (blocco ESCE ALLE azzurro chiaro) ---
    cyan_texts = []
    for i, (x, y, w, h, crop) in enumerate(find_blocks(img, "ciano")):
        t = ocr_region(crop)
        cyan_texts.append(t)
        if debug: cv2.imwrite(f"debug/ciano_{i}.png", crop)
    full_cyan = "\n".join(cyan_texts)
    result.raw_blocks["ciano"] = full_cyan
    result.uscite  += parse_entry_exit(full_cyan, "uscite")
    result.entrate += parse_entry_exit(full_cyan, "entrate")

    # --- ROSSO (cambi aula) ---
    red_texts = []
    for i, (x, y, w, h, crop) in enumerate(find_blocks(img, "rosso")):
        t = ocr_region(crop)
        red_texts.append(t)
        if debug: cv2.imwrite(f"debug/rosso_{i}.png", crop)
    full_red = "\n".join(red_texts)
    result.raw_blocks["rosso"] = full_red
    result.cambi_aula = parse_cambi_aula(full_red)

    # --- BEIGE (note FSL ecc.) ---
    for i, (x, y, w, h, crop) in enumerate(find_blocks(img, "beige", min_area=1500)):
        t = ocr_region(crop)
        if debug: cv2.imwrite(f"debug/beige_{i}.png", crop)
        if t.strip():
            result.note.append(classify_note(t))

    # --- FALLBACK titolo ---
    if not result.giorno:
        for text in [result.raw_blocks.get("titolo",""),
                     result.raw_blocks.get("giallo","")]:
            for line in text.splitlines():
                g, d = parse_title(line.strip())
                if g:
                    result.giorno, result.data = g, d
                    break
            if result.giorno:
                break

    output = asdict(result)
    if not debug:
        output.pop("raw_blocks", None)
    return output


def _save_debug_masks(img: np.ndarray, path: str):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    for cname in COLOR_RANGES:
        mask    = get_color_mask(hsv, cname)
        overlay = img.copy()
        overlay[mask == 0] = (overlay[mask == 0] * 0.3).astype(np.uint8)
        cv2.imwrite(f"debug/mask_{cname}.png", overlay)
        print(f"  [debug] {cname}: {(mask>0).sum()} pixel rilevati")


# ===========================================================================
# 6. BATCH
# ===========================================================================

SUPPORTED_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}

def process_folder(folder: str, debug: bool = False) -> list:
    folder_path = Path(folder)
    if not folder_path.is_dir():
        raise NotADirectoryError(f"Cartella non trovata: {folder}")
    images = sorted(p for p in folder_path.iterdir()
                    if p.suffix.lower() in SUPPORTED_EXT)
    if not images:
        print(f"[WARN] Nessuna immagine in: {folder}"); return []

    results = []
    for img_path in images:
        print(f"[INFO] {img_path.name}")
        try:
            data = process_image(str(img_path), debug=debug)
            data["_source"] = img_path.name
            results.append(data)
            print(f"  → {data.get('giorno','')} {data.get('data','')} | "
                  f"entrate={len(data.get('entrate',[]))} "
                  f"uscite={len(data.get('uscite',[]))} "
                  f"cambi={len(data.get('cambi_aula',[]))}")
        except Exception as exc:
            print(f"[ERROR] {img_path.name}: {exc}")
            results.append({"_source": img_path.name, "_error": str(exc)})
    return results

def save_json(data, output_path: str):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[OK] Salvato: {output_path}")


# ===========================================================================
# 7. ENTRY POINT
# ===========================================================================

def main():
    args   = sys.argv[1:]
    if not args:
        print("Uso: python orario_scolastico_ocr.py <immagine_o_cartella> [--debug]")
        sys.exit(1)
    target = args[0]
    debug  = "--debug" in args

    if Path(target).is_dir():
        results = process_folder(target, debug=debug)
        save_json(results, "output_batch.json")
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        result = process_image(target, debug=debug)
        out    = Path(target).stem + "_output.json"
        save_json(result, out)
        print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
