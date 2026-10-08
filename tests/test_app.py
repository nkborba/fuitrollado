import hashlib
import json
import re
import unittest
from pathlib import Path

import app as server
from prediction import normalize

ROOT = Path(__file__).resolve().parents[1]


class SiteTests(unittest.TestCase):
    def setUp(self):
        self.app = server.create_app(server.app.extensions["model_registry"])
        self.client = self.app.test_client()
        self.models = self.app.extensions["model_registry"].models

    def test_previsoes_preservadas(self):
        fixtures = json.loads((ROOT / "tests/previsoes_referencia.json").read_text())
        for row in fixtures:
            with self.subTest(model=row["model"], text=row["text"]):
                response = self.client.post(
                    "/api/analyze", json={"text": row["text"], "model": row["model"]}
                )
                if row["model"] not in self.models:
                    self.assertEqual(response.status_code, 400)
                    continue
                self.assertEqual(response.status_code, 200)
                self.assertAlmostEqual(response.json["probability"], row["probability"], places=12)

    def test_artefatos(self):
        checks = json.loads((ROOT / "models/LR/validacao_exportacao.json").read_text())
        for filename, digest in checks["sha256"].items():
            self.assertEqual(
                hashlib.sha256((ROOT / "models/LR" / filename).read_bytes()).hexdigest(), digest
            )

    def test_comparacao(self):
        r = self.client.post(
            "/api/analyze",
            json={
                "text": "O governo brasileiro proibiu GTA6.",
                "compare": True,
                "model": "normalizado_char",
            },
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json["comparisons"]), len(self.models))
        self.assertEqual(r.json["model_id"], "normalizado_char")
        self.assertEqual(r.json["label"], "abster")
        for kind in ("normalizado", "normalizado_char"):
            if kind not in self.models:
                continue
            model = self.models[kind]
            a, b = model.predict_proba(
                ["O governo brasileiro proibiu GTA6.", "O governo brasileiro proibiu GTA 6."]
            )
            self.assertEqual(a, b)

    def test_validacao(self):
        for data in [
            [],
            {"text": None},
            {"text": "curto"},
            {"text": "x" * 5001},
            {"text": "O governo brasileiro proibiu GTA6.", "model": []},
            {"text": "O governo brasileiro proibiu GTA6.", "model": "outro"},
            {"text": "O governo brasileiro proibiu GTA6.", "compare": "true"},
        ]:
            self.assertEqual(self.client.post("/api/analyze", json=data).status_code, 400)
        self.assertEqual(
            self.client.post("/api/analyze", data="{", content_type="application/json").status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                "/api/analyze", data="x" * 33000, content_type="application/json"
            ).status_code,
            413,
        )

    def test_vocabulario_desconhecido(self):
        for kind in self.models:
            r = self.client.post(
                "/api/analyze", json={"text": "𐀀𐀁𐀂 𐀃𐀄𐀅 𐀆𐀇𐀈 𐀉𐀊𐀋 𐀌𐀍𐀎 𐀏𐀐𐀑", "model": kind}
            )
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.json["label"], "abster")
            self.assertIsNone(r.json["probability"])

    def test_estaticos_e_isolamento(self):
        for path in (
            "/",
            "/style.css",
            "/app.js",
            "/config.js",
            "/assets/03-gamer-neutro.png",
            "/api/health",
            "/api/models",
        ):
            r = self.client.get(path)
            self.assertEqual(r.status_code, 200, path)
            r.close()
        for path in (
            "/models/LR/atual.joblib",
            "/app.py",
            "/../models/LR/atual.joblib",
            "/%2e%2e/models/LR/atual.joblib",
        ):
            self.assertEqual(self.client.get(path).status_code, 404, path)

    def test_pages_paths(self):
        for filename in ("index.html", "style.css"):
            text = (ROOT / "web" / filename).read_text()
            self.assertNotRegex(text, r"""(?:src=|href=|url\()["']/""")
        html = (ROOT / "web/index.html").read_text()
        for asset in re.findall(r'src="\./([^\"]+)"', html):
            self.assertTrue((ROOT / "web" / asset).is_file(), asset)

    def test_cors(self):
        old = self.app.config["ALLOWED_ORIGINS"]
        self.app.config["ALLOWED_ORIGINS"] = {"https://nkborba.github.io"}
        try:
            r = self.client.options(
                "/api/analyze",
                headers={
                    "Origin": "https://nkborba.github.io",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type",
                },
            )
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.headers["Access-Control-Allow-Origin"], "https://nkborba.github.io")
            r = self.client.get("/api/models", headers={"Origin": "https://outro.example"})
            self.assertNotIn("Access-Control-Allow-Origin", r.headers)
        finally:
            self.app.config["ALLOWED_ORIGINS"] = old

    def test_normalizacao(self):
        self.assertEqual(normalize("GTA6"), normalize("GTA 6"))
        self.assertNotEqual(normalize("GTA5"), normalize("GTA6"))
        self.assertIn("não", normalize("NÃO proibiu GTA6"))


if __name__ == "__main__":
    unittest.main()
