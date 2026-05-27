"""High level pipeline for translating English into ASL gloss with community signs."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from .gloss import GlossTranslator
from .nlp.analyzer import analyze_sentence
from .nlp.flexibility import find_mutable_groups
from .nlp.mwe import extract_mwe
from .nlp.transfer import apply_transfer_rules
from .signs import CommunitySignCatalog, CommunitySignLinker


@dataclass
class TranslationResult:
    """Container for the full translation pipeline output."""

    original_sentence: str
    tokens: list[str]
    normalized_tokens: list[str]
    lemmas: list[str]
    gloss_tokens: list[str]
    links: list[str | None]
    sign_available: list[bool]
    analysis_engine: str
    pos_tags: list[str] = field(default_factory=list)
    mutable_groups: list[dict] = field(default_factory=list)

    @property
    def sign_urls(self) -> list[str | None]:
        """Alias for community sign video paths (``links``)."""

        return self.links


class TranslationPipeline:
    """Run the full translation flow from sentence to community sign references."""

    def __init__(
        self,
        gloss_translator: GlossTranslator | None = None,
        linker: CommunitySignLinker | None = None,
        catalog: CommunitySignCatalog | None = None,
        *,
        use_spacy: bool = True,
    ) -> None:
        self.catalog = catalog or CommunitySignCatalog()
        self.gloss_translator = gloss_translator or GlossTranslator()
        self.linker = linker or CommunitySignLinker(self.catalog)
        self.use_spacy = use_spacy

    def translate(self, sentence: str) -> TranslationResult:
        analysis = analyze_sentence(sentence, prefer_spacy=self.use_spacy)
        raw_tokens = analysis.surface_tokens
        lemmas = analysis.lemmas
        mwe_gloss, remaining = extract_mwe(lemmas)
        gloss_body = self.gloss_translator.translate(remaining)
        is_question = sentence.strip().endswith("?")
        gloss_tokens = apply_transfer_rules(mwe_gloss + gloss_body, is_question=is_question)
        mutable_groups = [group.to_dict() for group in find_mutable_groups(gloss_tokens)]
        links = self.linker.links_for(gloss_tokens)
        sign_available = self.linker.availability_for(gloss_tokens)

        return TranslationResult(
            original_sentence=sentence,
            tokens=raw_tokens,
            normalized_tokens=lemmas,
            lemmas=lemmas,
            gloss_tokens=gloss_tokens,
            links=links,
            sign_available=sign_available,
            analysis_engine=analysis.engine,
            pos_tags=[token.pos for token in analysis.tokens],
            mutable_groups=mutable_groups,
        )

    def translate_many(self, sentences: Sequence[str]) -> list[TranslationResult]:
        return [self.translate(sentence) for sentence in sentences]


def run_pipeline(sentences: Iterable[str]) -> list[TranslationResult]:
    pipeline = TranslationPipeline()
    return pipeline.translate_many(list(sentences))


def default_data_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "data"
