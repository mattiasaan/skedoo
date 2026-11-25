"""
Segmentazione dell'immagine in riquadri e righe (OpenCV).

1. Taglio ricorsivo X-Y: lo sfondo in legno e i bordi neri dei riquadri
   fungono da "spazio vuoto" tra un riquadro e l'altro.
2. Ogni riquadro viene classificato dal colore di fondo.
3. Il pannello rosso "CAMBIO AULA" viene diviso in righe dal profilo
   dell'inchiostro (testo/sfondi diversi dal rosso).
4. Gli altri riquadri vengono divisi in righe di testo (per i motori OCR
   che lavorano meglio una riga alla volta).
"""
from dataclasses import dataclass
from typing import List

import cv2
import numpy as np


# ---------------------------------------------------------------------------
# Taglio X-Y
# ---------------------------------------------------------------------------
def _gap_mask(img: np.ndarray) -> np.ndarray:
    """True dove c'e' 'vuoto': legno (marrone scuro) o bordo nero."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    wood = (h >= 4) & (h <= 24) & (s >= 70) & (v <= 130)
    dark = v <= 75
    return wood | dark


def _content_runs(flags: np.ndarray, mingap: int):
    g = flags.copy()
    n = len(g)
    i = 0
    while i < n:
        if g[i]:
            j = i
            while j < n and g[j]:
                j += 1
            if j - i < mingap:
                g[i:j] = False
            i = j
        else:
            i += 1
    out, s = [], None
    for i, f in enumerate(g):
        if not f and s is None:
            s = i
        if f and s is not None:
            out.append((s, i))
            s = None
    if s is not None:
        out.append((s, n))
    return out


def _xycut(m, x0, y0, x1, y1, out, thr=0.96, mingap=2):
    sub = m[y0:y1, x0:x1]
    if sub.size == 0:
        return
    ry = _content_runs(sub.mean(1) >= thr, mingap)
    rx = _content_runs(sub.mean(0) >= thr, mingap)
    if not ry or not rx:
        return
    x0, y0, x1, y1 = x0 + rx[0][0], y0 + ry[0][0], x0 + rx[-1][1], y0 + ry[-1][1]
    sub = m[y0:y1, x0:x1]
    ry = _content_runs(sub.mean(1) >= thr, mingap)
    rx = _content_runs(sub.mean(0) >= thr, mingap)
    if len(ry) > 1:
        for a, b in ry:
            _xycut(m, x0, y0 + a, x1, y0 + b, out, thr, mingap)
        return
    if len(rx) > 1:
        for a, b in rx:
            _xycut(m, x0 + a, y0, x0 + b, y1, out, thr, mingap)
        return
    out.append((x0, y0, x1 - x0, y1 - y0))


# ---------------------------------------------------------------------------
# Colori
# ---------------------------------------------------------------------------
def nome_colore(bgr) -> str:
    px = np.uint8([[[int(bgr[0]), int(bgr[1]), int(bgr[2])]]])
    h, s, v = [int(x) for x in cv2.cvtColor(px, cv2.COLOR_BGR2HSV)[0, 0]]
    if s < 40 and v > 200:
        return "bianco"
    if 100 <= h <= 135 and s > 150:
        return "blu"
    if (h <= 8 or h >= 170) and s > 180 and v > 120:
        return "rosso"
    if 22 <= h <= 38 and s > 150:
        return "giallo"
    if 45 <= h <= 75 and s > 100:
        return "verde"
    if 45 <= h <= 75 and 20 <= s <= 100:
        return "verde_chiaro"
    if 76 <= h <= 105 and 20 <= s <= 100:
        return "azzurro_chiaro"
    if 8 <= h < 22 and s > 100:
        return "arancio"
    if 8 <= h < 22 and 30 <= s <= 100:
        return "pesca"
    return "altro"


# colore -> famiglia di riquadro
def famiglia_da_colore(colore: str, y: int) -> str:
    if colore == "blu":
        return "titolo"
    if colore == "rosso":
        return "cambio_aula"
    if colore == "giallo":
        return "giallo"
    if colore in ("verde_chiaro", "azzurro_chiaro"):
        return "chiaro"
    if colore == "bianco":
        return "bianco"
    return "info"          # arancio, pesca, verde, altro


@dataclass
class Box:
    x: int
    y: int
    w: int
    h: int
    colore: str
    famiglia: str          # titolo | cambio_aula | giallo | chiaro | bianco | info

    def crop(self, img, pad=0):
        H, W = img.shape[:2]
        return img[max(0, self.y - pad):min(H, self.y + self.h + pad),
                   max(0, self.x - pad):min(W, self.x + self.w + pad)]


def segmenta_riquadri(img: np.ndarray, min_area=300) -> List[Box]:
    m = _gap_mask(img)
    leaves = []
    _xycut(m, 0, 0, img.shape[1], img.shape[0], leaves)
    boxes = []
    for (x, y, w, h) in leaves:
        if w * h < min_area or w < 12 or h < 8:
            continue
        inner = img[y + 3:y + h - 3, x + 3:x + w - 3]
        if inner.size == 0:
            continue
        med = np.median(inner.reshape(-1, 3), axis=0)
        col = nome_colore(med)
        boxes.append(Box(x, y, w, h, col, famiglia_da_colore(col, y)))
    boxes.sort(key=lambda b: (b.x > img.shape[1] * 0.5, b.y, b.x))
    return boxes


# ---------------------------------------------------------------------------
# Righe
# ---------------------------------------------------------------------------
def _ink_mask(crop: np.ndarray, ref_bgr, tol=90) -> np.ndarray:
    d = np.abs(crop.astype(np.int16) - np.array(ref_bgr, dtype=np.int16)).sum(axis=2)
    return d > tol


def _spans(frac: np.ndarray, thr: float, min_h: int, merge_gap: int):
    on = frac > thr
    spans, s = [], None
    for i, f in enumerate(on):
        if f and s is None:
            s = i
        if (not f) and s is not None:
            spans.append([s, i])
            s = None
    if s is not None:
        spans.append([s, len(on)])
    merged = []
    for sp in spans:
        if merged and sp[0] - merged[-1][1] < merge_gap:
            merged[-1][1] = sp[1]
        else:
            merged.append(sp)
    return [(a, b) for a, b in merged if b - a >= min_h]


def _bg_ref(crop: np.ndarray, margin=5):
    """Colore di fondo: mediana dei bordi sinistro/destro/alto/basso."""
    h, w = crop.shape[:2]
    mg = min(margin, max(1, w // 4), max(1, h // 4))
    strips = [crop[:, :mg].reshape(-1, 3), crop[:, -mg:].reshape(-1, 3),
              crop[:mg, :].reshape(-1, 3), crop[-mg:, :].reshape(-1, 3)]
    return np.median(np.vstack(strips), axis=0)


def _trim_x(ink_rows: np.ndarray, pad=6):
    cols = np.where(ink_rows.sum(axis=0) > 0)[0]
    if len(cols) == 0:
        return 0, ink_rows.shape[1]
    return max(0, cols[0] - pad), min(ink_rows.shape[1], cols[-1] + 1 + pad)


@dataclass
class Riga:
    y0: int
    y1: int
    x0: int            # ritaglio "ampio" (con un po' di sfondo attorno al testo)
    x1: int
    sospetta: bool = False        # righe fuse e divise per stima
    tx0: int = -1      # ritaglio "stretto" (solo sfondo della riga, senza rosso)
    tx1: int = -1


def _ink_non_rosso(panel: np.ndarray, margine=60, vmin=80) -> np.ndarray:
    """Contenuto = pixel ne' 'rossastri' (R non domina G e B) ne' quasi neri.
    Cosi' contano sia il testo chiaro su sfondo nero, sia gli sfondi colorati
    (giallo, blu, verde...), mentre rosso del pannello, fili di rosso scuro e
    sfondo nero tra le righe restano 'vuoto'."""
    p = panel.astype(np.int16)
    b, g, r = p[:, :, 0], p[:, :, 1], p[:, :, 2]
    non_rosso = (r - np.maximum(g, b)) < margine
    non_nero = p.max(axis=2) >= vmin
    return non_rosso & non_nero


def _non_rossastro(panel: np.ndarray, margine=60) -> np.ndarray:
    p = panel.astype(np.int16)
    return (p[:, :, 2] - np.maximum(p[:, :, 1], p[:, :, 0])) < margine


def _trim_x_bg(nr_span: np.ndarray, pad=2):
    """Estremi orizzontali dello sfondo della riga (nero o colorato), senza il rosso."""
    frac = nr_span.mean(axis=0)
    cols = np.where(frac > 0.25)[0]
    if len(cols) == 0:
        return 0, nr_span.shape[1]
    return max(0, cols[0] - pad), min(nr_span.shape[1], cols[-1] + 1 + pad)


def righe_pannello(panel: np.ndarray) -> List[Riga]:
    """Righe del pannello rosso 'CAMBIO AULA' (anche testo bianco su rosso o su nero)."""
    ink = _ink_non_rosso(panel)
    nr = _non_rossastro(panel)
    nr[:, :2] = False
    nr[:, -2:] = False
    ink[:, :2] = False
    ink[:, -2:] = False
    frac = ink.mean(axis=1)
    spans = _spans(frac, thr=0.012, min_h=6, merge_gap=1)
    if not spans:
        return []
    # passo tra righe consecutive (stabile anche se alcune righe sono solo testo)
    starts = [a for a, _ in spans]
    diffs = sorted(starts[i + 1] - starts[i] for i in range(len(starts) - 1))
    pitch = diffs[len(diffs) // 2] if diffs else 16
    out = []
    for a, b in spans:
        h = b - a
        if pitch >= 10 and h > 1.5 * pitch:        # righe fuse (sfondi colorati adiacenti)
            for (ya, yb, sosp) in _dividi_blob(panel, ink, a, b, pitch):
                tx0, tx1 = _trim_x_bg(nr[ya:yb])
                x0, x1 = _trim_x(ink[ya:yb])
                out.append(Riga(ya, yb, x0, x1, sospetta=sosp, tx0=tx0, tx1=tx1))
        else:
            tx0, tx1 = _trim_x_bg(nr[a:b])
            x0, x1 = _trim_x(ink[a:b])
            out.append(Riga(a, b, x0, x1, tx0=tx0, tx1=tx1))
    return out


def _dividi_blob(panel, ink, a, b, pitch):
    """Divide un blocco di righe adiacenti usando i cambi di colore di sfondo."""
    h = b - a
    k_atteso = max(2, int(round((h + 2) / pitch)))
    seg = panel[a:b].astype(np.int16)
    m = ink[a:b]
    cols = []
    for y in range(h):
        px = seg[y][m[y]]
        cols.append(np.median(px, axis=0) if len(px) > 6 else np.array([-999, -999, -999]))
    cols = np.array(cols)
    diff = np.abs(np.diff(cols, axis=0)).sum(axis=1)
    cand = [(float(d), i + 1) for i, d in enumerate(diff) if d > 100]
    cand.sort(reverse=True)
    cuts = []
    for d, y in cand:
        if y < 6 or h - y < 6:
            continue
        if all(abs(y - c) >= 7 for c in cuts):
            cuts.append(y)
    cuts.sort()
    if len(cuts) == k_atteso - 1:
        edges = [0] + cuts + [h]
        return [(a + edges[i], a + edges[i + 1], False) for i in range(len(edges) - 1)]
    # fallback: parti uguali (segnalato)
    step = h / k_atteso
    return [(int(a + i * step), int(a + (i + 1) * step), True) for i in range(k_atteso)]


def righe_testo(box_crop: np.ndarray) -> List[Riga]:
    """Righe di testo di un riquadro qualsiasi (sfondo uniforme)."""
    ref = _bg_ref(box_crop, margin=4)
    ink = _ink_mask(box_crop, ref, tol=120)
    ink[:3, :] = False
    ink[-3:, :] = False
    ink[:, :3] = False
    ink[:, -3:] = False
    frac = ink.mean(axis=1)
    spans = _spans(frac, thr=0.004, min_h=5, merge_gap=3)
    out = []
    for a, b in spans:
        x0, x1 = _trim_x(ink[a:b])
        out.append(Riga(a, b, x0, x1))
    return out


def ritaglia_riga(src: np.ndarray, r: Riga, pad=1, stretto=False) -> np.ndarray:
    H, W = src.shape[:2]
    x0, x1 = (r.tx0, r.tx1) if (stretto and r.tx0 >= 0) else (r.x0, r.x1)
    return src[max(0, r.y0 - pad):min(H, r.y1 + pad), max(0, x0 - pad):min(W, x1 + pad)]
