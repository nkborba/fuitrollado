# Estudo 10 — robustez textual

Execução: `20261004T132959Z`. Dataset SHA256: `df8cd69fbafb9c4e1960637ae2c58bba791d695f410a625ca7e4f628687fc7cc`.

927 claims DEV, cinco folds externos; Platt ajustado em cinco folds internos. 103 claims de holdout excluídas. Mesmas partições históricas; nenhum texto sintético na avaliação de classificação.

| Modelo | F1 NC calibrado (média ± DP) | F1 NC sem calibração | Brier | Mudança média de p entre grafias alfanuméricas |
|---|---:|---:|---:|---:|
| LR atual | 0.8988 ± 0.0389 | 0.8940 | 0.0781 | 5.40 p.p. |
| LR normalizada | 0.8898 ± 0.0336 | 0.8883 | 0.0795 | 0.00 p.p. |
| LR + augmentation | 0.8987 ± 0.0401 | 0.8942 | 0.0780 | 4.11 p.p. |
| LR normalizada + palavras e caracteres | 0.8998 ± 0.0385 | 0.8968 | 0.0731 | 0.00 p.p. |

## Interpretação e limites

As médias calibradas usam limiar 0,5 e todos os exemplos. Abstenção é uma análise separada com delta fixo 0,375 (faixa aberta 0,125–0,875); não repetimos a seleção interna de delta do estudo 09. DP descreve variação entre folds, não é intervalo de confiança. Não há promoção automática de um vencedor.

O braço atual foi reestimado por fold com a receita original; no site continua sendo usado o artefato original, sem retreiná-lo em DEV para avaliá-lo. O F1 sem calibração reproduziu a referência do estudo 09.

Normalizada também preserva números isolados; portanto esse braço combina normalização e tokenização. Palavras+caracteres usa até 5.000 termos e 20.000 n-gramas de caracteres; “tudo” não significa vocabulário ilimitado nem inclusão de features externas.

Augmentation é apenas ortográfico, não paráfrases geradas por LLM. Cada família tem peso total 1; IDF conta famílias, evitando inflar frequência por cópias. As perturbações são hipóteses de invariância, não evidência de diversidade factual.

A estabilidade mede pares perturbados de textos do fold externo. Pares da mesma claim são dependentes. Menor variação não garante classificação correta. A avaliação continua exploratória no mesmo corpus já utilizado nos estudos anteriores; não demonstra generalização fora dele nem ausência de atalhos.

## Sonda solicitada: GTA6 / GTA 6

Os dois textos abaixo NÃO foram adicionados ao treino e não constituem um teste de acurácia factual. Valores gerados pelos artefatos finais:

| Modelo | p(NC) GTA6 | p(NC) GTA 6 | Decisões |
|---|---:|---:|---|
| LR atual | 0.3717 | 0.1075 | abster / credible |
| LR normalizada | 0.0389 | 0.0389 | credible / credible |
| LR + augmentation | 0.2983 | 0.1253 | abster / abster |
| LR normalizada + palavras e caracteres | 0.1383 | 0.1383 | abster / abster |

A calibração ajusta probabilidades de classe do corpus; não verifica acontecimentos. Estabilidade ortográfica e veracidade são objetivos diferentes. O site apresenta associação à classe, não um veredito de verdadeiro/falso.

## Reprodução

Execute `executar.py` no ambiente do estudo 09. Resultados por fold, OOF e pares estão ao lado deste relatório. O manifesto ativo só é atualizado após os checks. Os modelos podem ser escolhidos no site e comparados com o mesmo texto.