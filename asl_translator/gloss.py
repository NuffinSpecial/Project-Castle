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
            "yesterday": "PAST",
            "today": "NOW",
            "tomorrow": "FUTURE",
        }
    )
    emphasise_negation: bool = True


class GlossTranslator:
    """Translate normalised English tokens into a rough ASL gloss.

    The implementation is intentionally rule-based to make it deterministic and
    extendable. The goal is not to perfectly replicate a human translator but to
    provide infrastructure for experimentation and future improvements.
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

        return self._move_time_expression(gloss_tokens)

    def _move_time_expression(self, tokens: list[str]) -> list[str]:
        """Move simple time indicators to the start of the gloss."""

        if not tokens:
            return tokens

        time_keywords = {"PAST", "NOW", "FUTURE", "YESTERDAY", "TODAY", "TOMORROW"}
        # also allow explicit year/month/day tokens
        time_tokens = {
            "MONDAY",
            "TUESDAY",
            "WEDNESDAY",
            "THURSDAY",
            "FRIDAY",
            "SATURDAY",
            "SUNDAY",
        }
        reordered: list[str] = []
        time_buffer: list[str] = []

        for token in tokens:
            if token in time_keywords or token in time_tokens:
                time_buffer.append(token)
            else:
                reordered.append(token)

        if time_buffer:
            return time_buffer + reordered
        return tokens
