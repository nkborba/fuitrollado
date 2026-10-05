const element = (id) => document.getElementById(id);
const apiBase = (window.FUI_TROLLADO_CONFIG?.apiBase || '').replace(/\/$/, '');
const pagesWithoutAPI = location.hostname.endsWith('.github.io') && !apiBase;
const api = (path) => apiBase + path;
const scene = element('scene');
const trollSequence = createTrollSequence(scene);
function revealScene() {
  // Reserva espaço acima da cena para a marreta; o resultado fica logo abaixo.
  const headroom = matchMedia('(max-width: 760px)').matches ? 40 : 130;
  window.scrollTo({
    top: Math.max(0, window.scrollY + scene.getBoundingClientRect().top - headroom),
    behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth',
  });
}
// Se o GitHub estiver indisponível, preservar o avatar com iniciais.
document.querySelectorAll('.avatar-photo img').forEach((img) => {
  const fallback = () => img.remove();
  img.addEventListener('error', fallback, { once: true });
  if (img.complete && !img.naturalWidth) fallback();
});
let busy = false;
let modelInfo = {};
let catalogReady = false;
const labels = {
  credible: 'Padrões confiáveis',
  not_credible: 'Padrões não confiáveis',
  abster: 'Inconclusivo',
};
const number = ModelCatalog.number;
function clearComparison() {
  element('comparison').hidden = true;
  element('comparison-body').replaceChildren();
}
function addRow(body, values, selected = false) {
  const row = document.createElement('tr');
  if (selected) row.className = 'selected-model';
  values.forEach((value) => {
    const cell = document.createElement('td');
    cell.textContent = value;
    row.append(cell);
  });
  body.append(row);
}
function showComparison(data) {
  clearComparison();
  if (!data.comparisons) return;
  for (const item of data.comparisons)
    addRow(
      element('comparison-body'),
      [
        item.name + (item.model_id === data.model_id ? ' · selecionada' : ''),
        typeof item.probability === 'number'
          ? number(item.probability * 100, 2) + '%'
          : 'Sem representação',
        labels[item.label],
      ],
      item.model_id === data.model_id,
    );
  element('coverage-note').textContent = ModelCatalog.coverageNote(data.coverage);
  element('comparison').hidden = false;
}
element('model-select').addEventListener('change', () => {
  element('model-description').textContent = ModelCatalog.description(
    modelInfo[element('model-select').value],
  );
  clearComparison();
  showState('idle');
});
element('compare-models').addEventListener('change', clearComparison);
const states = {
  idle: {
    icon: '…',
    title: 'O próximo movimento é seu.',
    copy: 'Cole um texto para começar a análise.',
    speech: '...',
    caption: 'Só mais uma notícia…',
  },
  loading: {
    icon: '⌕',
    title: 'Analisando os padrões do texto…',
    copy: 'Um instante. O gamer está de olho.',
    speech: '...',
    caption: 'Lendo nas entrelinhas…',
  },
  credible: {
    icon: '✓',
    title: 'Padrões associados a conteúdo confiável',
    copy: 'O texto se aproxima da classe confiável da base estudada. Isso não confirma a veracidade da informação.',
    speech: '✓',
    caption: 'Parece tranquilo. Vale conferir!',
  },
  not_credible: {
    icon: '!',
    title: 'Padrões associados a conteúdo não confiável',
    copy: 'O modelo encontrou padrões associados à classe não confiável. Confira as evidências antes de compartilhar.',
    speech: '!',
    caption: 'O troll deu as caras. Atenção ao compartilhar!',
  },
  abster: {
    icon: '?',
    title: 'Resultado inconclusivo',
    copy: 'A probabilidade ficou na faixa de dúvida. O modelo se absteve; procure evidências para avaliar o conteúdo.',
    speech: '?',
    caption: 'Essa merece uma segunda olhada.',
  },
  error: {
    icon: '!',
    title: 'Não foi possível concluir a análise',
    copy: 'Tente novamente em alguns instantes.',
    speech: '?',
    caption: 'Pausa técnica…',
  },
};
function showState(kind, data = {}, preview = false) {
  const state = states[kind] || states.error;
  const result = element('result');
  // Reinicia a abertura mesmo quando repetimos a mesma classificação.
  result.removeAttribute('data-reveal');
  scene.dataset.state = kind;
  trollSequence.setState(kind);
  element('speech').textContent = state.speech;
  element('scene-caption').textContent = state.caption;
  element('result').dataset.kind = kind;
  element('result-icon').textContent = state.icon;
  element('result-title').textContent = (preview ? 'Prévia visual · ' : '') + state.title;
  element('result-copy').textContent = preview
    ? 'Simulação da animação. Nenhum texto foi classificado.'
    : data.reason === 'unknown_vocabulary'
      ? 'Não encontramos termos conhecidos pelo modelo. Não há base para emitir uma classificação.'
      : state.copy;
  const p = data.probability;
  element('probability').hidden = preview || typeof p !== 'number';
  element('probability').textContent =
    typeof p === 'number'
      ? `Estimativa para a classe “não confiável”: ${(p * 100).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%`
      : '';
  scene.setAttribute('aria-label', `Quarto do gamer. ${state.caption}`);
  if (kind !== 'idle') {
    void result.offsetWidth;
    result.dataset.reveal = 'opening';
  }
}
element('texto').addEventListener('input', () => {
  element('counter').textContent =
    `${element('texto').value.length.toLocaleString('pt-BR')} / 5.000`;
  element('field-error').textContent = '';
  clearComparison();
  if (!busy) showState('idle');
});
const examples = [
  'Roblox está dando Robux grátis para quem compartilhar o link com 10 amigos no WhatsApp.',
  'Nintendo confirma oficialmente a data de lançamento do novo console para novembro.',
];
let exampleIndex = 0;
element('example').addEventListener('click', () => {
  element('texto').value = examples[exampleIndex++ % examples.length];
  element('texto').dispatchEvent(new Event('input'));
  element('texto').focus();
});
document.querySelectorAll('[data-preview]').forEach((button) =>
  button.addEventListener('click', () => {
    if (!busy) {
      clearComparison();
      showState(button.dataset.preview, {}, true);
      revealScene();
    }
  }),
);
function setBusy(value) {
  busy = value;
  element('analyze-button').disabled = value || !catalogReady;
  element('example').disabled = value;
  element('texto').readOnly = value;
  element('model-select').disabled = value || !catalogReady;
  element('compare-models').disabled = value || !catalogReady;
  element('analyze-form').setAttribute('aria-busy', String(value));
  document.querySelectorAll('[data-preview]').forEach((b) => (b.disabled = value));
  element('button-label').textContent = value ? 'Analisando…' : 'Analisar texto';
}
element('analyze-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  if (busy) return;
  if (pagesWithoutAPI) {
    element('field-error').textContent =
      'A análise ainda não foi conectada. Configure o endereço da API para usar os modelos.';
    return;
  }
  if (!catalogReady) {
    element('field-error').textContent = 'Aguarde o carregamento dos modelos.';
    return;
  }
  const text = element('texto').value.trim();
  if (text.length < 20) {
    element('field-error').textContent = 'Cole pelo menos 20 caracteres para analisar.';
    return;
  }
  element('field-error').textContent = '';
  clearComparison();
  setBusy(true);
  showState('loading');
  element('texto').blur();
  revealScene();
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 90000);
  try {
    const response = await fetch(api('/api/analyze'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text,
        model: element('model-select').value,
        compare: element('compare-models').checked,
      }),
      signal: controller.signal,
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Falha ao analisar.');
    showState(data.label, data);
    showComparison(data);
  } catch (error) {
    showState('error');
    element('field-error').textContent =
      error.name === 'AbortError'
        ? 'A análise demorou mais que o esperado. Tente novamente.'
        : error.message;
  } finally {
    clearTimeout(timeout);
    setBusy(false);
  }
});
function renderCatalog(data) {
  const entries = Object.entries(data.models || {});
  if (!entries.length || !data.models[data.default_model]) {
    throw new Error('Catálogo de modelos inválido.');
  }
  modelInfo = data.models;
  const select = element('model-select');
  select.replaceChildren();
  element('study-body').replaceChildren();
  const families = new Map();
  for (const [id, info] of entries) {
    if (!families.has(info.family)) {
      const group = document.createElement('optgroup');
      group.label = info.family;
      families.set(info.family, group);
      select.append(group);
    }
    const option = document.createElement('option');
    option.value = id;
    option.textContent = info.name;
    families.get(info.family).append(option);
    addRow(element('study-body'), ModelCatalog.metricCells(info));
  }
  select.value = data.default_model;
  element('model-description').textContent = ModelCatalog.description(modelInfo[select.value]);
}

