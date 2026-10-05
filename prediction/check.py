"""Valida o cadastro local: python -m prediction.check."""

from pathlib import Path

from .registry import ModelRegistry


def main() -> None:
    registry = ModelRegistry.load(Path(__file__).resolve().parents[1] / "models")
    for model_id, model in registry.models.items():
        print(f"{model_id}: {model.name} ({model.version}), delta={model.delta}")
    print(f"{len(registry.models)} modelos carregados. Padrão: {registry.default_model_id}.")


if __name__ == "__main__":
    main()
