"""Recortes reproduzíveis. Requer Pillow; não modifica as folhas originais."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'assets/sprites-v1'
OUT = ROOT / 'web/assets/animation'
OUT.mkdir(parents=True, exist_ok=True)
troll = Image.open(SOURCE / 'troll-movimento.png').convert('RGBA')
# A divisão inferior fica em x=700, depois da ponta da marreta (x=661).
# Pivôs medidos no cinto e no piso, não no centro da caixa da marreta.
poses = [
    ('enter', (85, 70, 570, 600), (355, 585)),
    ('prepare', (710, 40, 1120, 600), (945, 585)),
    ('strike', (45, 690, 685, 1180), (282, 1166)),
    ('recover', (745, 660, 1215, 1180), (938, 1167)),
]
for name, box, (hip, ground) in poses:
    part = troll.crop(box)
    part.putalpha(part.getchannel('A').point(lambda a: 0 if a < 12 else a))
    part = part.resize(tuple(round(v * 1.2) for v in part.size), Image.Resampling.NEAREST)
    frame = Image.new('RGBA', (900, 760))
    frame.alpha_composite(part, (round(350 + (box[0]-hip)*1.2), round(720 + (box[1]-ground)*1.2)))
    frame.save(OUT / f'troll-{name}.png', optimize=True)

# Aproveita as expressões sem substituir cabeça, mãos ou cadeira.
# O sprite neutro permanece sob estas camadas: nenhum salto de escala/apoio.
gamer = Image.open(SOURCE / 'gamer-tonto.png').convert('RGBA')
eyes = [
    ('impact', (236, 176, 268, 215)),
    ('dizzy-a', (711, 182, 752, 226)),
    ('dizzy-b', (247, 901, 292, 951)),
    ('recover', (710, 916, 754, 963)),
]
for name, box in eyes:
    patch = gamer.crop(box).resize((66, 86), Image.Resampling.NEAREST)
    mask = Image.new('L', patch.size)
    ImageDraw.Draw(mask).rounded_rectangle((1, 1, 64, 84), radius=12, fill=255)
    patch.putalpha(mask.filter(ImageFilter.GaussianBlur(1.2)))
    layer = Image.new('RGBA', (1024, 1536))
    layer.alpha_composite(patch, (479, 259))
    layer.save(OUT / f'gamer-{name}.png', optimize=True)
