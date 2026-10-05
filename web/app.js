const $ = id => document.getElementById(id);
const apiBase = (window.FUI_TROLLADO_CONFIG?.apiBase || '').replace(/\/$/, '');
const pagesWithoutAPI = location.hostname.endsWith('.github.io') && !apiBase;
const api = path => apiBase + path;
const scene = $('scene');
const trollSequence = createTrollSequence(scene);
function revealScene() {
  // Reserva espaço acima da cena para a marreta; o resultado fica logo abaixo.
  const headroom = matchMedia('(max-width: 760px)').matches ? 40 : 130;
  window.scrollTo({
    top: Math.max(0, window.scrollY + scene.getBoundingClientRect().top - headroom),
    behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'
  });
}
// Se o GitHub estiver indisponível, preservar o avatar com iniciais.
document.querySelectorAll('.avatar-photo img').forEach(img => {
  const fallback = () => img.remove();
  img.addEventListener('error', fallback, {once:true});
  if (img.complete && !img.naturalWidth) fallback();
});
let busy = false;
let modelInfo = {};
const labels = {credible:'Padrões confiáveis',not_credible:'Padrões não confiáveis',abster:'Inconclusivo'};
const number = (n,d=3) => n.toLocaleString('pt-BR',{minimumFractionDigits:d,maximumFractionDigits:d});
function clearComparison() { $('comparison').hidden = true; $('comparison-body').replaceChildren(); }
function addRow(body, values, selected=false) {
  const row = document.createElement('tr');
  if (selected) row.className = 'selected-model';
  values.forEach(value => { const cell = document.createElement('td'); cell.textContent = value; row.append(cell); });
  body.append(row);
}
function showComparison(data) {
  clearComparison();
  if (!data.comparisons) return;
  for (const item of data.comparisons) addRow($('comparison-body'), [item.name + (item.model_id===data.model_id ? ' · selecionada' : ''), typeof item.probability==='number' ? number(item.probability*100,2)+'%' : 'Sem representação', labels[item.label]], item.model_id===data.model_id);
  const c = data.coverage;
  $('coverage-note').textContent = `Versão selecionada: ${c.known_terms} de ${c.total_terms} palavras/expressões distintas reconhecidas no vocabulário. Isso não mede compreensão; a versão com caracteres também usa fragmentos de palavras.`;
  $('comparison').hidden = false;
}
$('model-select').addEventListener('change', () => {
  $('model-description').textContent = modelInfo[$('model-select').value]?.description || '';
  clearComparison(); showState('idle');
});
$('compare-models').addEventListener('change', clearComparison);
const states = {
  idle: {icon:'…', title:'O próximo movimento é seu.', copy:'Cole um texto para começar a análise.', speech:'...', caption:'Só mais uma notícia…'},
  loading: {icon:'⌕', title:'Analisando os padrões do texto…', copy:'Um instante. O gamer está de olho.', speech:'...', caption:'Lendo nas entrelinhas…'},
  credible: {icon:'✓', title:'Padrões associados a conteúdo confiável', copy:'O texto se aproxima da classe confiável da base estudada. Isso não confirma a veracidade da informação.', speech:'✓', caption:'Parece tranquilo. Vale conferir!'},
  not_credible: {icon:'!', title:'Padrões associados a conteúdo não confiável', copy:'O modelo encontrou padrões associados à classe não confiável. Confira as evidências antes de compartilhar.', speech:'!', caption:'O troll deu as caras. Atenção ao compartilhar!'},
  abster: {icon:'?', title:'Resultado inconclusivo', copy:'A probabilidade ficou na faixa de dúvida. O modelo se absteve; procure evidências para avaliar o conteúdo.', speech:'?', caption:'Essa merece uma segunda olhada.'},
  error: {icon:'!', title:'Não foi possível concluir a análise', copy:'Tente novamente em alguns instantes.', speech:'?', caption:'Pausa técnica…'}
};
function showState(kind, data = {}, preview = false) {
  const s = states[kind] || states.error;
  scene.dataset.state = kind;
  trollSequence.setState(kind);
  $('speech').textContent = s.speech;
  $('scene-caption').textContent = s.caption;
  $('result').dataset.kind = kind;
  $('result-icon').textContent = s.icon;
  $('result-title').textContent = (preview ? 'Prévia visual · ' : '') + s.title;
  $('result-copy').textContent = preview ? 'Simulação da animação. Nenhum texto foi classificado.' : data.reason === 'unknown_vocabulary' ? 'Não encontramos termos conhecidos pelo modelo. Não há base para emitir uma classificação.' : s.copy;
  const p = data.probability;
  $('probability').hidden = preview || typeof p !== 'number';
  $('probability').textContent = typeof p === 'number' ? `Estimativa para a classe “não confiável”: ${(p * 100).toLocaleString('pt-BR', {minimumFractionDigits:2,maximumFractionDigits:2})}%` : '';
  scene.setAttribute('aria-label', `Quarto do gamer. ${s.caption}`);
}
$('texto').addEventListener('input', () => {
  $('counter').textContent = `${$('texto').value.length.toLocaleString('pt-BR')} / 5.000`;
  $('field-error').textContent = '';
  clearComparison();
  if (!busy) showState('idle');
});
const examples = ['Roblox está dando Robux grátis para quem compartilhar o link com 10 amigos no WhatsApp.', 'Nintendo confirma oficialmente a data de lançamento do novo console para novembro.'];
let exampleIndex = 0;
$('example').addEventListener('click', () => {
  $('texto').value = examples[exampleIndex++ % examples.length];
  $('texto').dispatchEvent(new Event('input'));
  $('texto').focus();
});
document.querySelectorAll('[data-preview]').forEach(button => button.addEventListener('click', () => {
  if (!busy) {
    clearComparison(); showState(button.dataset.preview, {}, true);
    revealScene();
  }
}));
function setBusy(value) {
  busy = value;
  $('analyze-button').disabled = value;
  $('example').disabled = value;
  $('texto').readOnly = value;
  $('model-select').disabled = value;
  $('compare-models').disabled = value;
  $('analyze-form').setAttribute('aria-busy', String(value));
  document.querySelectorAll('[data-preview]').forEach(b => b.disabled = value);
  $('button-label').textContent = value ? 'Analisando…' : 'Analisar texto';
}
$('analyze-form').addEventListener('submit', async event => {
  event.preventDefault();
  if (busy) return;
  if (pagesWithoutAPI) { $('field-error').textContent = 'A análise ainda não foi conectada. Configure o endereço da API para usar os modelos.'; return; }
  const text = $('texto').value.trim();
  if (text.length < 20) { $('field-error').textContent = 'Cole pelo menos 20 caracteres para analisar.'; return; }
  $('field-error').textContent = '';
  clearComparison(); setBusy(true); showState('loading');
  $('texto').blur();
  revealScene();
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 90000);
  try {
    const response = await fetch(api('/api/analyze'), {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({text,model:$('model-select').value,compare:$('compare-models').checked}), signal:controller.signal});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Falha ao analisar.');
    showState(data.label, data);
    showComparison(data);
  } catch(error) {
    showState('error');
    $('field-error').textContent = error.name === 'AbortError' ? 'A análise demorou mais que o esperado. Tente novamente.' : error.message;
  } finally { clearTimeout(timeout); setBusy(false); }
});
if (pagesWithoutAPI) {
  $('engine-status').textContent = 'Prévia sem API';
  $('field-error').textContent = 'Interface pronta. A análise precisa de um backend conectado.';
  addRow($('study-body'),['Conecte a API para carregar os resultados','—','—','—']);
} else {
fetch(api('/api/health'), {signal:AbortSignal.timeout(90000)}).then(r => {if (!r.ok) throw new Error(); return r.json();}).then(() => $('engine-status').textContent = 'Modelo conectado').catch(() => $('engine-status').textContent = 'Modelo indisponível');
fetch(api('/api/models'), {signal:AbortSignal.timeout(90000)}).then(r=>{if(!r.ok) throw new Error(); return r.json();}).then(data=>{
  modelInfo=data.models;
  for (const info of Object.values(modelInfo)) {
    const m=info.metrics;
    addRow($('study-body'),[info.name,`${number(m.f1_nc.mean)} ± ${number(m.f1_nc.std)}`,number(m.brier.mean),number(info.robustness.mean_probability_change*100,2)+' p.p.']);
  }
}).catch(()=>{addRow($('study-body'),['Resultados indisponíveis','—','—','—']);});
}
