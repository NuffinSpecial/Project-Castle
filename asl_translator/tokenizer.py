"""Tokenization utilities for the ASL translator pipeline."""

from __future__ import annotations

import re
from collections.abc import Iterable

_WORD_RE = re.compile(r"[A-Za-z']+")


def tokenize(sentence: str) -> list[str]:
    """Tokenise a raw English sentence.

    The tokenizer keeps apostrophes that are part of the word (e.g. "don't") and
    filters out any other punctuation. Numbers are currently removed from the
    output because the gloss lexicon indexes lexical entries by word rather
    than by digit. Prefer :func:`asl_translator.nlp.analyzer.analyze_sentence`.
    """

    if not sentence:
        return []

    tokens = [match.group(0) for match in _WORD_RE.finditer(sentence)]
    return tokens


def normalize(tokens: Iterable[str]) -> list[str]:
    """Normalize tokens prior to gloss translation."""

    return [token.lower() for token in tokens]
