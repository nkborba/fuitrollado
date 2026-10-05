# Fui Trollado?

Site do Data Hunters para analisar padrões de credibilidade em textos. Tem o cenário gamer, a equipe e quatro versões da LR para comparar a mesma mensagem.

O modelo não verifica fatos. Uma frase inventada com aparência de anúncio oficial pode receber uma probabilidade alta para a classe confiável. O resultado mostra semelhança com os padrões do corpus, não uma confirmação de verdade.

## Rodar localmente

Precisa de Python 3.12. Os quatro modelos já estão treinados e versionados. Não precisa do dataset, dos notebooks ou da pasta original dos estudos.

```sh
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

No Windows, ative com `.venv\Scripts\activate`. Abra http://127.0.0.1:8765.
Para mudar a porta: `PORT=8766 python app.py` no macOS/Linux.

## O que tem aqui

- `web/`: HTML, CSS, JavaScript e os cinco assets usados no cenário. Fotos da equipe vêm do GitHub, com iniciais como alternativa se não carregarem.
- `app.py`: API Flask e entrega dos arquivos do site.
- `inference.py`: limpeza, representação, LR, Platt e abstenção, sem código de treino.
- `models/`: quatro artefatos congelados, métricas, protocolo e relatório do estudo 10.
- `tests/`: checks de previsões, entradas, CORS e acesso aos arquivos.
- `render.yaml`: configuração para hospedar o site completo no Render.
- `.github/workflows/pages.yml`: publicação manual da interface no GitHub Pages.

## Modelos

| Identificador | Versão |
|---|---|
| `atual` | LR original do estudo 09, TF-IDF de palavras |
| `normalizado` | LR com normalização e números preservados |
| `augmentation` | LR treinada com variações ortográficas |
| `normalizado_char` | LR normalizada com TF-IDF de palavras e caracteres |

Todos usam calibração Platt. Entre 12,5% e 87,5%, sem incluir os limites, o modelo se abstém. Texto sem representação conhecida também recebe inconclusivo. O mínimo continua em 20 caracteres e o máximo em 5.000. A conversa sobre aumentar o mínimo não foi convertida em mudança de regra.

Na preparação deste repo, os estimadores foram extraídos dos artefatos originais sem retreino. Conferimos as previsões em 927 textos DEV e seis sondas. A diferença máxima foi zero nas quatro versões. Isso é um teste de compatibilidade, não uma nova avaliação de desempenho. O holdout não foi utilizado. Os hashes e o registro estão em `models/validacao_exportacao.json`.

O relatório e protocolo são cópias do estudo original; referências a scripts e resultados detalhados pertencem à pasta dos estudos, que não faz parte deste repo. Aqui entram os resultados por fold e o necessário para inferência. Não carregue arquivos joblib de origem desconhecida.

## Heroku

O projeto também está preparado para o Heroku. Veja o passo a passo em [HEROKU.md](HEROKU.md). O `Procfile` inicia o site e os quatro modelos no mesmo serviço; `.python-version` seleciona Python 3.12.

## Alternativa: Render

O GitHub Pages não executa Python. Para publicar tudo junto, recomendo um **Web Service no Render, plano Free**. O `render.yaml` já está pronto:

1. Envie este repo para o GitHub.
2. No Render, crie um Blueprint e conecte `nkborba/fuitrollado`.
3. Revise o plano `Free` e aplique a configuração do `render.yaml`.
4. Aguarde o deploy e abra a URL HTTPS que o Render gerar.

Se preferir criar o Web Service manualmente:

```text
Runtime: Python
Build: pip install -r requirements.txt
Start: gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120
Health check: /api/health
PYTHON_VERSION: 3.12.12
OPENBLAS_NUM_THREADS: 1
OMP_NUM_THREADS: 1
```

O plano gratuito suspende o serviço após 15 minutos sem tráfego. A primeira abertura pode levar cerca de um minuto. A interface espera até 90 segundos pela API. Existem limites de horas e tráfego; confira as condições antes de publicar. É uma opção para demonstração, sem garantia de disponibilidade de produção.

Documentação consultada em 04/10/2026: [Render Free](https://render.com/docs/free), [planos](https://render.com/docs/compute-plans).

## GitHub Pages, se quiser separar a interface

É possível hospedar **a interface** no Pages e manter os modelos no Render:

1. Publique o backend no Render.
2. Em `web/config.js`, coloque `apiBase: 'https://SEU-SERVICO.onrender.com'`.
3. No Render, configure `ALLOWED_ORIGINS=https://nkborba.github.io` (sem `/fuitrollado`). Para mais origens, separe por vírgula. O CORS não é autenticação nem proteção contra abuso.
4. No GitHub, abra Settings > Pages > Source e escolha GitHub Actions.
5. Execute o workflow **Publicar interface no Pages**, na aba Actions.
6. A interface ficará em `https://nkborba.github.io/fuitrollado/` se essa for a configuração da conta e do repo.

O workflow publica somente `web/`, sem os modelos. Sem API configurada, o Pages mostra uma prévia sem análise. Os caminhos de assets são relativos para funcionar no subdiretório `/fuitrollado/`. Para um domínio próprio, configure igualmente a API e a origem autorizada.

Se rodar tudo no Render, deixe `apiBase` vazio e não precisa configurar CORS.

Documentação: [o que o GitHub Pages hospeda](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages).

## Verificar

A animação de “não confiável” usa sprites preparados e uma linha do tempo de
4,7 segundos, com alternativa estática para movimento reduzido. Os controles
“Explorar as animações” permitem repetir e interromper a cena sem analisar texto.
Recortes, alinhamento e instruções para regenerar os assets estão em
[assets/sprites-v1/PREPARACAO.md](assets/sprites-v1/PREPARACAO.md).

```sh
node --test tests/scene-animation.test.cjs
```

```sh
python -m unittest discover -s tests -v
```

A API recebe `POST /api/analyze` com JSON:

```json
{"text":"O governo brasileiro proibiu GTA 6.","model":"normalizado_char","compare":true}
```

`GET /api/models` retorna as métricas do estudo. `GET /api/health` confirma que os modelos carregaram. Textos são processados em memória, sem armazenamento pela aplicação. A hospedagem pode registrar metadados de requisições. Não habilite debug ao publicar.

Os testes automatizados também rodam no GitHub Actions. O deploy no Pages é manual. Nenhuma conta de hospedagem é criada por este repositório.
