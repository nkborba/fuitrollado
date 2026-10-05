# Integração dos sprites

`README.md`, `PROMPTS.md` e as duas folhas PNG desta pasta são cópias intactas
dos arquivos fornecidos. Os cinco assets originais de `web/assets/` também foram
preservados. Esta pasta não é servida pela aplicação.

Para reproduzir os oito PNGs derivados, instale Pillow em um ambiente de trabalho
e execute `python scripts/prepare_animation.py` na raiz do repositório.
Pillow não é uma dependência do site nem do backend.

O troll usa regiões específicas, inclusive a extensão da marreta além de x=627
no quadro inferior esquerdo. Todos os quadros usam a mesma escala de 1,2, uma
tela RGBA de 900 × 760, o piso em y=720 e o apoio do corpo em x=350.
A postura agachada durante o golpe é intencional. Somente resíduos de alpha
abaixo de 12 são removidos no troll; as bordas semitransparentes são mantidas.

As cadeiras e os corpos da folha do gamer não são suficientemente consistentes
para substituição integral. Por isso, os quatro recortes dos olhos são camadas
RGBA na tela original de 1024 × 1536. A cabeça, o corpo, a cadeira e as mãos
continuam sendo os pixels do sprite neutro. Os passarinhos são um SVG em pixel art
com órbita elíptica e asas animadas em CSS, sem GIF e sem temporizadores contínuos
em JavaScript. O reflexo da tela continua acima das expressões e mantém sua
máscara original. A cabeça da marreta na pose final recebeu uma correção local
com a ferramenta integrada de imagens: agora o cabo entra na lateral da cabeça,
formando um T. O script aplica uma máscara somente na região da marreta e
preserva os pixels do corpo, da mão e das botas. A imagem editada e o prompt
estão em `troll-recover-corrigido.png` e `CORRECAO-MARRETA.md`.

## Linha do tempo

| Tempo | Troll | Gamer |
| --- | --- | --- |
| 0 ms | Portal abre | Neutro |
| 450 ms | Aparece diante do portal em 250 ms, sem deslocamento lateral ou mudança de escala | Neutro |
| 1200 ms | Prepara a marreta | Neutro |
| 1900 ms | Golpe e brilho de impacto | Olho fechado |
| 2100 ms em diante | Marreta abaixada, portal aberto | Confuso, passarinhos circulando continuamente |

`scene-animation.js` controla ambos os personagens no mesmo callback de
`requestAnimationFrame`. Cada mudança de estado cancela o callback e invalida
qualquer espera por decodificação anterior. Repetir “não confiável” recomeça
desde o portal. As imagens são decodificadas antes do primeiro quadro.
Movimento reduzido exibe troll, gamer tonto e passarinhos estáticos; ocultar a aba
pausa os passarinhos. Eles retomam ao voltar à aba ou desativar movimento reduzido,
sem repetir o golpe. A tontura só acaba com uma mudança de estado ou nova análise.
O portal conserva a geometria anterior (27% de largura no desktop, 33% no celular)
e não fecha após o golpe. Os controles de prévia não executam inferência e levam
o cenário para a área visível.

## Verificação

- `node --test tests/scene-animation.test.cjs`: sequência, sincronismo, estados
  permitidos, cancelamento em cada fase, repetição, decodificação pendente,
  tontura persistente, movimento reduzido, aba oculta e retomada do movimento.
- `python -m unittest discover -s tests -v`: previsões, hashes e contrato da API.
- Navegador: desktop 1280 px e celular 390 px, golpe, tontura, recuperação,
  repetição e interrupção, incluindo respostas reais dos três resultados.

Limite artístico: são quatro poses do troll, com transições em passos;
não há interpolação desenhada dos braços. O corpo do gamer fica fixo de
propósito para preservar o alinhamento com a mesa e eliminar oscilações da cadeira.

Para reverter, reverta o commit da animação. Código, folhas originais e arquivos
derivados ficam separados; modelos e regras de inferência não foram alterados.
