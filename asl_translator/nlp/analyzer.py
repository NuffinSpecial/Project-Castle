"""English sentence analysis (spaCy with regex fallback)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

_WORD_RE = re.compile(r"[A-Za-z0-9']+")

_SPACY_MODEL = "en_core_web_sm"


@dataclass(frozen=True)
class AnalyzedToken:
    text: str
    lemma: str
    pos: str


@dataclass(frozen=True)
class SentenceAnalysis:
    original: str
    tokens: list[AnalyzedToken]
    engine: str

    @property
    def lemmas(self) -> list[str]:
        return [token.lemma for token in self.tokens]

    @property
    def surface_tokens(self) -> list[str]:
        return [token.text for token in self.tokens]


def _regex_analyze(sentence: str) -> SentenceAnalysis:
    if not sentence.strip():
        return SentenceAnalysis(original=sentence, tokens=[], engine="regex")

    tokens: list[AnalyzedToken] = []
    for match in _WORD_RE.finditer(sentence):
        text = match.group(0)
        lower = text.lower()
        lemma = lower
        if lower.isdigit():
            lemma = _number_lemma(lower)
        tokens.append(AnalyzedToken(text=text, lemma=lemma, pos=_guess_pos(lower)))

    return SentenceAnalysis(original=sentence, tokens=tokens, engine="regex")


def _number_lemma(value: str) -> str:
    number_words = {
        "0": "zero",
        "1": "one",
        "2": "two",
        "3": "three",
        "4": "four",
        "5": "five",
        "6": "six",
        "7": "seven",
        "8": "eight",
        "9": "nine",
        "10": "ten",
    }
    return number_words.get(value, value)


def _guess_pos(token: str) -> str:
    if token in {"i", "you", "he", "she", "we", "they", "me", "him", "her", "us", "them"}:
        return "PRON"
    if token in {"will", "have", "has", "had", "do", "does", "did"}:
        return "AUX"
    if token in {"not", "never", "no"}:
        return "PART"
    if token.isdigit():
        return "NUM"
    return "X"


@lru_cache(maxsize=1)
def _load_spacy():
    import spacy

    try:
        return spacy.load(_SPACY_MODEL)
    except OSError:
        return spacy.blank("en")


def _spacy_analyze(sentence: str) -> SentenceAnalysis:
    nlp = _load_spacy()
    doc = nlp(sentence)
    tokens: list[AnalyzedToken] = []
    for token in doc:
        if token.is_space:
            continue
        if token.is_punct and not token.text.isalnum():
            continue
        text = token.text
        lemma = token.lemma_.lower().strip()
        if not lemma or lemma == "-pron-":
            lemma = text.lower()
        if text.isdigit():
            lemma = _number_lemma(text)
        pos = token.pos_ if hasattr(token, "pos_") and token.pos_ else "X"
        tokens.append(AnalyzedToken(text=text, lemma=lemma, pos=pos))

    engine = _SPACY_MODEL if nlp.meta.get("name") else "spacy-blank"
    return SentenceAnalysis(original=sentence, tokens=tokens, engine=engine)


def analyze_sentence(sentence: str, *, prefer_spacy: bool = True) -> SentenceAnalysis:
    """Return lemmas and POS tags for a sentence."""

    if not sentence or not sentence.strip():
        return SentenceAnalysis(original=sentence, tokens=[], engine="regex")

    if prefer_spacy:
        try:
            return _spacy_analyze(sentence)
        except Exception:  # pragma: no cover - fallback safety
            return _regex_analyze(sentence)
    return _regex_analyze(sentence)
