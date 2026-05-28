"""Admin routes for reviewing sign submissions."""

from __future__ import annotations

from functools import wraps

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import current_user, login_required

from .submissions import get_submission, list_submissions, update_submission_status

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)

    return wrapped


@admin_bp.get("/submissions/<submission_id>/video")
@admin_required
def preview_video(submission_id: str):
    record = get_submission(submission_id)
    if record is None or not record.video:
        abort(404)
    path = record.folder / record.video
    if not path.is_file():
        abort(404)
    return send_file(path, conditional=True)


@admin_bp.get("/")
@admin_required
def admin_dashboard():
    pending = list_submissions(status="pending")
    recent = list_submissions(status="approved")[:10]
    rejected = list_submissions(status="rejected")[:10]
    return render_template(
        "admin/review.html",
        active_page="admin",
        pending=pending,
        recent=recent,
        rejected=rejected,
    )


@admin_bp.post("/submissions/<submission_id>/approve")
@admin_required
def approve_submission(submission_id: str):
    record = get_submission(submission_id)
    if record is None:
        return jsonify({"error": "Submission not found."}), 404
    if record.status != "pending":
        return jsonify({"error": "Submission is not pending review."}), 400
    if not record.video:
        return jsonify({"error": "Submission has no video file."}), 400

    update_submission_status(
        submission_id,
        status="approved",
        reviewer_id=current_user.id,
    )

    catalog = current_app.extensions["catalog"]
    catalog.register(
        english=record.english,
        gloss=record.gloss,
        submission_id=record.id,
        video=record.video,
    )
    catalog._reload()

    if request.accept_mimetypes.best == "application/json":
        return jsonify({"success": True, "message": "Submission approved."})
    flash(f"Approved sign for “{record.gloss}”.", "success")
    return redirect(url_for("admin.admin_dashboard"))


@admin_bp.post("/submissions/<submission_id>/reject")
@admin_required
def reject_submission(submission_id: str):
    record = get_submission(submission_id)
    if record is None:
        return jsonify({"error": "Submission not found."}), 404
    if record.status != "pending":
        return jsonify({"error": "Submission is not pending review."}), 400

    payload = request.get_json(silent=True) or {}
    note = str(payload.get("reviewNote", "") or request.form.get("review_note", ""))

    update_submission_status(
        submission_id,
        status="rejected",
        reviewer_id=current_user.id,
        review_note=note,
    )

    if request.accept_mimetypes.best == "application/json":
        return jsonify({"success": True, "message": "Submission rejected."})
    flash(f"Rejected sign for “{record.gloss}”.", "success")
    return redirect(url_for("admin.admin_dashboard"))
