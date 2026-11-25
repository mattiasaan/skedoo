"""Test del client Gemini senza rete: le risposte HTTP sono finte.
Esegui dalla cartella V5-Gemini:  python -m unittest discover -s tests -v"""
import io
import json
import sys
import unittest
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from gemini_ocr.engine import GeminiEngine, GeminiError, InvalidKey, QuotaExhausted, estrai_unita

KEY = "chiave-di-prova"


def crop():
    return np.full((20, 60, 3), 200, np.uint8)


def risposta(unita, thought=None):
    parts = [{"text": "ragionamento", "thought": True}] if thought else []
    parts.append({"text": json.dumps({"unita": unita})})
    return {"candidates": [{"content": {"parts": parts}, "finishReason": "STOP"}]}


def http_error(code, body):
    return urllib.error.HTTPError("https://x", code, "err", {}, io.BytesIO(json.dumps(body).encode()))


def quota(per_day, delay="7s"):
    return http_error(429, {"error": {"code": 429, "message": "Resource has been exhausted", "details": [
        {"@type": "type.googleapis.com/google.rpc.QuotaFailure", "violations": [
            {"quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier" if per_day
             else "GenerateRequestsPerMinutePerProjectPerModel-FreeTier"}]},
        {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": delay}]}})


class FakeEngine(GeminiEngine):
    """Motore con _request finto: `script` è una lista di risposte (dict) o eccezioni, consumate in ordine."""

    def __init__(self, script, **kw):
        kw.setdefault("models", ["m1", "m2"])
        self.sleeps = []
        super().__init__(KEY, sleep=self.sleeps.append, **kw)
        self.script = list(script)
        self.calls = []

    def _request(self, method, path, payload=None):
        self.calls.append((method, path, payload))
        item = self.script.pop(0)
        if callable(item):
            item = item(payload)
        if isinstance(item, Exception):
            raise item
        return item


def eco(payload):
    """Risposta che restituisce per ogni ritaglio il suo id come testo."""
    ids = [p["text"].split(" ")[0] for p in payload["contents"][0]["parts"] if p.get("text", "").startswith("u")]
    return risposta([{"id": i, "righe": [f"testo {i}"]} for i in ids])


class TestGeminiEngine(unittest.TestCase):
    def test_una_richiesta_per_tutti_i_ritagli(self):
        e = FakeEngine([eco])
        out = e.read_batch([("a", "riga", crop()), ("b", "riquadro", crop()), ("c", "titolo", crop())])
        self.assertEqual(out, {"a": ["testo u01"], "b": ["testo u02"], "c": ["testo u03"]})
        self.assertEqual(len(e.calls), 1)
        method, path, payload = e.calls[0]
        self.assertEqual((method, path), ("POST", "models/m1:generateContent"))
        self.assertNotIn(KEY, path)                      # la chiave va nell'header, mai nell'URL
        parts = payload["contents"][0]["parts"]
        self.assertEqual(sum("inline_data" in p for p in parts), 3)
        self.assertEqual(payload["generationConfig"]["responseMimeType"], "application/json")
        self.assertIn("responseSchema", payload["generationConfig"])

    def test_header_con_la_chiave(self):
        e = GeminiEngine(KEY, ["m1"])
        seen = {}

        class Resp(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def fake_urlopen(req, timeout):
            seen["url"], seen["key"] = req.full_url, req.get_header("X-goog-api-key")
            return Resp(json.dumps({"models": [{"name": "models/m1"}]}).encode())

        from unittest import mock
        with mock.patch("urllib.request.urlopen", fake_urlopen):
            self.assertEqual(e.verifica(), ["m1"])
        self.assertEqual(seen["key"], KEY)
        self.assertNotIn(KEY, seen["url"])

    def test_unita_mancante_e_id_sconosciuto(self):
        e = FakeEngine([risposta([{"id": "u02", "righe": ["x"]}, {"id": "u99", "righe": ["y"]}])])
        self.assertEqual(e.read_batch([("a", "riga", crop()), ("b", "riga", crop())]), {"b": ["x"]})

    def test_blocchi(self):
        e = FakeEngine([eco, eco, eco], max_unita_per_richiesta=2)
        out = e.read_batch([(k, "riga", crop()) for k in "abcde"])
        self.assertEqual(len(e.calls), 3)
        self.assertEqual(out["e"], ["testo u05"])     # gli id proseguono tra un blocco e l'altro

    def test_limite_al_minuto_aspetta_e_riprova(self):
        e = FakeEngine([quota(per_day=False, delay="7s"), eco])
        self.assertEqual(e.read_batch([("a", "riga", crop())]), {"a": ["testo u01"]})
        self.assertEqual(e.sleeps, [7.0])
        self.assertEqual(e.model, "m1")

    def test_quota_giornaliera_passa_al_modello_successivo(self):
        e = FakeEngine([quota(per_day=True), eco, eco])
        e.read_batch([("a", "riga", crop())])
        self.assertEqual([c[1] for c in e.calls], ["models/m1:generateContent", "models/m2:generateContent"])
        self.assertEqual(e.model, "m2")
        self.assertEqual(e.sleeps, [])
        e.read_batch([("a", "riga", crop())])           # m1 resta escluso per un po'
        self.assertEqual(e.calls[-1][1], "models/m2:generateContent")

    def test_modello_inesistente(self):
        e = FakeEngine([http_error(404, {"error": {"message": "not found"}}), eco])
        e.read_batch([("a", "riga", crop())])
        self.assertEqual(e.model, "m2")

    def test_tutte_le_quote_esaurite(self):
        e = FakeEngine([quota(per_day=True), quota(per_day=True)])
        with self.assertRaises(QuotaExhausted):
            e.read_batch([("a", "riga", crop())])

    def test_chiave_non_valida_senza_tentativi(self):
        body = {"error": {"code": 400, "message": "API key not valid. Please pass a valid API key.",
                          "details": [{"reason": "API_KEY_INVALID"}]}}
        e = FakeEngine([http_error(400, body)])
        with self.assertRaises(InvalidKey):
            e.read_batch([("a", "riga", crop())])
        self.assertEqual(len(e.calls), 1)

    def test_errori_del_servizio_riprova_poi_errore(self):
        e = FakeEngine([http_error(503, {}), urllib.error.URLError("rete"), http_error(500, {})], max_tentativi=3)
        with self.assertRaises(GeminiError) as ctx:
            e.read_batch([("a", "riga", crop())])
        self.assertNotIsInstance(ctx.exception, QuotaExhausted)
        self.assertEqual(e.sleeps, [2.0, 4.0])
        self.assertNotIn(KEY, str(ctx.exception))

    def test_attesa_massima(self):
        e = FakeEngine([quota(per_day=False, delay="3600s"), eco], max_attesa_s=90)
        e.read_batch([("a", "riga", crop())])
        self.assertEqual(e.sleeps, [90])

    def test_generation_config_extra(self):
        e = FakeEngine([eco], generation_config={"temperature": 0})
        e.read_batch([("a", "riga", crop())])
        self.assertEqual(e.calls[0][2]["generationConfig"]["temperature"], 0)


class TestEstraiUnita(unittest.TestCase):
    def test_salta_il_ragionamento_e_le_righe_vuote(self):
        r = risposta([{"id": "U01", "righe": ["a", " ", "b"]}], thought=True)
        self.assertEqual(estrai_unita(r), {"u01": ["a", "b"]})

    def test_json_con_testo_intorno(self):
        r = {"candidates": [{"content": {"parts": [{"text": 'ecco: {"unita": [{"id": "u01", "righe": []}]} fine'}]}}]}
        self.assertEqual(estrai_unita(r), {"u01": []})

    def test_risposte_non_valide(self):
        for r in ({"promptFeedback": {"blockReason": "SAFETY"}}, {"candidates": []},
                  {"candidates": [{"content": {"parts": [{"text": "non json"}]}, "finishReason": "MAX_TOKENS"}]}):
            with self.assertRaises(GeminiError):
                estrai_unita(r)


if __name__ == "__main__":
    unittest.main()
