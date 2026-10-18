"""
diagnosi_colori.py
------------------
Analizza i colori reali dell'immagine e mostra i valori HSV
per calibrare i range in orario_scolastico_ocr.py
"""

import cv2
import numpy as np
import sys

pytesseract_path = r"C:\Users\matti\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

def sample_hsv(img_path: str):
    img = cv2.imread(img_path)
    if img is None:
        print(f"ERRORE: impossibile aprire {img_path}")
        return

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, w = img.shape[:2]
    print(f"\nImmagine: {img_path}  →  {w}x{h} pixel")
    print("=" * 60)

    # Campiona una griglia 10x10 di punti e mostra i valori HSV unici
    print("\n[1] CAMPIONAMENTO A GRIGLIA (H, S, V) per area:")
    regions = {
        "TITOLO (riga top)":    (0,    0,    w,    h//8),
        "SINISTRA (blocchi)":   (0,    h//8, w//2, h),
        "DESTRA (cambi aula)":  (w//2, h//8, w,    h),
        "BASSO-SX (FSL)":       (0,    h*3//4, w//2, h),
    }

    for name, (x1, y1, x2, y2) in regions.items():
        region_bgr = img[y1:y2, x1:x2]
        region_hsv = hsv[y1:y2, x1:x2]
        # Calcola il colore medio della regione (escludendo pixel molto scuri = bordi/legno)
        mask = region_hsv[:,:,2] > 30  # esclude pixel quasi neri
        if mask.sum() == 0:
            continue
        h_vals = region_hsv[:,:,0][mask]
        s_vals = region_hsv[:,:,1][mask]
        v_vals = region_hsv[:,:,2][mask]
        print(f"\n  {name}:")
        print(f"    H: min={h_vals.min():3d}  max={h_vals.max():3d}  mean={h_vals.mean():.0f}")
        print(f"    S: min={s_vals.min():3d}  max={s_vals.max():3d}  mean={s_vals.mean():.0f}")
        print(f"    V: min={v_vals.min():3d}  max={v_vals.max():3d}  mean={v_vals.mean():.0f}")

    # Campiona pixel specifici su colori attesi
    print("\n[2] PIXEL SPECIFICI (clicca coordinate visivamente):")
    sample_points = {
        "Titolo (centro top)":      (w//2,  h//16),
        "Blocco giallo (centro)":   (w//4,  h//5),
        "Blocco verde (uscita)":    (w//4,  h//2),
        "Blocco rosso (dx)":        (w*3//4, h//3),
        "Blocco FSL (beige)":       (w//4,  h*7//8),
    }
    for name, (px, py) in sample_points.items():
        px = max(0, min(px, w-1))
        py = max(0, min(py, h-1))
        b, g, r = img[py, px]
        hh, ss, vv = hsv[py, px]
        print(f"  {name:35s}  BGR=({b:3d},{g:3d},{r:3d})  HSV=({hh:3d},{ss:3d},{vv:3d})")

    # Genera automaticamente i range consigliati per ogni colore cercato
    print("\n[3] RANGE HSV CONSIGLIATI (±15 H, ±60 S/V dal campione):")
    auto_ranges = {}
    for name, (px, py) in sample_points.items():
        px = max(0, min(px, w-1))
        py = max(0, min(py, h-1))
        hh, ss, vv = hsv[py, px]
        lo = (max(0, hh-15), max(0, ss-80), max(0, vv-80))
        hi = (min(180, hh+15), 255, 255)
        print(f"  {name:35s}  lo={lo}  hi={hi}")
        auto_ranges[name] = (lo, hi)

    # Salva immagine annotata con i punti campionati
    debug_img = img.copy()
    for name, (px, py) in sample_points.items():
        px = max(0, min(px, w-1))
        py = max(0, min(py, h-1))
        cv2.circle(debug_img, (px, py), 8, (0, 255, 0), 2)
        cv2.putText(debug_img, name[:10], (px+10, py),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,255,0), 1)
    out = img_path.replace(".png", "_debug_hsv.png").replace(".jpg", "_debug_hsv.jpg")
    cv2.imwrite(out, debug_img)
    print(f"\n[OK] Immagine annotata salvata: {out}")

    # Mostra le maschere per ogni colore
    print("\n[4] TEST MASCHERE — pixel trovati per colore:")
    test_ranges = {
        "giallo":  [(np.array([15, 80, 80]),  np.array([40, 255, 255]))],
        "verde":   [(np.array([35, 50, 50]),  np.array([90, 255, 255]))],
        "rosso":   [(np.array([0,  80, 80]),  np.array([15, 255, 255])),
                    (np.array([160,80, 80]),  np.array([180,255, 255]))],
        "celeste": [(np.array([85, 80, 80]),  np.array([135,255, 255]))],
        "arancio": [(np.array([8,  80, 80]),  np.array([22, 255, 255]))],
        "beige":   [(np.array([15, 10, 180]), np.array([40, 80,  255]))],
    }
    for cname, ranges in test_ranges.items():
        mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for lo, hi in ranges:
            mask |= cv2.inRange(hsv, lo, hi)
        pct = mask.sum() / (h * w * 255) * 100
        print(f"  {cname:10s}: {mask.sum()//255:6d} pixel  ({pct:.1f}% immagine)")
        # Salva maschera
        cv2.imwrite(img_path.replace(".png", f"_mask_{cname}.png"), mask)

    print("\nFine diagnosi. Controlla i valori HSV sopra e aggiorna COLOR_RANGES nel codice principale.")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "img-test.png"
    sample_hsv(path)
