"""Site e API. Local: python app.py. Hospedagem: gunicorn app:app."""
import os
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge, UnsupportedMediaType
from inference import clean, load_models

ROOT = Path(__file__).resolve().parent
app = Flask(__name__, static_folder=None)
app.json.sort_keys = False
app.config['MAX_CONTENT_LENGTH'] = 32000
manifest, models = load_models()
allowed_origins = {s.strip().rstrip('/') for s in os.environ.get('ALLOWED_ORIGINS', '').split(',') if s.strip()}

@app.after_request
def headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    if request.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
        origin = request.headers.get('Origin')
        if origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            response.vary.add('Origin')
    return response

@app.get('/api/health')
def health():
    return jsonify(ready=True, model=models['atual'].data['version'], delta=models['atual'].delta)

@app.get('/api/models')
def metadata():
    return jsonify(models=manifest['models'], run=manifest['run'], n_dev=manifest['n_dev'], folds=5)

@app.post('/api/analyze')
def analyze():
    data = request.get_json()
    if not isinstance(data, dict) or not isinstance(data.get('text'), str):
        return jsonify(error='Envie um texto válido.'), 400
    kind = data.get('model', 'atual')
    if not isinstance(kind, str) or kind not in models or not isinstance(data.get('compare',False), bool):
        return jsonify(error='Selecione um modelo e uma opção de comparação válidos.'), 400
    text = clean(data['text'])
    if not 20 <= len(text) <= 5000:
        return jsonify(error='Cole um texto entre 20 e 5.000 caracteres.'), 400
    result = models[kind].analyze(text,manifest['models'][kind]['name'])
    if data.get('compare',False):
        result['comparisons'] = [result.copy() if k==kind else m.analyze(text,manifest['models'][k]['name']) for k,m in models.items()]
    return jsonify(result)

@app.errorhandler(BadRequest)
@app.errorhandler(UnsupportedMediaType)
def invalid_json(error):
    return jsonify(error='Envie um JSON válido com o campo text.'), 400

@app.errorhandler(RequestEntityTooLarge)
def too_large(error):
    return jsonify(error='O texto deve ter até 5.000 caracteres.'), 413

@app.errorhandler(500)
def failed(error):
    return jsonify(error='Não foi possível analisar agora. Tente novamente.'), 500

@app.get('/')
def index():
    return send_from_directory(ROOT/'web', 'index.html')

@app.get('/<path:filename>')
def static_file(filename):
    # A raiz servida contém apenas a interface; modelos e código não são públicos.
    return send_from_directory(ROOT/'web', filename)

if __name__ == '__main__':
    app.run(host=os.environ.get('HOST','127.0.0.1'), port=int(os.environ.get('PORT','8765')), debug=False)
