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
continuam sendo os pixels do sprite neutro. As estrelas são uma camada CSS
independente. O reflexo da tela continua acima das expressões e mantém sua
máscara original. Não houve nova geração de imagens.

## Linha do tempo

| Tempo | Troll | Gamer |
| --- | --- | --- |
| 0 ms | Portal abre | Neutro |
| 450 ms | Entrada, sem mudança de escala | Neutro |
| 1200 ms | Prepara a marreta | Neutro |
| 1900 ms | Golpe e brilho de impacto | Olho fechado |
| 2100–4100 ms | Marreta abaixada | Espirais e estrelas |
| 4100 ms | Recuperação, portal fecha | Expressão cansada, uma estrela |
| 4700 ms | Pose final estática | Neutro |

`scene-animation.js` controla ambos os personagens no mesmo callback de
`requestAnimationFrame`. Cada mudança de estado cancela o callback e invalida
qualquer espera por decodificação anterior. Repetir “não confiável” recomeça
desde o portal. As imagens são decodificadas antes do primeiro quadro.
Movimento reduzido exibe troll e gamer tonto estáticos; ocultar a aba também
interrompe a sequência. Os controles de prévia não executam inferência e levam
o cenário para a área visível.

## Verificação

- `node --test tests/scene-animation.test.cjs`: sequência, sincronismo, estados
  permitidos, cancelamento em cada fase, repetição, decodificação pendente,
  movimento reduzido e aba oculta.
- `python -m unittest discover -s tests -v`: previsões, hashes e contrato da API.
- Navegador: desktop 1280 px e celular 390 px, golpe, tontura, recuperação,
  repetição e interrupção, incluindo respostas reais dos três resultados.

Limite artístico: são quatro poses do troll, com transições em passos;
não há interpolação desenhada dos braços. O corpo do gamer fica fixo de
propósito para preservar o alinhamento com a mesa e eliminar oscilações da cadeira.

Para reverter, reverta o commit da animação. Código, folhas originais e arquivos
derivados ficam separados; modelos e regras de inferência não foram alterados.
