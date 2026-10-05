# Estudo 10 — robustez de escrita e comparação no site

Desenho fixado antes da execução. Motivo: as grafias GTA6/GTA 6 alteraram fortemente a previsão do modelo do estudo 09. Não acrescentamos esse exemplo ao treino nem usamos seu rótulo como objetivo de seleção.

## Quatro braços

1. **atual**: receita da LR de referência (C=1, max_iter=1000, seed 42), TF-IDF de palavras 1–2, min_df=2, até 5.000 termos. No site permanece o artefato original do estudo 09.
2. **normalizado**: mesma LR e TF-IDF, com normalização Unicode NFKC, espaços uniformizados, aspas/hífens tipográficos padronizados e separação entre letras e números. Tokenizador também preserva dígitos isolados; palavras de uma letra continuam excluídas. Essa alteração faz parte do braço, não é uma ablação separada do tokenizador.
3. **augmentation**: sem normalização na inferência. No treino, original + grafias com letras/números separados ou unidos + variações de caixa/espaçamento e pontuação terminal. Não altera entidades, negações, quantidades, datas, verbos nem rótulos. Alterações ortográficas são hipóteses de invariância, não garantia semântica universal. Amostra de pares fica registrada para revisão.
4. **normalizado_char**: normalização do braço 2 + TF-IDF de palavras e caracteres (analyzer=char, 3–5 caracteres, min_df=2, até 20.000 termos). Blocos L2 com peso 1/sqrt(2) cada, para não dobrar a norma da representação. Sem extras lexicais, SVD ou clustering.

## Controle de augmentation

Variações são geradas depois de cada split e ficam exclusivamente no treino correspondente. Cada notícia tem peso total 1 na LR, dividido entre suas versões. Vocabulário e IDF do augmentation usam frequência documental por notícia original (união dos termos de suas versões); cópias sintéticas não contam como documentos independentes para min_df/IDF. O limite de vocabulário usa frequência média por família. Não criaremos paráfrases generativas nesta rodada.

## Avaliação

- Mesma carga/deduplicação/SHA/split do estudo 09, usando caminho real do dataset no workspace.
- DEV: 927 textos, cinco folds externos estratificados idênticos. Holdout histórico: 103 textos, excluído de treino, seleção, calibração e métricas desta rodada.
- Verificação de sobreposição de textos normalizados entre splits. Augmentation feito após as divisões, inclusive internas.
- Todos os braços usam Platt fixado previamente, ajustado em previsões OOF de cinco folds internos. Nenhum ajuste de vocabulário ou LR vê a avaliação externa.
- Sem busca de hiperparâmetros. Abstenção com delta **fixo 0,375**, herdado do artefato do site para todos os braços. Não significa 95% garantidos. Diferente da escolha de delta por fold do estudo 09; não comparar cobertura entre os estudos como reprodução exata.
- Reportar F1 NC bruto e calibrado, F1 macro, acurácia balanceada, AP NC (Average Precision, não AUC trapezoidal), Brier, matriz de confusão, cobertura e acurácia das decisões emitidas.
- Robustez nos textos externos de cada fold: mudanças de probabilidade e de classe, por transformação. Separar alterações de letras/números dos controles triviais de caixa/espaçamento.
- Casos GTA6/GTA 6 são diagnóstico conhecido, sem alegar avaliação independente ou acerto factual. Não usados para treinar ou selecionar.
- Comparação descritiva; nenhum vencedor automaticamente promovido ao site. Uso exploratório do corpus já conhecido permanece limitação.

## Inferência final

Três candidatos ajustados somente no DEV, com Platt OOF interno. A referência no site continua sendo o joblib original. Probabilidade apresentada sempre se refere à classe não confiável. Sem termos reconhecidos, a proteção de entrada retorna inconclusivo sem probabilidade; baixa cobertura não ganha um limiar inventado nesta rodada. O estudo não mede checagem factual nem elimina atalhos temáticos.
