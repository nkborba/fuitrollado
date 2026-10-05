/* Uma linha do tempo para os dois personagens; nenhuma alteração na classificação. */
function createTrollSequence(scene) {
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  const frames = [...scene.querySelectorAll('[data-pose]')];
  const ready = Promise.all(frames.map(img => img.decode().catch(() => null)));
  let generation = 0;
  let request = 0;
  let active = false;
  const timeline = [
    [0, 'portal', 'enter', 'neutral'],
    [450, 'enter', 'enter', 'neutral'],
    [1200, 'prepare', 'prepare', 'neutral'],
    [1900, 'strike', 'strike', 'impact'],
    [2100, 'dizzy', 'recover', 'dizzy-a'],
    [2600, 'dizzy', 'recover', 'dizzy-b'],
    [3100, 'dizzy', 'recover', 'dizzy-a'],
    [3600, 'dizzy', 'recover', 'dizzy-b'],
    [4100, 'recover', 'recover', 'recover'],
    [4700, 'settled', 'recover', 'neutral'],
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
  motion.addEventListener('change', () => { if (active) { generation++; still(); } });
  document.addEventListener('visibilitychange', () => {
    if (active && document.hidden) { generation++; still(); }
  });
  window.addEventListener('pagehide', cancel);
  return {setState};
}
