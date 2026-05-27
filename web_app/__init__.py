"""Flask application exposing the ASL translation pipeline via a web UI."""

from __future__ import annotations

import json
import uuid
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime
from pathlib import Path

from asl_translator.pipeline import TranslationPipeline, TranslationResult
from asl_translator.signs import CommunitySignCatalog
from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_DATA_DIR = _PROJECT_ROOT / "data"
_SUBMISSIONS_DIR = _DATA_DIR / "submissions"
_MAX_UPLOAD_BYTES = 25 * 1024 * 1024
_ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov"}


def _sanitize_sentences(raw_sentences: Iterable[str | None]) -> list[str]:
    """Return a list of trimmed, non-empty sentences."""

    sanitized: list[str] = []
    for sentence in raw_sentences:
        if sentence is None:
            continue
        if not isinstance(sentence, str):
            raise TypeError("Each sentence must be a string")
        stripped = sentence.strip()
        if stripped:
            sanitized.append(stripped)
    return sanitized


def _format_results(results: Sequence[TranslationResult]) -> list[dict]:
    """Serialize :class:`TranslationResult` instances to dictionaries."""

    formatted: list[dict] = []
    for result in results:
        formatted.append(
            {
                "originalSentence": result.original_sentence,
                "tokens": result.tokens,
                "normalizedTokens": result.normalized_tokens,
                "lemmas": result.lemmas,
                "posTags": result.pos_tags,
                "glossTokens": result.gloss_tokens,
                "links": result.links,
                "signAvailable": result.sign_available,
                "analysisEngine": result.analysis_engine,
                "mutableGroups": result.mutable_groups,
            }
        )
    return formatted


def _allowed_video(filename: str) -> bool:
    return Path(filename).suffix.lower() in _ALLOWED_VIDEO_EXTENSIONS


def create_app() -> Flask:
    """Return a configured Flask application."""

    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "templates"),
        static_folder=str(Path(__file__).parent / "static"),
    )
    _SUBMISSIONS_DIR.mkdir(parents=True, exist_ok=True)
    catalog = CommunitySignCatalog(_DATA_DIR)
    pipeline = TranslationPipeline(catalog=catalog)

    @app.get("/")
    def home() -> str:
        return render_template("home.html", active_page="home")

    @app.get("/translation")
    def translation_page() -> str:
        return render_template("translation.html", active_page="home")

    @app.get("/submit")
    def submit_page() -> str:
        return render_template("submit.html", active_page="submit")

    @app.get("/info")
    def info_page() -> str:
        return render_template("info.html", active_page="info")

    @app.get("/settings")
    def settings_page() -> str:
        return render_template("settings.html", active_page="settings")

    @app.get("/api/signs")
    def list_signs():  # type: ignore[override]
        entries = catalog.list_entries()
        return jsonify(
            {
                "signs": [
                    {
                        "gloss": entry.gloss,
                        "english": entry.english,
                        "videoUrl": entry.video_api_path,
                    }
                    for entry in entries
                ]
            }
        )

    @app.get("/api/signs/<gloss>/video")
    def sign_video(gloss: str):  # type: ignore[override]
        video_path = catalog.video_path(gloss)
        if video_path is None:
            return jsonify({"error": "No community video for this sign yet."}), 404
        return send_file(video_path, conditional=True)

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

    @app.post("/api/submissions")
    def submit_translation():  # type: ignore[override]
        english = (request.form.get("english") or "").strip()
        notes = (request.form.get("notes") or "").strip()
        gloss = (request.form.get("gloss") or "").strip() or None

        if not english:
            return jsonify({"error": "English word or phrase is required."}), 400

        submission_id = uuid.uuid4().hex
        submission_dir = _SUBMISSIONS_DIR / submission_id
        submission_dir.mkdir(parents=True, exist_ok=True)

        video_file = request.files.get("video")
        saved_video: str | None = None
        if video_file and video_file.filename:
            if not _allowed_video(video_file.filename):
                return jsonify({"error": "Unsupported video format. Use MP4, WebM, or MOV."}), 400

            video_file.seek(0, 2)
            size = video_file.tell()
            video_file.seek(0)
            if size > _MAX_UPLOAD_BYTES:
                return jsonify({"error": "Video file exceeds 25 MB limit."}), 400

            filename = secure_filename(video_file.filename)
            destination = submission_dir / filename
            video_file.save(destination)
            saved_video = filename

        metadata = {
            "id": submission_id,
            "english": english,
            "gloss": gloss or english,
            "notes": notes,
            "video": saved_video,
            "submittedAt": datetime.now(UTC).isoformat(),
        }
        (submission_dir / "metadata.json").write_text(
            json.dumps(metadata, indent=2),
            encoding="utf-8",
        )

        if saved_video:
            entry = catalog.register(
                english=english,
                gloss=gloss or english,
                submission_id=submission_id,
                video=saved_video,
            )
            video_url = entry.video_api_path
        else:
            video_url = None

        return jsonify(
            {
                "success": True,
                "message": "Thank you! Your sign is live in the community catalog.",
                "id": submission_id,
                "videoUrl": video_url,
            }
        )

    return app


app = create_app()
