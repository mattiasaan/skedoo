"""Il JSON della V5 deve essere quello della V4: stessa immagine, stesso testo letto -> stesso risultato.
Usa le immagini di ../V4-AI/test_images e motori finti (nessuna rete, nessun Ollama)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gemini_ocr import pipeline as G
from gemini_ocr.config import load_config
from gemini_ocr.v4 import V4_DIR
from gemini_ocr.v4 import pipeline as V4

IMAGES = sorted((V4_DIR / "test_images").glob("*.*"))[:4]

TESTI = {
    "titolo": ["LUNEDÌ 16 NOVEMBRE"],
    "riga": ["3 C/T : 11.45 - 13.25 AULA B207"],
    "riquadro": ["ENTRA ALLE 09.00", "1 F + 4 J*", "* posticipa 1° a 2°"],
    "info": ["DOCENTI ASSENTI", "ROSSI"],
}


def testo(uid, kind):
    """Testo finto ma vario: alcune righe con un'altra classe per esercitare i controlli tra voci."""
    if kind == "riga" and uid.endswith(("1", "5")):
        return ["1 A : 08.00 - 09.00 AULA D205"]
    return list(TESTI[kind])


class FintoV4:
    """Motore della V4: un ritaglio alla volta."""
    name, model, scale = "finto", "finto", 2
    kinds = {"riga", "riquadro", "titolo", "info"}

    def __init__(self):
        self.uids = []

    def supports(self, kind):
        return kind in self.kinds

    def read(self, crop, kind):
        return testo(self._uid, kind)


class FintoGemini:
    name, model, scale = "finto", "finto", 2
    kinds = FintoV4.kinds

    def __init__(self, mancanti=()):
        self.chiamate = 0
        self.mancanti = set(mancanti)

    def supports(self, kind):
        return kind in self.kinds

    def read_batch(self, items):
        self.chiamate += 1
        return {uid: testo(uid, kind) for uid, kind, _ in items if uid not in self.mancanti}


def senza_tempo(res):
    res = dict(res)
    res.pop("estratto_il")
    return res


