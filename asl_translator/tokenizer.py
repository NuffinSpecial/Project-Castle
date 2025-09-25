"""Tokenization utilities for the ASL translator pipeline."""
from __future__ import annotations

import re
from typing import Iterable, List

_WORD_RE = re.compile(r"[A-Za-z']+")


def tokenize(sentence: str) -> List[str]:
    """Tokenise a raw English sentence.

    The tokenizer keeps apostrophes that are part of the word (e.g. "don't") and
    filters out any other punctuation. Numbers are currently removed from the
    output because HandSpeak typically indexes lexical entries by word rather
    than by digit.
    """

    if not sentence:
        return []

    tokens = [match.group(0) for match in _WORD_RE.finditer(sentence)]
    return tokens


def normalize(tokens: Iterable[str]) -> List[str]:
    """Normalize tokens prior to gloss translation."""

    return [token.lower() for token in tokens]
