"""Genera i file JSON di riferimento (trascrizione manuale verificata a 3x)."""
import json, re, sys
from pathlib import Path

def righe(txt):
    out = []
    for ln in txt.strip().splitlines():
        ln = ln.strip()
        if not ln:
            continue
        m = re.match(r"^(.*?)\s*:?\s*(\d\d\.\d\d)\s*-\s*(\d\d\.\d\d)\s+(.*)$", ln)
        cl = m.group(1).replace(" ", "").replace(":", "").strip()
        out.append({"classe": cl or None,
                    "orario": f"{m.group(2).replace('.', ':')} - {m.group(3).replace('.', ':')}",
                    "aula": m.group(4).strip()})
    return out

def box(ora, classi):
    return {"ora": ora.replace(".", ":"), "classi": classi.split()}

GT = {}

cambi_lun30 = """
1 A : 08.10 - 09.50 AULA D205
1 B : 08.10 - 09.50 AULA D206
1 C : 09.50 - 11.45 AULA D205
1 D : 09.50 - 11.45 AULA D206
1 E : 11.45 - 12.35 AULA D205
1 I : 09.50 - 10.40 AULA B115
1 MAQ1 : 09.50 - 10.40 LAB. B119
1 P : 11.45 - 12.35 AULA D206
3 C/T : 11.45 - 13.25 AULA B207
3 J : 09.50 - 10.40 AULA B013
3 L : 12.35 - 13.25 AULA B011
3 OD : 09.50 - 10.40 AULA B011
4 D : 08.10 - 09.50 AULA B207
4 F : 08.10 - 09.50 AULA B108
4 I : 08.10 - 10.40 AULA D204
4 J : 10.55 - 12.35 AULA D204
4 MAT : 12.35 - 13.25 AULA B016
5 B : 10.55 - 11.45 AULA B210
5 G/N : 08.10 - 13.25 AULA A106
5 H : 08.10 - 13.25 AULA A106
"""
lun30 = {
  "giorno": "LUNEDÌ", "numero": 30, "mese": "MARZO",
  "entrate": [box("09.00", "1F 4J"), box("09.50", "1MAQ2 4N"), box("15.20", "2F")],
  "uscite": [box("12.35", "1P 2D")],
  "senza_lezioni_pomeridiane": [],
  "cambi_aula": righe(cambi_lun30),
  "n_note": 1,
}
GT["img0"] = lun30
GT["img2"] = lun30

GT["img1"] = {
  "giorno": "LUNEDÌ", "numero": 9, "mese": "FEBBRAIO",
  "entrate": [box("09.00", "3H"), box("09.50", "1P 3F 4J")],
  "uscite": [box("11.45", "5A 5N"), box("16.10", "4L")],
  "senza_lezioni_pomeridiane": [],
  "cambi_aula": righe("""
1 B : 08.10 - 09.50 LAB. D004
1 C : 09.50 - 11.45 LAB. D004
1 L : 09.00 - 10.40 AULA A106
1 MAQ2 : 11.45 - 13.25 AULA B309
1 P : 10.55 - 12.35 AULA A106
2 C : 12.35 - 13.25 AULA B311
2 D : 11.45 - 13.25 AULA B307
2 F : 12.35 - 13.25 AULA B107
3 E : 10.55 - 13.25 LAB. A210
 : 11.45 - 13.25 LAB. B219
3 F : 10.55 - 13.25 LAB. D011
4 H : 10.55 - 13.25 AULA CALABRONE
4 I : 15.20 - 16.10 AULA B204
4 L : 08.10 - 10.40 AULA CALABRONE
5 G : 10.55 - 12.35 AULA D004
5 G/N : 16.20 - 17.10 AULA B311
5 OD : 14.30 - 15.20 AULA B204
"""),
  "n_note": 2,
}

GT["img3"] = {
  "giorno": "VENERDÌ", "numero": 29, "mese": "MAGGIO",
  "entrate": [box("09.00", "1C 2C 5B"), box("09.50", "1B 1G 1P 2I 3A 3E 4F 4N 5MAT")],
  "uscite": [box("10.40", "1OD"), box("11.45", "1A 2F 2P 3C 3D 3H 5C"), box("12.35", "1D 2A 5D")],
  "senza_lezioni_pomeridiane": [],
  "cambi_aula": righe("""
1 B : 11.45 - 12.35 LAB. B212
1 C : 11.45 - 13.25 AULA MAGNA
1 D : 10.55 - 12.35 AULA MAGNA
1 E : 09.50 - 10.40 AULA B108
1 I : 11.45 - 13.25 AULA MAGNA
2 E : 08.10 - 09.00 AULA B201
 : 09.00 - 09.50 AULA B101
 : 11.45 - 13.25 LAB. B219
2 L : 08.10 - 09.50 LAB. B221
 : 10.55 - 13.25 AULA MAGNA
2 OD : 09.00 - 10.40 AULA CALABRONE
4 P : 08.10 - 10.40 LAB. B219
5 E : 08.10 - 09.50 AULA B115
5 G : 08.10 - 11.45 AULA A110
5 N : 11.45 - 13.25 AULA A110
5 OD : 11.45 - 13.25 AULA B204
"""),
  "n_note": 1,
}

