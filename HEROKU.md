# Rodar no Heroku

O repo já tem `Procfile`, `.python-version` e `requirements.txt`. O site e a API rodam juntos, sem banco de dados. Deixe `web/config.js` com `apiBase` vazio.

## Antes de publicar

Ative a [oferta de estudante](https://www.heroku.com/github-students/) e confira os créditos em Account Settings > Billing. Não considere o benefício ativo apenas por ter enviado a solicitação. Recursos pagos podem ser cobrados antes da aprovação, acima do crédito ou depois que ele expirar.

## Pelo painel

1. Envie o commit de configuração para o GitHub com `git push`.
2. No Heroku, abra New > Create new app. Escolha um nome disponível e a região.
3. Na aba Deploy, escolha GitHub, conecte a conta e selecione `nkborba/fuitrollado`.
4. Em Manual deploy, selecione `main` e clique em Deploy Branch.
5. Aguarde o build terminar. O Heroku instala as dependências e reconhece o processo `web` do Procfile.
6. Na aba Resources, confira o tipo de dyno e deixe apenas um processo `web` ativo. Se os créditos estiverem aprovados, o Basic é a opção recomendada para evitar suspensão por inatividade. Revise o preço exibido antes de confirmar.
7. Clique em Open app. Acesse também `/api/health`: deve retornar `ready: true`.
8. No site, analise uma frase com a comparação das quatro versões marcada.

Para atualizar depois, faça push para o GitHub e use Deploy Branch novamente. Também é possível habilitar deploy automático, preferencialmente aguardando os testes do GitHub Actions.

## Se der erro

- Veja More > View logs e o log do build.
- `H14`: confira se o processo `web` está ativado em Resources.
- Erro ao instalar dependências: confirme que `.python-version` e `requirements.txt` estão na raiz do repo e que o buildpack é Python.
- Não configure `PORT` manualmente. O Heroku fornece essa variável.
- Não habilite debug nem crie bancos/add-ons para este site; eles não são necessários.

O comando usa um worker e duas threads para não duplicar os modelos em vários processos. A versão do Python fica na família 3.12, permitindo que o Heroku aplique atualizações de segurança da mesma família.

Documentação: [Python no Heroku](https://devcenter.heroku.com/articles/python-support), [versão do Python](https://devcenter.heroku.com/articles/python-runtimes), [Gunicorn](https://devcenter.heroku.com/articles/python-gunicorn).
