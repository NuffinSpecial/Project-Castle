"""Flask application exposing the ASL translation pipeline via a web UI."""

from __future__ import annotations

import os
from collections.abc import Iterable, Sequence
from pathlib import Path

from asl_translator.pipeline import TranslationPipeline, TranslationResult
from asl_translator.signs import CommunitySignCatalog
from flask import Flask, jsonify, render_template, request, send_file
from flask_login import LoginManager, current_user, login_required

from . import db
from .admin_routes import admin_bp
from .auth_routes import auth_bp
from .config import data_dir, secret_key
from .models import User
from .submissions import create_submission

_MAX_UPLOAD_BYTES = 25 * 1024 * 1024


def _sanitize_sentences(raw_sentences: Iterable[str | None]) -> list[str]:
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


def _variant_payload(entry) -> dict:
    context = entry.notes.strip() or entry.english
    return {
        "submissionId": entry.submission_id,
        "videoUrl": entry.video_api_path,
        "english": entry.english,
        "context": context,
    }


def _format_results(
    results: Sequence[TranslationResult],
    catalog: CommunitySignCatalog,
) -> list[dict]:
    formatted: list[dict] = []
    for result in results:
        sign_variants: list[list[dict]] = []
        submission_ids: list[str | None] = []
        links: list[str | None] = []
        sign_available: list[bool] = []

        for token in result.gloss_tokens:
            entries = catalog.lookup_all(token)
            variants = [
                _variant_payload(entry)
                for entry in entries
                if catalog.video_path_for_entry(entry) is not None
            ]
            sign_variants.append(variants)
            if variants:
                links.append(variants[0]["videoUrl"])
                submission_ids.append(variants[0]["submissionId"])
                sign_available.append(True)
            else:
                links.append(None)
                submission_ids.append(None)
                sign_available.append(False)

        formatted.append(
            {
                "originalSentence": result.original_sentence,
                "tokens": result.tokens,
                "normalizedTokens": result.normalized_tokens,
                "lemmas": result.lemmas,
                "posTags": result.pos_tags,
                "glossTokens": result.gloss_tokens,
                "links": links,
                "submissionIds": submission_ids,
                "signVariants": sign_variants,
                "signAvailable": sign_available,
                "analysisEngine": result.analysis_engine,
                "mutableGroups": result.mutable_groups,
            }
        )
    return formatted


def _bootstrap_admin() -> None:
    email = os.environ.get("CASTLE_ADMIN_EMAIL", "").strip().lower()
    password = os.environ.get("CASTLE_ADMIN_PASSWORD", "")
    username = os.environ.get("CASTLE_ADMIN_USERNAME", "admin")
    if not email or not password:
        return
    if db.get_user_by_email(email) is not None:
        return
    db.create_user(email=email, username=username, password=password, is_admin=True)


def create_app() -> Flask:
    root = Path(__file__).parent
    app = Flask(
        __name__,
        template_folder=str(root / "templates"),
        static_folder=str(root / "static"),
    )
    app.config["SECRET_KEY"] = secret_key()
    app.config["MAX_CONTENT_LENGTH"] = _MAX_UPLOAD_BYTES

    db.init_db()
    _bootstrap_admin()

    login_manager = LoginManager()
    login_manager.login_view = "auth.login_page"
    login_manager.login_message = "Please sign in to continue."

    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:
        row = db.get_user_by_id(int(user_id))
        return User(row) if row else None

    login_manager.init_app(app)

    catalog = CommunitySignCatalog(data_dir())
    app.extensions["catalog"] = catalog

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    @app.context_processor
    def inject_user():
        return {"current_user": current_user}

    @app.get("/")
    def home() -> str:
        return render_template("home.html", active_page="home")

    @app.get("/translation")
    def translation_page() -> str:
        return render_template("translation.html", active_page="home")

    @app.get("/submit")
    @login_required
    def submit_page() -> str:
        return render_template("submit.html", active_page="submit")

    @app.get("/info")
    def info_page() -> str:
        return render_template("info.html", active_page="info")

    @app.get("/settings")
    @login_required
    def settings_page() -> str:
        return render_template("settings.html", active_page="settings")

    def _pipeline() -> TranslationPipeline:
        catalog = app.extensions["catalog"]
        catalog._reload()
        return TranslationPipeline(catalog=catalog)

    @app.get("/api/signs")
    def list_signs():  # type: ignore[override]
        catalog = app.extensions["catalog"]
        catalog._reload()
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
        catalog = app.extensions["catalog"]
        catalog._reload()
        submission_id = (request.args.get("submission") or "").strip() or None
        video_path = catalog.video_path(gloss, submission_id=submission_id)
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
        except TypeError as exc:
            return jsonify({"error": str(exc)}), 400

        if not sentences:
            return jsonify({"error": "No sentences provided."}), 400

        pipeline = _pipeline()
        results = pipeline.translate_many(sentences)
        catalog = app.extensions["catalog"]
        return jsonify({"sentences": sentences, "results": _format_results(results, catalog)})

    @app.post("/api/reports")
    @login_required
    def create_report():  # type: ignore[override]
        from .reports import create_report as save_report

        payload = request.get_json(silent=True) or {}
        report_type = str(payload.get("type", "")).strip().lower()
        original_sentence = str(payload.get("originalSentence", "")).strip()
        message = str(payload.get("message", "")).strip()
        gloss_tokens = payload.get("glossTokens")
        gloss_token = str(payload.get("glossToken", "")).strip() or None
        submission_id = str(payload.get("submissionId", "")).strip() or None

        if not isinstance(gloss_tokens, list):
            gloss_tokens = []

        try:
            record = save_report(
                report_type=report_type,
                original_sentence=original_sentence,
                message=message,
                gloss_tokens=[str(token) for token in gloss_tokens],
                gloss_token=gloss_token,
                submission_id=submission_id,
                reporter_id=current_user.id,
                reporter_username=current_user.username,
            )
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        return jsonify(
            {
                "success": True,
                "message": "Thank you — your report was submitted.",
                "id": record.id,
            }
        )

    @app.post("/api/submissions")
    @login_required
    def submit_translation():  # type: ignore[override]
        english = (request.form.get("english") or "").strip()
        notes = (request.form.get("notes") or "").strip()
        gloss = (request.form.get("gloss") or "").strip() or None

        if not english:
            return jsonify({"error": "English word or phrase is required."}), 400

        try:
            record = create_submission(
                english=english,
                gloss=gloss,
                notes=notes,
                video_file=request.files.get("video"),
                user_id=current_user.id,
                username=current_user.username,
            )
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        return jsonify(
            {
                "success": True,
                "message": "Thank you! Your submission is pending admin review.",
                "id": record.id,
                "status": record.status,
            }
        )

    return app


app = create_app()
