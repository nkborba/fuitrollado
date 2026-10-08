# Modelos do site

Cada família fica numa pasta. O cadastro fica em `manifest.json`.

```text
models/
  manifest.json
  README.md
  LR/
    atual.joblib
    normalizado.joblib
    augmentation.joblib
    normalizado_char.joblib
    PROTOCOLO_ESTUDO_10.md
    RELATORIO_ESTUDO_10.md
    metricas_folds.csv
    validacao_exportacao.json
  KNN/                       # criar quando houver um KNN treinado
    modelo.joblib
```

As quatro LRs foram apenas movidas. Os arquivos treinados e suas previsões foram preservados.

## Adicionar um modelo

Para um pipeline compatível, basta salvar o arquivo na pasta da família e adicionar uma entrada em `models/manifest.json`. Não precisa alterar Python, HTML ou a lista de opções do site.

### 1. Salvar o pipeline completo

O arquivo deve conter tudo que transforma texto em probabilidade: normalização, TF-IDF, SVD, classificador e calibração, se foram usados. Salvar só o KNN ou só a LR não basta.

O objeto precisa:

- estar treinado e aceitar uma lista de textos em `predict_proba`;
- devolver uma matriz com duas colunas, com probabilidades entre 0 e 1 que somam 1 por linha;
- ter `classes_` com dois rótulos, na mesma ordem das colunas;
- usar rótulos inteiros ou strings. Declare qual significa não confiável no cadastro.

Exemplo de exportação, dentro do ambiente em que o modelo foi treinado:

```python
from pathlib import Path
import joblib

destino = Path("models/KNN/modelo.joblib")
destino.parent.mkdir(parents=True, exist_ok=True)
joblib.dump(pipeline_treinado, destino)
```

`pipeline_treinado` é o pipeline que vocês já treinaram e avaliaram, por exemplo um `sklearn.pipeline.Pipeline` ou um `CalibratedClassifierCV` envolvendo o pipeline completo. O site não treina, não cria TF-IDF novo e não calibra automaticamente o arquivo recebido.

A API uniformiza espaços antes de entregar o texto ao pipeline. Qualquer outra transformação específica deve estar dentro dele. Se houver classes ou funções próprias, coloque-as em módulos Python importáveis no repositório, nunca só em células do notebook ou em `__main__`. Mantenha as versões de bibliotecas compatíveis com `requirements.txt`.

### 2. Calcular o SHA256

Na raiz do projeto:

```sh
python -c "import hashlib; from pathlib import Path; print(hashlib.sha256(Path('models/KNN/modelo.joblib').read_bytes()).hexdigest())"
```

### 3. Cadastrar em `manifest.json`

Adicione uma entrada dentro de `models`, ao lado das LRs. Exemplo:

```json
"knn_v1": {
  "enable": true,
  "name": "KNN + TF-IDF",
  "description": "KNN treinado com TF-IDF de palavras.",
  "family": "KNN",
  "version": "knn-v1",
  "artifact": "KNN/modelo.joblib",
  "adapter": "sklearn_pipeline",
  "positive_class": 1,
  "delta": 0,
  "sha256": "COLE_AQUI_O_HASH_DO_ARQUIVO"
}
```

Use `positive_class: 1` somente se **1 for o rótulo de não confiável no seu treino**. Se usou strings, pode ser `"not_credible"` ou outro rótulo correspondente. O site consulta `classes_`; não presume que a segunda coluna é a classe positiva.

`delta` controla a abstenção: se `abs(probabilidade - 0.5) < delta`, o resultado é inconclusivo. Com `0`, não há faixa de abstenção por probabilidade. Com `0.375`, a faixa é de 12,5% a 87,5%, sem incluir os limites. Não copie o valor das LRs sem avaliar no seu modelo. A calibração também precisa ser avaliada, mesmo que o estimador já tenha `predict_proba`.