GT["img4"] = {
  "giorno": "MERCOLEDÌ", "numero": 13, "mese": "MAGGIO",
  "entrate": [box("09.00", "1D 3J 3OD"), box("09.50", "1G 3T 4P 5A 5D")],
  "uscite": [box("11.45", "1C 1I 3A 4D"), box("12.35", "1E 1P 3J"), box("16.10", "1OD 2P 4MAT")],
  "senza_lezioni_pomeridiane": [{"classi": ["2OD", "3J"]}],
  "cambi_aula": righe("""
1 A : 08.10 - 09.00 AULA B007
1 B : 10.55 - 11.45 AULA B209
1 C : 09.50 - 11.45 AULA B108
1 I : 09.50 - 11.45 AULA B207
1 L : 09.50 - 11.45 AULA 201
1 MAQ2 : 10.55 - 11.45 AULA B111
2 OD : 08.10 - 10.40 LAB. B219
3 I : 10.55 - 11.45 AULA B317
3 L : 08.10 - 13.25 AULA MAGNA
3 P : 10.55 - 13.25 AULA B004
4 D : 09.00 - 11.45 AULA 302
5 C : 09.50 - 11.45 AULA B112
5 E : 09.50 - 10.40 AULA B107
5 H : 10.55 - 11.45 AULA 301
5 I : 09.50 - 11.45 AULA B304
5 K : 09.50 - 11.45 AULA B013
5 L : 09.50 - 11.45 AULA B106
5 OD : 10.55 - 11.45 AULA B309
"""),
  "n_note": 5,
}

GT["img5"] = {
  "giorno": "VENERDÌ", "numero": 5, "mese": "GIUGNO",
  "entrate": [box("09.00", "2I")],
  "uscite": [], "senza_lezioni_pomeridiane": [],
  "cambi_aula": righe("""
1 OD : 09.50 - 10.40 AULA B113
1 P : 09.50 - 10.40 AULA B205
2 E : 10.55 - 12.35 TALVERA
3 P : 08.10 - 09.00 AULA D204
4 H* : 09.50 - 11.45 AULA D009
4 L* : 08.10 - 09.50 AULA A110
5 A* : 10.55 - 11.45 AULA B119
5 C* : 09.50 - 10.40 AULA B301
5 G* : 08.10 - 09.50 AULA D206
5 K : 08.10 - 09.50 AULA UDIENZE
5 L : 09.50 - 11.45 TALVERA
"""),
  "n_note": 1,
}

GT["img6"] = {
  "giorno": "GIOVEDÌ", "numero": 7, "mese": "MAGGIO",
  "entrate": [box("09.00", "3F 4J 5MAT"), box("09.50", "1A 3H 3D 4F"), box("15.20", "3MAT 5B 5MAT")],
  "uscite": [box("11.45", "3C/T 3L 3P 4N"), box("12.35", "1F 3E"), box("15.20", "3I 4I"),
             box("16.10", "1MAQ2 4F 4J 5I")],
  "senza_lezioni_pomeridiane": [],
  "cambi_aula": righe("""
1 E : 09.50 - 11.45 LAB. B221
1 G : 15.20 - 16.10 LAB. B221
2 B : 09.50 - 11.45 AULA B016
2 F : 09.50 - 10.40 AULA B307
3 A : 08.10 - 10.40 AULA D205
3 L : 08.10 - 13.25 AULA MAGNA
4 H : 09.50 - 10.40 AULA B115
5 B : 11.45 - 13.25 AULA B016
5 E : 08.10 - 13.25 LAB. D008
5 I : 09.50 - 11.45 AULA B204
5 J : 08.10 - 13.25 AULA A106
5 K : 08.10 - 13.25 LAB. D008
5 MAT : 12.35 - 13.25 AULA B106
"""),
  "n_note": 3,
}

d = Path(__file__).parent
for k, v in GT.items():
    # i marcatori (*) non fanno parte della classe nel confronto
    for r in v["cambi_aula"]:
        if r["classe"]:
            r["classe"] = r["classe"].replace("*", "")
    (d / f"{k}.json").write_text(json.dumps(v, ensure_ascii=False, indent=2), encoding="utf-8")
print("scritti:", ", ".join(sorted(GT)))