async function loadCatalog() {
  catalogReady = false;
  setBusy(false);
  element('retry-models').hidden = true;
  element('engine-status').textContent = 'Conectando aos modelos';
  try {
    const response = await fetch(api('/api/models'), { signal: AbortSignal.timeout(90000) });
    if (!response.ok) throw new Error('Catálogo indisponível.');
    renderCatalog(await response.json());
    catalogReady = true;
    element('engine-status').textContent = 'Modelos conectados';
    element('field-error').textContent = '';
  } catch {
    element('engine-status').textContent = 'Modelos indisponíveis';
    element('field-error').textContent =
      'Não foi possível carregar os modelos. Tente conectar novamente.';
    element('study-body').replaceChildren();
    addRow(element('study-body'), ['Resultados indisponíveis', '—', '—', '—', '—']);
    element('retry-models').hidden = false;
  }
  setBusy(false);
}

element('retry-models').addEventListener('click', loadCatalog);
if (pagesWithoutAPI) {
  setBusy(false);
  element('engine-status').textContent = 'Prévia sem API';
  element('field-error').textContent =
    'Interface pronta. A análise precisa de um backend conectado.';
  addRow(element('study-body'), ['Conecte a API para carregar os resultados', '—', '—', '—', '—']);
} else {
  loadCatalog();
}
