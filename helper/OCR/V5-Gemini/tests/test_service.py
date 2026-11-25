"""Test del servizio HTTP (service.py) senza rete: Gemini è finto. Servono fastapi e httpx."""
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import numpy as np
from fastapi.testclient import TestClient

import service
from gemini_ocr.engine import GeminiError, GeminiUnavailable, InvalidKey, QuotaExhausted

TOKEN = "x" * 40
KEY = "chiave-segreta-di-prova"
AUTH = {"Authorization": f"Bearer {TOKEN}"}
ENV = {"OCR_TOKEN": TOKEN, "GEMINI_API_KEY": KEY, "OCR_MAX_IMAGE_MB": "1"}


def png_bytes():
    ok, data = cv2.imencode(".png", np.full((40, 60, 3), 255, np.uint8))
    assert ok
    return data.tobytes()


def settings(**extra):
    with mock.patch.dict(os.environ, {**ENV, **extra}, clear=False):
        return service.Settings()


class TestSettings(unittest.TestCase):
    def test_token_e_chiave_obbligatori(self):
        for env in ({"OCR_TOKEN": "corto"}, {"GEMINI_API_KEY": ""}):
            with self.subTest(env=env), self.assertRaises(SystemExit):
                settings(**env)

    def test_modelli_da_ambiente(self):
        s = settings(GEMINI_MODELS="a, b")
        self.assertEqual(s.cfg["gemini"]["models"], ["a", "b"])
        self.assertFalse(s.cfg["salva_ritagli"])


class TestService(unittest.TestCase):
    def setUp(self):
        self.settings = settings()
        self.app = service.create_app(self.settings, start_engine=False)
        self.client = TestClient(self.app)
        self.calls = []

        def fake_process(img, name, engine, cfg, outdir=None, log=None):
            self.calls.append((name, img.shape, outdir, cfg["salva_ritagli"]))
            return {"schema_versione": 2, "_source": name, "n_voci": 0, "motore": {"modello": "m"}}

        patcher = mock.patch.object(service, "processa_array", fake_process)
        patcher.start()
        self.addCleanup(patcher.stop)

    def ready(self):
        self.app.state.ocr.engine = object()

    def post(self, body=None, nome="a.png", headers=AUTH):
        return self.client.post("/ocr", params={"nome": nome}, content=png_bytes() if body is None else body,
                                headers=headers)

    def test_health_senza_token(self):
        self.assertEqual(self.client.get("/health").json(), {"status": "starting"})
        self.ready()
        self.assertEqual(self.client.get("/health").json(), {"status": "ok"})

    def test_token_sbagliato_o_assente(self):
        self.ready()
        self.assertEqual(self.post(headers={}).status_code, 401)
        self.assertEqual(self.post(headers={"Authorization": "Bearer " + "y" * 40}).status_code, 401)
        self.assertEqual(self.calls, [])

    def test_lettura(self):
        self.ready()
        r = self.post(nome="15128149_1_2_NOV_16_STU_1.png")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["_source"], "15128149_1_2_NOV_16_STU_1.png")
        self.assertEqual(self.calls, [("15128149_1_2_NOV_16_STU_1.png", (40, 60, 3), None, False)])

    def test_stessa_immagine_letta_una_volta(self):
        self.ready()
        primo = self.post(nome="cartellone.png")
        secondo = self.post(nome="cartellone.png")
        self.assertEqual((primo.status_code, secondo.status_code), (200, 200))
        self.assertEqual(primo.json(), secondo.json())
        self.assertEqual(len(self.calls), 1)                 # la seconda volta niente Gemini
        self.post(nome="altro.png")                          # nome diverso = unit_id diversi: si rilegge
        other = np.full((40, 60, 3), 0, np.uint8)
        self.post(cv2.imencode(".png", other)[1].tobytes(), nome="cartellone.png")   # contenuto diverso
        self.assertEqual(len(self.calls), 3)

    def test_risultato_in_memoria_anche_senza_motore(self):
        self.ready()
        self.post(nome="cartellone.png")
        self.app.state.ocr.engine = None                     # es. dopo un problema con la chiave
        self.assertEqual(self.post(nome="cartellone.png").status_code, 200)

    def test_errori_non_restano_in_memoria(self):
        self.ready()
        with mock.patch.object(service, "processa_array", mock.Mock(side_effect=GeminiUnavailable("503"))), \
                self.assertLogs("skedoo.ocr"):
            self.assertEqual(self.post().status_code, 503)
        self.assertEqual(self.post().status_code, 200)
        self.assertEqual(len(self.calls), 1)

    def test_memoria_limitata(self):
        state = service.State()
        for i in range(service.CACHE_SIZE + 5):
            state.remember(str(i), {"i": i})
        self.assertEqual(len(state.results), service.CACHE_SIZE)
        self.assertIsNone(state.cached("0"))
        risultato = state.cached(str(service.CACHE_SIZE + 4))
        risultato["i"] = "modificato"                       # copia: la memoria non cambia
        self.assertEqual(state.cached(str(service.CACHE_SIZE + 4)), {"i": service.CACHE_SIZE + 4})

    def test_non_pronto(self):
        r = self.post()
        self.assertEqual(r.status_code, 503)
        self.assertEqual(r.headers["retry-after"], "60")

    def test_input_non_validi(self):
        self.ready()
        self.assertEqual(self.post(b"non un'immagine").status_code, 422)
        self.assertEqual(self.post(nome="script.sh").status_code, 422)
        self.assertEqual(self.post(b"").status_code, 422)
        self.assertEqual(self.post(b"0" * (1024 * 1024 + 1)).status_code, 413)
        self.assertEqual(self.calls, [])

    def test_errori_di_gemini(self):
        self.ready()
        casi = ((QuotaExhausted("quota"), 503, "Quota Gemini esaurita, riprova più tardi"),
                (GeminiUnavailable("503"), 503, "Gemini sovraccarico o non raggiungibile, riprova più tardi"),
                (GeminiError(f"dettaglio {KEY}"), 502, "Lettura con Gemini fallita"),
                (RuntimeError("/app/segreto"), 500, "Lettura dell'immagine fallita"))
        for exc, status, detail in casi:
            with self.subTest(exc=type(exc).__name__), \
                    mock.patch.object(service, "processa_array", mock.Mock(side_effect=exc)), \
                    self.assertLogs("skedoo.ocr"):
                r = self.post()
            self.assertEqual(r.status_code, status)
            self.assertEqual(r.json(), {"detail": detail})
            self.assertNotIn(KEY, r.text)
        self.assertEqual(r.headers.get("retry-after"), None)

    def test_safe_name(self):
        self.assertEqual(service.safe_name("../../etc/passwd.png"), "passwd.png")
        self.assertEqual(service.safe_name("..\\..\\x y.JPG"), "x_y.JPG")
        self.assertIsNone(service.safe_name(".png"))
        self.assertIsNone(service.safe_name("file"))


class TestPrepare(unittest.TestCase):
    def run_prepare(self, results):
        s, state = settings(), service.State()
        engine = mock.Mock(models=["m1"])
        engine.verifica.side_effect = results
        with mock.patch.object(service, "make_engine", lambda _: engine):
            service.prepare(s, state, retry_seconds=0, invalid_key_seconds=0)
        return state, engine

    def test_pronto_dopo_la_verifica(self):
        state, engine = self.run_prepare([OSError("rete"), InvalidKey("chiave"), ["m1"]])
        self.assertIs(state.engine, engine)
        self.assertEqual(engine.verifica.call_count, 3)


if __name__ == "__main__":
    unittest.main()
