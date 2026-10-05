/* Uma linha do tempo para os dois personagens; nenhuma alteração na classificação. */
// Espera depois que o portal abre: 1000 = 1 segundo; 2000 = 2 segundos.
const PORTAL_PAUSE_MS = 1250;

function createTrollSequence(scene) {
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  const frames = [...scene.querySelectorAll('[data-pose]')];
  const ready = Promise.all(frames.map(img => img.decode().catch(() => null)));
  let generation = 0;
  let request = 0;
  let active = false;
  const trollAppearsAt = 450 + PORTAL_PAUSE_MS;
  const timeline = [
    [0, 'portal', 'enter', 'neutral'],
    [trollAppearsAt, 'enter', 'enter', 'neutral'],
    [trollAppearsAt + 750, 'prepare', 'prepare', 'neutral'],
    [trollAppearsAt + 1450, 'strike', 'strike', 'impact'],
    [trollAppearsAt + 1650, 'dizzy', 'recover', 'dizzy-a'],
  ];
  function paint(phase, troll, gamer) {
    scene.dataset.phase = phase;
    frames.forEach(img => {
      img.hidden = img.dataset.pose !== (img.classList.contains('troll-pose') ? troll : gamer);
    });
  }
  function cancel() {
    generation++;
    cancelAnimationFrame(request);
    request = 0;
    active = false;
    paint('idle', 'enter', 'neutral');
    // Materializa o reset antes de repetir a mesma classificação, inclusive
    // quando o portal anterior ainda estava aberto.
    void scene.offsetWidth;
  }
  function still() {
    cancelAnimationFrame(request);
    request = 0;
    paint('still', 'recover', 'dizzy-a');
  }
  async function setState(kind) {
    cancel();
    if (kind !== 'not_credible') return;
    active = true;
    const token = generation;
    paint('waiting', 'enter', 'neutral');
    await ready;
    if (token !== generation) return;
    if (motion.matches || document.hidden) { still(); return; }
    const start = performance.now();
    let previous = -1;
    function tick(now) {
      if (token !== generation) return;
      const elapsed = now - start;
      const index = timeline.findLastIndex(([at]) => elapsed >= at);
      if (index !== previous) {
        const [, phase, troll, gamer] = timeline[index];
        paint(phase, troll, gamer);
        previous = index;
      }
      request = index < timeline.length - 1 ? requestAnimationFrame(tick) : 0;
    }
    request = requestAnimationFrame(tick);
  }
  function updateMotion() {
    if (!active) return;
    generation++;
    still();
    if (!motion.matches && !document.hidden) paint('dizzy', 'recover', 'dizzy-a');
  }
  motion.addEventListener('change', updateMotion);
  document.addEventListener('visibilitychange', () => {
    updateMotion();
  });
  window.addEventListener('pagehide', cancel);
  return {setState};
}
