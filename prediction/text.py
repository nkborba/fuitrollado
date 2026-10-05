"""Limpeza compartilhada pela API e pelas LRs exportadas dos estudos."""

import re
import unicodedata

TYPOGRAPHIC_REPLACEMENTS = str.maketrans(
    {
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "–": "-",
        "—": "-",
        "\u200b": "",
    }
)
LETTER = r"[^\W\d_]"
LETTER_NUMBER_BOUNDARY = re.compile(rf"(?<={LETTER})(?=\d)|(?<=\d)(?={LETTER})")


def clean(text: str) -> str:
    """Uniformiza espaços sem mudar palavras, caixa ou números."""
    return " ".join(str(text).split())


def normalize(text: str) -> str:
    """Repete a normalização usada no treino das variantes normalizadas."""
    text = unicodedata.normalize("NFKC", str(text)).translate(TYPOGRAPHIC_REPLACEMENTS)
    return clean(LETTER_NUMBER_BOUNDARY.sub(" ", text)).lower()
