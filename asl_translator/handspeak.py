"""Utilities for creating HandSpeak links for gloss tokens."""

from __future__ import annotations

from collections.abc import Iterable
from urllib.parse import quote_plus


class HandSpeakLinker:
    """Generate URLs that point to the HandSpeak dictionary."""

    BASE_SEARCH_URL = "https://www.handspeak.com/word/search/index.php?word="

    def __init__(self, overrides: dict[str, str] | None = None) -> None:
        # Overrides map a gloss token to a full URL. This allows using canonical
        # entries when they differ from the default search behaviour.
        self.overrides = overrides or {}

    def links_for(self, gloss_tokens: Iterable[str]) -> list[str]:
        return [self._link_for_token(token) for token in gloss_tokens]

    def _link_for_token(self, token: str) -> str:
        if token in self.overrides:
            return self.overrides[token]

        return f"{self.BASE_SEARCH_URL}{quote_plus(token.lower())}"
