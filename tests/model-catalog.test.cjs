const { test } = require('node:test');
const assert = require('node:assert/strict');
const catalog = require('../web/model-catalog.js');

test('modelo sem métricas não herda números do estudo da LR', () => {
  assert.deepEqual(catalog.metricCells({ name: 'KNN' }), [
    'KNN',
    '—',
    '—',
    '—',
    'Avaliação não informada.',
  ]);
  assert.match(catalog.coverageNote(null), /não informa/);
});

test('descrição respeita o delta de cada modelo', () => {
  assert.match(catalog.description({ name: 'KNN', delta: 0 }), /Sem faixa/);
  assert.match(catalog.description({ name: 'LR', delta: 0.375 }), /12,5% e 87,5%/);
});

test('métrica zero é apresentada e valor ausente não vira NaN', () => {
  const cells = catalog.metricCells({
    name: 'Teste',
    metrics: { brier: { mean: 0 } },
    robustness: { mean_probability_change: 0 },
  });
  assert.equal(cells[2], '0,000');
  assert.equal(cells[3], '0,00 p.p.');
  assert.equal(cells[1], '—');
});
