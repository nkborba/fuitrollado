"""Inferência dos modelos congelados. Não carrega dados nem treina modelos."""
import json
import re
import unicodedata
from pathlib import Path

import joblib
import numpy as np
from scipy.sparse import hstack

ROOT = Path(__file__).resolve().parent

def clean(text):
    return ' '.join(str(text).split())

def normalize(text):
    text = unicodedata.normalize('NFKC', str(text)).translate(str.maketrans({
        '“':'"', '”':'"', '‘':"'", '’':"'", '–':'-', '—':'-', '\u200b':''}))
    letters = r'[^\W\d_]'
    text = re.sub(rf'(?<={letters})(?=\d)|(?<=\d)(?={letters})', ' ', text)
    return clean(text).lower()

class Model:
    def __init__(self, artifact):
        self.data = artifact
        self.kind = artifact['kind']
        self.delta = artifact['delta']

    def prepare(self, texts):
        fn = normalize if self.kind in ('normalizado', 'normalizado_char') else clean
        return [fn(t) for t in texts]

    def matrix(self, texts):
        texts = self.prepare(texts)
        word = self.data['word'].transform(texts)
        char = self.data['char']
        return hstack([word, char.transform(texts)], format='csr') / np.sqrt(2) if char is not None else word

    def predict_proba(self, texts):
        matrix = self.matrix(texts)
        if self.data['calibration_input'] == 'logit_probability':
            p = np.clip(self.data['lr'].predict_proba(matrix)[:, 1], 1e-6, 1-1e-6)
            scores = np.log(p/(1-p))
        else:
            scores = self.data['lr'].decision_function(matrix)
        return self.data['calibrator'].predict_proba(scores[:, None])[:, 1]

    def analyze(self, text, name):
        terms = set(self.data['word'].build_analyzer()(self.prepare([text])[0]))
        known = terms & self.data['word'].vocabulary_.keys()
        nonzero = bool(self.matrix([text]).nnz)
        result = dict(model_id=self.kind, name=name, model=self.data['version'], delta=self.delta,
                      coverage=dict(known_terms=len(known), total_terms=len(terms),
                                    word_coverage=len(known)/len(terms) if terms else 0., representation_nonzero=nonzero))
        if not nonzero:
            return dict(result, label='abster', probability=None, reason='unknown_vocabulary')
        p = float(self.predict_proba([text])[0])
        label = 'abster' if abs(p-.5)<self.delta else ('not_credible' if p>=.5 else 'credible')
        return dict(result, label=label, probability=p)

def load_models():
    manifest = json.loads((ROOT / 'models/manifest.json').read_text())
    # Apenas artefatos confiáveis versionados neste repositório; sem upload de joblib.
    models = {key: Model(joblib.load(ROOT / 'models' / filename)) for key, filename in manifest['artifacts'].items()}
    return manifest, models
