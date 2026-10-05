"""Adapta os formatos de artefato à resposta comum da API."""

from abc import ABC, abstractmethod

import numpy as np
from scipy.sparse import hstack

from .text import clean, normalize


class TextClassifier(ABC):
    """A probabilidade retornada sempre corresponde a não confiável."""

    def __init__(self, model_id: str, settings: dict):
        self.model_id = model_id
        self.name = settings["name"]
        self.version = settings["version"]
        self.delta = settings["delta"]

    @abstractmethod
    def predict_proba(self, texts: list[str]) -> np.ndarray:
        """Retorna uma probabilidade por texto, na ordem recebida."""

    def coverage(self, text: str) -> dict | None:
        # Pipelines externos podem ter representações que não usam vocabulário.
        return None

    def analyze(self, text: str) -> dict:
        coverage = self.coverage(text)
        result = {
            "model_id": self.model_id,
            "name": self.name,
            "model": self.version,
            "delta": self.delta,
            "coverage": coverage,
        }
        if coverage and not coverage["representation_nonzero"]:
            return dict(result, label="abster", probability=None, reason="unknown_vocabulary")

        probability = float(self.predict_proba([text])[0])
        if not np.isfinite(probability) or not 0 <= probability <= 1:
            raise ValueError(f"{self.model_id}: probabilidade inválida.")
        if abs(probability - 0.5) < self.delta:
            label = "abster"
        else:
            label = "not_credible" if probability >= 0.5 else "credible"
        return dict(result, label=label, probability=probability)


class LegacyLRClassifier(TextClassifier):
    """Mantém a inferência dos estudos 09/10 sem retreinar os estimadores."""

    def __init__(self, model_id: str, settings: dict, artifact: dict):
        super().__init__(model_id, settings)
        required = {
            "word",
            "char",
            "lr",
            "calibrator",
            "calibration_input",
            "kind",
            "delta",
            "version",
        }
        if not isinstance(artifact, dict) or not required <= artifact.keys():
            raise ValueError(f"{model_id}: artefato legacy_lr incompleto.")
        if (
            artifact["kind"] != model_id
            or artifact["delta"] != self.delta
            or artifact["version"] != self.version
        ):
            raise ValueError(f"{model_id}: cadastro difere do artefato LR.")
        if artifact["calibration_input"] not in {"logit_probability", "decision_function"}:
            raise ValueError(f"{model_id}: entrada de calibração desconhecida.")
        self.artifact = artifact
        self.preprocess = (
            normalize if artifact["kind"] in {"normalizado", "normalizado_char"} else clean
        )

    def prepare(self, texts: list[str]) -> list[str]:
        return [self.preprocess(text) for text in texts]

    def matrix(self, texts: list[str]):
        prepared = self.prepare(texts)
        word_matrix = self.artifact["word"].transform(prepared)
        char_vectorizer = self.artifact["char"]
        if char_vectorizer is None:
            return word_matrix
        # O peso dos blocos precisa ser idêntico ao usado no treinamento.
        return hstack([word_matrix, char_vectorizer.transform(prepared)], format="csr") / np.sqrt(2)

    def predict_proba(self, texts: list[str]) -> np.ndarray:
        matrix = self.matrix(texts)
        classifier = self.artifact["lr"]
        if self.artifact["calibration_input"] == "logit_probability":
            probabilities = np.clip(classifier.predict_proba(matrix)[:, 1], 1e-6, 1 - 1e-6)
            scores = np.log(probabilities / (1 - probabilities))
        else:
            scores = classifier.decision_function(matrix)
        return self.artifact["calibrator"].predict_proba(scores[:, None])[:, 1]

    def coverage(self, text: str) -> dict:
        vectorizer = self.artifact["word"]
        terms = set(vectorizer.build_analyzer()(self.prepare([text])[0]))
        known_terms = terms & vectorizer.vocabulary_.keys()
        return {
            "known_terms": len(known_terms),
            "total_terms": len(terms),
            "word_coverage": len(known_terms) / len(terms) if terms else 0.0,
            "representation_nonzero": bool(self.matrix([text]).nnz),
        }


class SklearnPipelineClassifier(TextClassifier):
    """Recebe um pipeline binário já ajustado, incluindo seu pré-processamento."""

    def __init__(self, model_id: str, settings: dict, artifact):
        super().__init__(model_id, settings)
        if not callable(getattr(artifact, "predict_proba", None)):
            raise ValueError(f"{model_id}: o pipeline precisa implementar predict_proba.")
        classes = np.asarray(getattr(artifact, "classes_", []))
        if classes.ndim != 1 or len(classes) != 2:
            raise ValueError(f"{model_id}: esperado classificador binário treinado com classes_.")
        positive_class = settings.get("positive_class")
        matches = [index for index, label in enumerate(classes.tolist()) if label == positive_class]
        if len(matches) != 1:
            raise ValueError(f"{model_id}: positive_class não corresponde às classes do pipeline.")
        self.positive_index = matches[0]
        self.pipeline = artifact

    def predict_proba(self, texts: list[str]) -> np.ndarray:
        probabilities = np.asarray(self.pipeline.predict_proba(texts), dtype=float)
        if probabilities.shape != (len(texts), 2):
            raise ValueError(
                f"{self.model_id}: predict_proba deve retornar duas colunas por texto."
            )
        if (
            not np.isfinite(probabilities).all()
            or (probabilities < 0).any()
            or (probabilities > 1).any()
            or not np.allclose(probabilities.sum(axis=1), 1)
        ):
            raise ValueError(f"{self.model_id}: saída não contém probabilidades válidas.")
        return probabilities[:, self.positive_index]
