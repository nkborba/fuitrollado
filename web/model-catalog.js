/* Formatação do catálogo compartilhada pela interface e pelos testes. */
const ModelCatalog = (() => {
  function number(value, digits = 3) {
    return Number.isFinite(value)
      ? value.toLocaleString('pt-BR', {
          minimumFractionDigits: digits,
          maximumFractionDigits: digits,
        })
      : '—';
  }

  function metricCells(info) {
    const f1 = info.metrics?.f1_nc;
    const f1Text =
      Number.isFinite(f1?.mean) && Number.isFinite(f1?.std)
        ? `${number(f1.mean)} ± ${number(f1.std)}`
        : '—';
    const variation = info.robustness?.mean_probability_change;
    return [
      info.name,
      f1Text,
      number(info.metrics?.brier?.mean),
      Number.isFinite(variation) ? `${number(variation * 100, 2)} p.p.` : '—',
      info.evaluation?.description || 'Avaliação não informada.',
    ];
  }

  function description(info) {
    if (!info) return '';
    const abstention =
      info.delta === 0
        ? 'Sem faixa de abstenção por probabilidade.'
        : `Inconclusivo entre ${number((0.5 - info.delta) * 100, 1)}% e ${number((0.5 + info.delta) * 100, 1)}%, sem incluir os limites.`;
    return `${info.description || info.name} ${abstention}`;
  }

  function coverageNote(coverage) {
    if (!coverage) return 'Este modelo não informa cobertura de vocabulário.';
    return `Versão selecionada: ${coverage.known_terms} de ${coverage.total_terms} palavras/expressões distintas reconhecidas no vocabulário. Isso não mede compreensão; modelos com caracteres também usam fragmentos de palavras.`;
  }

  return { number, metricCells, description, coverageNote };
})();

if (typeof module !== 'undefined') module.exports = ModelCatalog;
