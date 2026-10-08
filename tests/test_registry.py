"""Contrato de novos modelos e preservação das regras de inferência."""

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline

from app import create_app
from prediction import ModelRegistry
from prediction.adapters import SklearnPipelineClassifier


class FixedProbabilityPipeline:
    # Não confiável vem primeiro: o adaptador não pode assumir a coluna 1.
    classes_ = np.array(["fake", "real"])

    def __init__(self, probability):
        self.probability = probability

    def predict_proba(self, texts):
        return np.tile([self.probability, 1 - self.probability], (len(texts), 1))


class ModelRegistryTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.models_dir = Path(directory.name)
        (self.models_dir / "KNN").mkdir()
        pipeline = make_pipeline(TfidfVectorizer(), KNeighborsClassifier(n_neighbors=1))
        pipeline.fit(
            [
                "oferta golpe senha",
                "boato falso prêmio",
                "anúncio oficial console",
                "evento confirmado lançamento",
            ],
            ["fake", "fake", "real", "real"],
        )
        artifact_path = self.models_dir / "KNN/modelo.joblib"
        joblib.dump(pipeline, artifact_path)
        self.settings = {
            "name": "KNN de teste",
            "family": "KNN",
            "version": "1",
            "artifact": "KNN/modelo.joblib",
            "adapter": "sklearn_pipeline",
            "positive_class": "fake",
            "delta": 0.2,
            "sha256": hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
        }
        self.manifest = {
            "schema_version": 2,
            "default_model": "knn_teste",
            "models": {"knn_teste": self.settings},
        }

    def load_registry(self):
        (self.models_dir / "manifest.json").write_text(json.dumps(self.manifest))
        return ModelRegistry.load(self.models_dir)

    def test_knn_entra_so_com_artefato_e_cadastro(self):
        registry = self.load_registry()
        client = create_app(registry).test_client()
        catalog = client.get("/api/models").json
        self.assertEqual(catalog["default_model"], "knn_teste")
        self.assertEqual(catalog["models"]["knn_teste"]["family"], "KNN")
        self.assertNotIn("metrics", catalog["models"]["knn_teste"])
        self.assertNotIn("artifact", catalog["models"]["knn_teste"])
        result = client.post(
            "/api/analyze",
            json={
                "text": "oferta golpe senha oferta golpe senha",
                "compare": True,
            },
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json["label"], "not_credible")
        self.assertEqual(result.json["probability"], 1.0)
        self.assertIsNone(result.json["coverage"])
        self.assertEqual(len(result.json["comparisons"]), 1)
        self.assertEqual(client.get("/api/health").json["model_id"], "knn_teste")

    def test_desativado_nao_carrega_nem_aparece_na_api(self):
        self.settings["enable"] = True
        self.manifest["models"]["desativado"] = {
            "enable": False,
            "artifact": "arquivo_ausente.joblib",
        }
        with patch("prediction.registry.joblib.load", wraps=joblib.load) as load:
            registry = self.load_registry()
            self.assertEqual(load.call_count, 1)
        client = create_app(registry).test_client()
        self.assertEqual(set(registry.models), {"knn_teste"})
        self.assertEqual(set(client.get("/api/models").json["models"]), {"knn_teste"})
        self.assertEqual(client.get("/api/health").json["model_count"], 1)
        payload = {"text": "oferta golpe senha oferta golpe senha", "compare": True}
        response = client.post("/api/analyze", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json["comparisons"]), 1)
        payload["model"] = "desativado"
        self.assertEqual(client.post("/api/analyze", json=payload).status_code, 400)
        # Reativar restaura a entrada sem qualquer mudança no código.
        self.manifest["models"]["desativado"] = dict(self.settings, enable=True)
        self.assertEqual(len(self.load_registry().models), 2)

    def test_rejeita_enable_que_nao_seja_booleano(self):
        for value in ["false", "true", 0, 1, None, []]:
            with self.subTest(value=value):
                self.settings["enable"] = value
                with self.assertRaisesRegex(ValueError, "enable"):
                    self.load_registry()

    def test_rejeita_padrao_desativado(self):
        self.settings["enable"] = False
        self.manifest["models"]["outro"] = dict(self.settings, enable=True)
        with self.assertRaisesRegex(ValueError, "default_model"):
            self.load_registry()

    def test_rejeita_todos_desativados(self):
        self.settings["enable"] = False
        with self.assertRaisesRegex(ValueError, "pelo menos um modelo"):
            self.load_registry()

    def test_classe_positiva_e_limites_da_abstencao(self):
        settings = dict(self.settings, delta=0.375)
        for probability, label in [
            (0.124, "credible"),
            (0.125, "credible"),
            (0.5, "abster"),
            (0.875, "not_credible"),
            (0.876, "not_credible"),
        ]:
            with self.subTest(probability=probability):
                model = SklearnPipelineClassifier(
                    "teste", settings, FixedProbabilityPipeline(probability)
                )
                result = model.analyze("texto")
                self.assertEqual(result["probability"], probability)
                self.assertEqual(result["label"], label)
        model = SklearnPipelineClassifier(
            "teste", dict(settings, delta=0), FixedProbabilityPipeline(0.5)
        )
        self.assertEqual(model.analyze("texto")["label"], "not_credible")

    def test_rejeita_cadastros_invalidos(self):
        original = copy.deepcopy(self.settings)
        for key, value in [
            ("adapter", "inexistente"),
            ("positive_class", "outra"),
            ("positive_class", None),
            ("delta", 0.5),
            ("delta", -0.1),
            ("delta", float("nan")),
            ("delta", True),
            ("sha256", "alterado"),
            ("artifact", "../fora.joblib"),
            ("artifact", "KNN/ausente.joblib"),
        ]:
            with self.subTest(key=key, value=value):
                self.manifest["models"]["knn_teste"] = dict(original, **{key: value})
                with self.assertRaisesRegex(ValueError, "knn_teste"):
                    self.load_registry()

    def test_rejeita_padrao_ausente(self):
        self.manifest["default_model"] = "outro"
        with self.assertRaisesRegex(ValueError, "default_model"):
            self.load_registry()

    def test_rejeita_arquivo_alterado_antes_de_desserializar(self):
        (self.models_dir / self.settings["artifact"]).write_bytes(b"arquivo trocado")
        with patch("prediction.registry.joblib.load") as load:
            with self.assertRaisesRegex(ValueError, "SHA256"):
                self.load_registry()
            load.assert_not_called()

    def test_rejeita_probabilidades_invalidas(self):
        for probability in [float("nan"), float("inf"), -0.1, 1.1]:
            model = SklearnPipelineClassifier(
                "teste", self.settings, FixedProbabilityPipeline(probability)
            )
            with self.subTest(probability=probability), self.assertRaises(ValueError):
                model.analyze("texto")

    def test_rejeita_estimador_sem_pipeline_textual(self):
        estimator = KNeighborsClassifier(n_neighbors=1).fit([[0], [1]], ["fake", "real"])
        path = self.models_dir / self.settings["artifact"]
        joblib.dump(estimator, path)
        self.settings["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError, "knn_teste"):
            self.load_registry()


if __name__ == "__main__":
    unittest.main()
