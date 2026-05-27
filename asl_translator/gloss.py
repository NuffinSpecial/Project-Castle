"""Tools to convert normalised English tokens into an ASL gloss."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field


@dataclass
class GlossConfig:
    """Configuration object used by :class:`GlossTranslator`."""

    drop_words: Iterable[str] = field(
        default_factory=lambda: {
            "a",
            "an",
            "the",
            "is",
            "are",
            "am",
            "was",
            "were",
            "be",
            "to",
            "do",
            "does",
            "did",
            "of",
            "and",
            "on",
            "in",
            "at",
            "over",  # directional particle in "over there" (locative = THERE)
            # Tense/mood modals often dropped when gloss already marks time (FUTURE, etc.)
            "would",
            "should",
            "will",
            "shall",
        }
    )
    substitutions: dict[str, str] = field(
        default_factory=lambda: {
            "i": "ME",
            "me": "ME",
            "my": "MY",
            "mine": "MY",
            "you": "YOU",
            "your": "YOUR",
            "yours": "YOUR",
            "he": "HE",
            "him": "HE",
            "his": "HIS",
            "she": "SHE",
            "her": "HER",
            "hers": "HER",
            "we": "WE",
            "us": "WE",
            "our": "OUR",
            "they": "THEY",
            "them": "THEY",
            "their": "THEIR",
            "will": "FUTURE",
            "shall": "FUTURE",
            "yesterday": "PAST",
            "today": "NOW",
            "tomorrow": "FUTURE",
            "want": "WANT",
            "wants": "WANT",
            "wanted": "WANT",
            "why": "WHY",
            "what": "WHAT",
            "when": "WHEN",
            "where": "WHERE",
            "who": "WHO",
            "whom": "WHOM",
            "whose": "WHOSE",
            "how": "HOW",
            "which": "WHICH",
            "monday": "MONDAY",
            "tuesday": "TUESDAY",
            "wednesday": "WEDNESDAY",
            "thursday": "THURSDAY",
            "friday": "FRIDAY",
            "saturday": "SATURDAY",
            "sunday": "SUNDAY",
            "there": "THERE",
            "here": "HERE",
            "go": "GO",
            "goes": "GO",
            "went": "GO",
            "going": "GO",
            "can": "CAN",
            "could": "CAN",
            "may": "MAY",
            "must": "MUST",
            "might": "MIGHT",
        }
    )
    emphasise_negation: bool = True


class GlossTranslator:
    """Translate normalised English tokens into a rough ASL gloss.

    Rule-based and deterministic; designed to pair with NLP lemmas and a community
    sign catalog.
    """

    def __init__(self, config: GlossConfig | None = None) -> None:
        self.config = config or GlossConfig()

    def translate(self, tokens: Iterable[str]) -> list[str]:
        gloss_tokens: list[str] = []
        for token in tokens:
            if token in self.config.drop_words:
                continue

            if token in self.config.substitutions:
                gloss_tokens.append(self.config.substitutions[token])
                continue

            if self.config.emphasise_negation and token in {"not", "never", "no"}:
                gloss_tokens.append(token.upper() + "++")
                continue

            gloss_tokens.append(token.upper())

        return self._dedupe_consecutive(gloss_tokens)

    @staticmethod
    def _dedupe_consecutive(tokens: list[str]) -> list[str]:
        if not tokens:
            return tokens
        deduped = [tokens[0]]
        for token in tokens[1:]:
            if token != deduped[-1]:
                deduped.append(token)
        return deduped
