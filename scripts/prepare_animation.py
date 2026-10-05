"""Recortes reproduzíveis. Requer Pillow; não modifica as folhas originais."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "assets/sprites-v1"
OUTPUT_DIR = ROOT / "web/assets/animation"


def prepare_troll_frames():
    troll = Image.open(SOURCE_DIR / "troll-movimento.png").convert("RGBA")
    # A divisão inferior fica em x=700, depois da ponta da marreta (x=661).
    # Pivôs medidos no cinto e no piso, não no centro da caixa da marreta.
    poses = [
        ("enter", (85, 70, 570, 600), (355, 585)),
        ("prepare", (710, 40, 1120, 600), (945, 585)),
        ("strike", (45, 690, 685, 1180), (282, 1166)),
        ("recover", (745, 660, 1215, 1180), (938, 1167)),
    ]
    for name, box, (hip, ground) in poses:
        part = troll.crop(box)
        part.putalpha(part.getchannel("A").point(lambda a: 0 if a < 12 else a))
        part = part.resize(tuple(round(v * 1.2) for v in part.size), Image.Resampling.NEAREST)
        frame = Image.new("RGBA", (900, 760))
        frame.alpha_composite(
            part, (round(350 + (box[0] - hip) * 1.2), round(720 + (box[1] - ground) * 1.2))
        )
        if name == "recover":
            # A folha original desenhou a cabeça no prolongamento do cabo.
            # Integra somente a marreta corrigida; corpo, mão e botas ficam intactos.
            corrected = Image.open(SOURCE_DIR / "troll-recover-corrigido.png").convert("RGBA")
            corrected = corrected.resize(frame.size, Image.Resampling.NEAREST)
            corrected.putalpha(corrected.getchannel("A").point(lambda a: 0 if a < 12 else a))
            aligned = Image.new("RGBA", frame.size)
            aligned.alpha_composite(corrected, (-6, 0))
            mask = Image.new("L", frame.size)
            ImageDraw.Draw(mask).polygon(
                [
                    (490, 520),
                    (540, 520),
                    (600, 490),
                    (900, 490),
                    (900, 760),
                    (525, 760),
                    (525, 686),
                    (475, 650),
                    (460, 590),
                    (475, 550),
                ],
                fill=255,
            )
            frame = Image.composite(aligned, frame, mask)
        frame.save(OUTPUT_DIR / f"troll-{name}.png", optimize=True)


def prepare_gamer_overlays():
    # Aproveita as expressões sem substituir cabeça, mãos ou cadeira.
    # O sprite neutro permanece sob estas camadas: nenhum salto de escala/apoio.
    gamer = Image.open(SOURCE_DIR / "gamer-tonto.png").convert("RGBA")
    eyes = [
        ("impact", (236, 176, 268, 215)),
        ("dizzy-a", (711, 182, 752, 226)),
        ("dizzy-b", (247, 901, 292, 951)),
        ("recover", (710, 916, 754, 963)),
    ]
    for name, box in eyes:
        patch = gamer.crop(box).resize((66, 86), Image.Resampling.NEAREST)
        mask = Image.new("L", patch.size)
        ImageDraw.Draw(mask).rounded_rectangle((1, 1, 64, 84), radius=12, fill=255)
        patch.putalpha(mask.filter(ImageFilter.GaussianBlur(1.2)))
        layer = Image.new("RGBA", (1024, 1536))
        layer.alpha_composite(patch, (479, 259))
        layer.save(OUTPUT_DIR / f"gamer-{name}.png", optimize=True)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    prepare_troll_frames()
    prepare_gamer_overlays()


if __name__ == "__main__":
    main()
