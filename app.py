"""Site e API. Local: python app.py. Hospedagem: gunicorn app:app."""

import os
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge, UnsupportedMediaType

from prediction import ModelRegistry, clean

ROOT = Path(__file__).resolve().parent
MIN_TEXT_LENGTH = 20
MAX_TEXT_LENGTH = 5000


def create_app(registry: ModelRegistry | None = None) -> Flask:
    app = Flask(__name__, static_folder=None)
    app.json.sort_keys = False
    app.config["MAX_CONTENT_LENGTH"] = 32000
    app.config["ALLOWED_ORIGINS"] = {
        origin.strip().rstrip("/")
        for origin in os.environ.get("ALLOWED_ORIGINS", "").split(",")
        if origin.strip()
    }
    registry = registry if registry is not None else ModelRegistry.load(ROOT / "models")
    app.extensions["model_registry"] = registry

    @app.after_request
    def add_response_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
            origin = request.headers.get("Origin")
            if origin in app.config["ALLOWED_ORIGINS"]:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
                response.headers["Access-Control-Allow-Headers"] = "Content-Type"
                response.vary.add("Origin")
        return response

    @app.get("/api/health")
    def health():
        model = registry.models[registry.default_model_id]
        return jsonify(
            ready=True,
            model=model.version,
            model_id=model.model_id,
            delta=model.delta,
            model_count=len(registry.models),
        )

    @app.get("/api/models")
    def model_metadata():
        return jsonify(registry.metadata())

    @app.post("/api/analyze")
    def analyze():
        payload = request.get_json()
        if not isinstance(payload, dict) or not isinstance(payload.get("text"), str):
            return jsonify(error="Envie um texto válido."), 400
        model_id = payload.get("model", registry.default_model_id)
        compare = payload.get("compare", False)
        if (
            not isinstance(model_id, str)
            or model_id not in registry.models
            or not isinstance(compare, bool)
        ):
            return jsonify(error="Selecione um modelo e uma opção de comparação válidos."), 400
        text = clean(payload["text"])
        if not MIN_TEXT_LENGTH <= len(text) <= MAX_TEXT_LENGTH:
            return jsonify(error="Cole um texto entre 20 e 5.000 caracteres."), 400

        result = registry.models[model_id].analyze(text)
        if compare:
            result["comparisons"] = [
                result.copy() if other_id == model_id else model.analyze(text)
                for other_id, model in registry.models.items()
            ]
        return jsonify(result)

    @app.errorhandler(BadRequest)
    @app.errorhandler(UnsupportedMediaType)
    def invalid_json(error):
        return jsonify(error="Envie um JSON válido com o campo text."), 400

    @app.errorhandler(RequestEntityTooLarge)
    def request_too_large(error):
        return jsonify(error="O texto deve ter até 5.000 caracteres."), 413

    @app.errorhandler(500)
    def analysis_failed(error):
        return jsonify(error="Não foi possível analisar agora. Tente novamente."), 500

    @app.get("/")
    def index():
        return send_from_directory(ROOT / "web", "index.html")

    @app.get("/<path:filename>")
    def static_file(filename):
        # Modelos e código ficam fora da raiz pública.
        return send_from_directory(ROOT / "web", filename)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8765")),
        debug=False,
    )
