"""Flask application exposing the ASL translation pipeline via a web UI."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Sequence

from flask import Flask, jsonify, render_template, request

from asl_translator.pipeline import TranslationPipeline, TranslationResult


def _sanitize_sentences(raw_sentences: Iterable[str | None]) -> List[str]:
    """Return a list of trimmed, non-empty sentences."""

    sanitized: List[str] = []
    for sentence in raw_sentences:
        if sentence is None:
            continue
        if not isinstance(sentence, str):
            raise TypeError("Each sentence must be a string")
        stripped = sentence.strip()
        if stripped:
            sanitized.append(stripped)
    return sanitized


def _format_results(results: Sequence[TranslationResult]) -> List[dict]:
    """Serialize :class:`TranslationResult` instances to dictionaries."""

    formatted: List[dict] = []
    for result in results:
        formatted.append(
            {
                "originalSentence": result.original_sentence,
                "tokens": result.tokens,
                "normalizedTokens": result.normalized_tokens,
                "glossTokens": result.gloss_tokens,
                "links": result.links,
            }
        )
    return formatted


def create_app() -> Flask:
    """Return a configured Flask application."""

    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "templates"),
        static_folder=str(Path(__file__).parent / "static"),
    )
    pipeline = TranslationPipeline()

    @app.get("/")
    def index() -> str:
        return render_template("index.html")

    @app.post("/translate")
    def translate():  # type: ignore[override]
        payload = request.get_json(silent=True) or {}
        raw_sentences = payload.get("sentences")

        if isinstance(raw_sentences, str):
            raw_sentences = [raw_sentences]

        if raw_sentences is None:
            return jsonify({"error": "No sentences provided."}), 400

        if not isinstance(raw_sentences, list):
            return jsonify({"error": "Sentences must be provided as a list or string."}), 400

        try:
            sentences = _sanitize_sentences(raw_sentences)
        except TypeError as exc:  # pragma: no cover - handled for robustness
            return jsonify({"error": str(exc)}), 400

        if not sentences:
            return jsonify({"error": "No sentences provided."}), 400

        results = pipeline.translate_many(sentences)
        return jsonify({"sentences": sentences, "results": _format_results(results)})

    return app


app = create_app()
