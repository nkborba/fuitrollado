// node --test tests/scene-animation.test.cjs — relógio determinístico, sem dependências.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync(require('node:path').join(__dirname, '../web/scene-animation.js'), 'utf8');

function setup({reduced = false, decoding = Promise.resolve()} = {}) {
  let time = 0, serial = 0;
  const jobs = new Map(), events = {}, mediaEvents = {};
  const frames = ['enter', 'prepare', 'strike', 'recover'].map(pose => frame(pose, true))
    .concat(['impact', 'dizzy-a', 'dizzy-b', 'recover'].map(pose => frame(pose, false)));
  function frame(pose, troll) {
    return {dataset:{pose}, hidden:true, decode:() => decoding, classList:{contains:() => troll}};
  }
  const scene = {dataset:{}, querySelectorAll:() => frames};
  const media = {matches:reduced, addEventListener:(name, cb) => mediaEvents[name] = cb};
  const document = {hidden:false, addEventListener:(name, cb) => events[name] = cb};
  const context = vm.createContext({document, window:{addEventListener(){}}, matchMedia:() => media,
    performance:{now:() => time}, requestAnimationFrame:cb => {jobs.set(++serial, cb); return serial;},
    cancelAnimationFrame:id => jobs.delete(id)});
  vm.runInContext(source, context);
  return {controller:context.createTrollSequence(scene), scene, frames, jobs, document,
    visible:() => frames.filter(f => !f.hidden).map(f => f.dataset.pose),
    step(at) { time = at; const pending = [...jobs.values()]; jobs.clear(); pending.forEach(cb => cb(time)); },
    reduce(value) {media.matches = value; mediaEvents.change();},
    hide() {document.hidden = true; events.visibilitychange();},
    show() {document.hidden = false; events.visibilitychange();}};
}

test('impacto compartilhado e tontura persistente sem callbacks ociosos', async () => {
  const s = setup(); await s.controller.setState('not_credible');
  for (const [at, phase, poses] of [
    [0,'portal',['enter']], [450,'portal',['enter']], [1449,'portal',['enter']],
    [1450,'enter',['enter']], [2200,'prepare',['prepare']],
    [2900,'strike',['strike','impact']], [3100,'dizzy',['recover','dizzy-a']],
    [4700,'dizzy',['recover','dizzy-a']], [60000,'dizzy',['recover','dizzy-a']],
  ]) {s.step(at); assert.equal(s.scene.dataset.phase,phase); assert.deepEqual(s.visible(),poses);}
  assert.equal(s.jobs.size,0);
});

test('passarinhos retomam ao voltar à aba ou desativar movimento reduzido', async () => {
  const s = setup(); await s.controller.setState('not_credible'); s.step(3100);
  s.hide(); assert.equal(s.scene.dataset.phase,'still');
  s.show(); assert.equal(s.scene.dataset.phase,'dizzy');
  s.reduce(true); assert.equal(s.scene.dataset.phase,'still');
  s.reduce(false); assert.equal(s.scene.dataset.phase,'dizzy');
  assert.equal(s.jobs.size,0);
  await s.controller.setState('credible'); s.hide(); s.show(); s.reduce(false);
  assert.equal(s.scene.dataset.phase,'idle');
});

test('somente a classe não confiável inicia a sequência', async () => {
  const s = setup();
  for (const state of ['idle','loading','credible','abster','error']) {
    await s.controller.setState(state); s.step(9000);
    assert.equal(s.scene.dataset.phase,'idle'); assert.equal(s.jobs.size,0);
  }
});

test('interromper qualquer fase cancela todos os callbacks antigos', async () => {
  for (const at of [0,500,1250,1500,2250,2950,3700,4800]) {
    const s = setup(); await s.controller.setState('not_credible'); s.step(at);
    await s.controller.setState('loading'); s.step(10000);
    assert.equal(s.scene.dataset.phase,'idle'); assert.deepEqual(s.visible(),['enter']);
    assert.equal(s.jobs.size,0);
  }
});

test('repetição do mesmo resultado reinicia no portal com gamer neutro', async () => {
  const s = setup(); await s.controller.setState('not_credible'); s.step(3700);
  await s.controller.setState('not_credible'); s.step(3700);
  assert.equal(s.scene.dataset.phase,'portal'); assert.deepEqual(s.visible(),['enter']);
  s.step(6600); assert.deepEqual(s.visible(),['strike','impact']);
});

test('mudança de estado enquanto imagens decodificam não ressuscita sequência', async () => {
  let resolve; const decoding = new Promise(r => resolve = r); const s = setup({decoding});
  const pending = s.controller.setState('not_credible');
  await s.controller.setState('credible'); resolve(); await pending;
  s.step(9000); assert.equal(s.scene.dataset.phase,'idle'); assert.equal(s.jobs.size,0);
});

test('movimento reduzido inicial, mudança durante execução e aba oculta', async () => {
  const reduced = setup({reduced:true}); await reduced.controller.setState('not_credible');
  assert.equal(reduced.scene.dataset.phase,'still'); assert.equal(reduced.jobs.size,0);
  assert.deepEqual(reduced.visible(),['recover','dizzy-a']);
  for (const action of [s => s.reduce(true), s => s.hide()]) {
    const s = setup(); await s.controller.setState('not_credible'); s.step(2900); action(s);
    s.step(9000); assert.equal(s.scene.dataset.phase,'still'); assert.equal(s.jobs.size,0);
    await s.controller.setState('idle'); assert.equal(s.scene.dataset.phase,'idle');
  }
});