@unittest.skipUnless(IMAGES, "nessuna immagine in V4-AI/test_images")
class TestStessoJsonDellaV4(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config()
        self.cfg["anno"] = 2026
        self.cfg["salva_ritagli"] = False

    def v4(self, img):
        engine = FintoV4()
        original = V4.leggi_unita

        def leggi(unit, eng, log=print):        # il motore finto deve sapere quale unità legge
            engine._uid = unit.uid
            return original(unit, eng, log=log)

        V4.leggi_unita = leggi
        try:
            return V4.processa_immagine(img, engine, self.cfg, outdir=None, log=lambda m: None)
        finally:
            V4.leggi_unita = original

    def test_stesso_json(self):
        for img in IMAGES:
            with self.subTest(img=img.name):
                engine = FintoGemini()
                atteso = senza_tempo(self.v4(img))
                ottenuto = senza_tempo(G.processa_immagine(img, engine, self.cfg, log=lambda m: None))
                self.assertEqual(ottenuto, atteso)
                self.assertEqual(engine.chiamate, 1)        # un cartellone = una richiesta
                self.assertGreater(ottenuto["n_voci"], 0)

    def test_unita_non_restituita_diventa_bassa(self):
        img = IMAGES[0]
        cfg = self.cfg
        units = G.costruisci_unita(__import__("cv2").imread(str(img)), img.stem, cfg)
        righe = [u.uid for u in units if u.kind == "riga"]
        self.assertTrue(righe)
        res = G.processa_immagine(img, FintoGemini(mancanti={righe[0]}), cfg, log=lambda m: None)
        voce = next(v for v in res["cambi_aula"] if v["unit_id"] == righe[0])
        self.assertEqual(voce["affidabilita"], "bassa")
        self.assertIn("lettura_fallita", voce["motivi"])
        self.assertEqual(res["stato"], "da_verificare")

    def test_salva_ritagli(self):
        import tempfile
        img = IMAGES[0]
        cfg = dict(self.cfg, salva_ritagli=True)
        with tempfile.TemporaryDirectory() as out:
            res = G.processa_immagine(img, FintoGemini(), cfg, outdir=out, log=lambda m: None)
            self.assertTrue(any(Path(out, f"{img.stem}_ritagli").iterdir()))
        for voce in res["da_verificare"]:
            self.assertTrue(voce["ritaglio"].startswith(f"{img.stem}_ritagli/"))


class TestTitoloAbbreviato(unittest.TestCase):
    def test_espandi_giorno(self):
        casi = {"MER. 25 NOVEMBRE": "MERCOLEDÌ 25 NOVEMBRE", "mar 3 marzo": "MARTEDÌ 3 marzo",
                "GIO.26 NOVEMBRE": "GIOVEDÌ 26 NOVEMBRE", "VEN 27 NOVEMBRE": "VENERDÌ 27 NOVEMBRE",
                "SAB. 28 NOVEMBRE": "SABATO 28 NOVEMBRE", "MERC. 25 NOVEMBRE": "MERCOLEDÌ 25 NOVEMBRE",
                "LUNEDÌ 16 NOVEMBRE": "LUNEDÌ 16 NOVEMBRE",       # già per intero: invariato
                "LUNEDI 16 NOVEMBRE": "LUNEDI 16 NOVEMBRE",
                "MA 3 MARZO": "MA 3 MARZO",                       # troppo corto / ambiguo: invariato
                "25 NOVEMBRE": "25 NOVEMBRE", "": ""}
        for testo, atteso in casi.items():
            with self.subTest(testo=testo):
                self.assertEqual(G.espandi_giorno(testo), atteso)

    def test_titolo_abbreviato_e_affidabile(self):
        cfg = dict(load_config(), anno=2026)
        from gemini_ocr.v4 import parse as P
        valuta = V4.valuta
        t = P.parse_title(G.espandi_giorno("MER. 25 NOVEMBRE"), cfg)
        self.assertEqual((t.giorno, t.iso), ("MERCOLEDÌ", "2026-11-25"))
        self.assertEqual(valuta(t).affidabilita, "alta")
        sbagliato = P.parse_title(G.espandi_giorno("GIO. 25 NOVEMBRE"), cfg)   # 25/11/2026 è mercoledì
        self.assertEqual(valuta(sbagliato).affidabilita, "bassa")


class TestColoreRiquadri(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config()

    def test_no_lez_di_qualsiasi_colore(self):
        for hint in ("bianco", "giallo", "chiaro"):
            with self.subTest(hint=hint):
                r = G.parse_riquadro(["NO LEZ. POM.", "4 E"], hint, self.cfg)
                self.assertEqual((r.kind, [c.classe for c in r.classi]), ("nolez", ["4E"]))
                self.assertEqual(V4.valuta(r).affidabilita, "alta")

    def test_entra_esce_col_colore_sbagliato_restano_bassa(self):
        r = G.parse_riquadro(["ESCE ALLE 12.35", "1 D"], "giallo", self.cfg)
        self.assertIn("colore_giallo_incoerente_con_esce", r.problems)
        self.assertEqual(V4.valuta(r).affidabilita, "bassa")
        r = G.parse_riquadro(["ENTRA ALLE 09.00", "1 D"], "bianco", self.cfg)
        self.assertEqual(V4.valuta(r).affidabilita, "bassa")


class TestConfig(unittest.TestCase):
    def test_config_della_v4_piu_gemini(self):
        cfg = load_config()
        self.assertTrue(cfg["orari_noti"])                   # dalla V4
        self.assertTrue(cfg["classi_valide"])                # elenchi della V4
        self.assertTrue(cfg["gemini"]["models"])
        self.assertNotIn("ollama", cfg)


if __name__ == "__main__":
    unittest.main()
