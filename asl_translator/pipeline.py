"""High level pipeline for translating English into ASL gloss with links."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from .gloss import GlossTranslator
from .handspeak import HandSpeakLinker
from .tokenizer import normalize, tokenize


@dataclass
class TranslationResult:
    """Container for the full translation pipeline output."""

    original_sentence: str
    tokens: list[str]
    normalized_tokens: list[str]
    gloss_tokens: list[str]
    links: list[str]


class TranslationPipeline:
    """Run the full translation flow from sentence to HandSpeak links."""

    def __init__(
        self,
        gloss_translator: GlossTranslator | None = None,
        linker: HandSpeakLinker | None = None,
    ) -> None:
        self.gloss_translator = gloss_translator or GlossTranslator()
        self.linker = linker or HandSpeakLinker()

    def translate(self, sentence: str) -> TranslationResult:
        raw_tokens = tokenize(sentence)
        normalized_tokens = normalize(raw_tokens)
        gloss_tokens = self.gloss_translator.translate(normalized_tokens)
        links = self.linker.links_for(gloss_tokens)

        return TranslationResult(
            original_sentence=sentence,
            tokens=raw_tokens,
            normalized_tokens=normalized_tokens,
            gloss_tokens=gloss_tokens,
            links=links,
        )

    def translate_many(self, sentences: Sequence[str]) -> list[TranslationResult]:
        return [self.translate(sentence) for sentence in sentences]


def run_pipeline(sentences: Iterable[str]) -> list[TranslationResult]:
    pipeline = TranslationPipeline()
    return pipeline.translate_many(list(sentences))
