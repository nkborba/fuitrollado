"""Carrega somente os modelos explicitamente cadastrados no manifesto."""

import hashlib
import json
import math
from numbers import Real
from pathlib import Path

import joblib

from .adapters import LegacyLRClassifier, SklearnPipelineClassifier

ADAPTERS = {
    "legacy_lr": LegacyLRClassifier,
    "sklearn_pipeline": SklearnPipelineClassifier,
}
PUBLIC_FIELDS = (
    "name",
    "description",
    "family",
    "version",
    "delta",
    "metrics",
    "robustness",
    "evaluation",
)


class ModelRegistry:
    def __init__(self, manifest: dict, models: dict):
        self.manifest = manifest
        self.models = models
        self.default_model_id = manifest["default_model"]

    @classmethod
    def load(cls, models_dir: Path):
        models_dir = models_dir.resolve()
        manifest = json.loads((models_dir / "manifest.json").read_text(encoding="utf-8"))
        entries = manifest.get("models")
        if manifest.get("schema_version") != 2 or not isinstance(entries, dict) or not entries:
            raise ValueError("manifest.json precisa de schema_version 2 e models não vazio.")
        entries = enabled_entries(entries)
        if not entries:
            raise ValueError("Habilite pelo menos um modelo com enable: true.")
        if manifest.get("default_model") not in entries:
            raise ValueError("default_model precisa indicar um modelo cadastrado e habilitado.")
        models = {}
        for model_id, settings in entries.items():
            try:
                validate_settings(settings)
                artifact_path = (models_dir / settings["artifact"]).resolve()
                if not artifact_path.is_relative_to(models_dir) or not artifact_path.is_file():
                    raise ValueError("artifact deve apontar para um arquivo dentro de models/.")
                digest = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
                if digest != settings["sha256"]:
                    raise ValueError("SHA256 do artefato difere do cadastro.")
                # Joblib executa código ao abrir: só carregar arquivos revisados da equipe.
                artifact = joblib.load(artifact_path)
                model = ADAPTERS[settings["adapter"]](model_id, settings, artifact)
                model.analyze("Texto de verificação do carregamento do modelo.")
                models[model_id] = model
            except Exception as error:
                raise ValueError(f"Não foi possível carregar {model_id}: {error}") from error
        return cls(manifest, models)

    def metadata(self) -> dict:
        return {
            "default_model": self.default_model_id,
            "models": {
                model_id: {
                    key: self.manifest["models"][model_id][key]
                    for key in PUBLIC_FIELDS
                    if key in self.manifest["models"][model_id]
                }
                for model_id in self.models
            },
            "run": self.manifest.get("run"),
            "n_dev": self.manifest.get("n_dev"),
            "folds": self.manifest.get("outer_folds"),
        }


def enabled_entries(entries: dict) -> dict:
    """Filtra antes de validar artefatos; cadastros antigos continuam habilitados."""
    enabled = {}
    for model_id, settings in entries.items():
        if not isinstance(settings, dict):
            raise ValueError(f"{model_id}: o cadastro deve ser um objeto JSON.")
        flag = settings.get("enable", True)
        if not isinstance(flag, bool):
            raise ValueError(f"{model_id}: enable deve ser true ou false, sem aspas.")
        if flag:
            enabled[model_id] = settings
    return enabled


def validate_settings(settings: dict) -> None:
    if not isinstance(settings, dict):
        raise ValueError("o cadastro deve ser um objeto JSON.")
    for key in ("name", "family", "version", "artifact", "sha256"):
        if not isinstance(settings.get(key), str) or not settings[key].strip():
            raise ValueError(f"campo obrigatório ausente ou inválido: {key}.")
    if settings.get("adapter") not in ADAPTERS:
        raise ValueError(f"adapter deve ser um de: {', '.join(ADAPTERS)}.")
    if Path(settings["artifact"]).is_absolute():
        raise ValueError("artifact deve usar um caminho relativo a models/.")
    delta = settings.get("delta")
    if (
        isinstance(delta, bool)
        or not isinstance(delta, Real)
        or not math.isfinite(delta)
        or not 0 <= delta < 0.5
    ):
        raise ValueError("delta deve ser um número entre 0 (inclusive) e 0.5 (exclusive).")
    if settings["adapter"] == "sklearn_pipeline":
        positive = settings.get("positive_class")
        if isinstance(positive, bool) or not isinstance(positive, (str, int)):
            raise ValueError(
                "positive_class deve ser o rótulo inteiro ou textual de não confiável."
            )