O identificador, como `knn_v1`, deve ser único e estável. `name` aparece no site; `family` agrupa o seletor; `version` identifica o artefato. `artifact` é relativo a esta pasta. Para mudar a seleção inicial, altere `default_model` na raiz do manifesto.

Não adicione uma lista `artifacts`: a versão 2 do cadastro reúne o caminho e as informações na mesma entrada. Reinicie o servidor depois de alterar o cadastro ou um arquivo de modelo.

### Habilitar ou desabilitar

Cada entrada em `models` aceita `"enable": true` ou `"enable": false`.
Sem a propriedade, o modelo continua habilitado. Use booleanos, sem aspas.

Com `false`, o modelo não é carregado, não aparece no seletor e não entra nas
comparações. A API também rejeita pedidos que tentem usá-lo diretamente.
O arquivo treinado pode continuar na pasta; basta trocar para `true` e reiniciar
o servidor para disponibilizá-lo novamente. Os artefatos desabilitados não são
verificados durante a inicialização.

Mantenha pelo menos um modelo habilitado. `default_model` precisa apontar para
um deles; o servidor informa o erro se o padrão estiver desabilitado.
Na configuração da apresentação, `atual` e `normalizado_char` estão habilitados;
`normalizado` e `augmentation` estão desabilitados.

### 4. Verificar

```sh
python -m prediction.check
python -m unittest discover -s tests -v
node --test tests/*.test.cjs
python app.py
```

O primeiro comando confere o cadastro, o hash, as classes e uma inferência de teste. Isso verifica compatibilidade com o site, não qualidade do modelo. Um cadastro inválido impede a inicialização e a mensagem informa qual modelo falhou.

No site, o modelo aparece automaticamente no seletor, agrupado pela família, e entra na comparação. Teste também um texto conhecido de cada classe. O health check passa a mostrar o modelo padrão e a quantidade carregada.

## Informar os resultados da avaliação

Métricas são opcionais. Se não informar, o site mostra um traço. Para publicar resultados, inclua na entrada:

```json
"metrics": {
  "f1_nc": {"mean": 0.89, "std": 0.03},
  "brier": {"mean": 0.08}
},
"evaluation": {
  "description": "Descreva aqui dataset, divisão, quantidade de folds e calibração."
}
```

Os números acima são só exemplos. Use os resultados reais da validação. Para F1 NC, a tabela espera média e desvio dos folds, sem abstenção, com limiar 0,5. O Brier deve usar a probabilidade da classe não confiável. `robustness.mean_probability_change` é opcional e só deve ser preenchido se o teste de variações ortográficas tiver sido feito; o valor usa escala 0 a 1.

Não compare diretamente métricas calculadas com bases ou splits diferentes. Os dados de execução na raiz do manifesto e os relatórios em `LR/` descrevem o estudo 10, não os modelos que forem acrescentados depois.

## Formatos aceitos

- `legacy_lr`: formato antigo das quatro LRs exportadas dos estudos. Preserva TF-IDF, pesos, calibração e proteção para vocabulário desconhecido. Não use esse formato para cadastrar um KNN.
- `sklearn_pipeline`: pipeline binário completo. Pode ser LR, KNN, MLP ou outro classificador com o contrato descrito acima. Não ganha normalização, calibração ou detecção de vocabulário desconhecido por fora do pipeline. A API retorna `coverage: null`, e a interface informa que a cobertura não está disponível.

Se o modelo usa outro formato, como PyTorch ou um serviço remoto, será necessário implementar um adaptador em `prediction/adapters.py` e registrá-lo em `ADAPTERS`, no arquivo `prediction/registry.py`. O contrato é `TextClassifier`: retornar probabilidades de não confiável e, opcionalmente, cobertura. Não precisa mexer no formulário ou nas animações.

Carregue apenas arquivos da equipe cuja origem foi conferida. `joblib.load` pode executar código; o hash detecta alteração do arquivo, mas não torna um arquivo desconhecido seguro. O site não recebe upload de modelos.
