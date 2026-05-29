"""Admin routes for reviewing and managing sign submissions."""

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

from .submissions import (
    SubmissionRecord,
    delete_submission,
    get_submission,
    list_submissions,
    replace_submission_video,
    update_submission_metadata,
    update_submission_status,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

_VALID_VIEWS = frozenset({"pending", "all", "approved", "rejected"})


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def _sync_catalog(record: SubmissionRecord | None) -> None:
    catalog = current_app.extensions["catalog"]
    if record is None:
        catalog._reload()
        return
    catalog.remove_by_submission_id(record.id)
    if record.status == "approved" and record.video:
        catalog.register(
            english=record.english,
            gloss=record.gloss,
            submission_id=record.id,
            video=record.video,
        )
    catalog._reload()


def _wants_json() -> bool:
    return request.accept_mimetypes.best == "application/json"


def _redirect_after_review() -> str:
    if request.form.get("_from") == "signs":
        return "admin.admin_signs"
    return "admin.admin_dashboard"


def _respond_json_or_redirect(
    *,
    success_message: str,
    redirect_endpoint: str,
    status: int = 200,
    error: str | None = None,
):
    if error:
        if _wants_json():
            return jsonify({"error": error}), status
        flash(error, "error")
        return redirect(url_for(redirect_endpoint))

    if _wants_json():
        return jsonify({"success": True, "message": success_message}), status
    flash(success_message, "success")
    return redirect(url_for(redirect_endpoint))


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


def _submission_counts() -> dict[str, int]:
    return {
        "all": len(list_submissions()),
        "pending": len(list_submissions(status="pending")),
        "approved": len(list_submissions(status="approved")),
        "rejected": len(list_submissions(status="rejected")),
    }


@admin_bp.get("/")
@admin_required
def admin_dashboard():
    pending = list_submissions(status="pending")
    return render_template(
        "admin/review.html",
        active_page="admin",
        admin_section="review",
        admin_view="pending",
        pending=pending,
        counts=_submission_counts(),
    )


@admin_bp.get("/signs")
@admin_required
def admin_signs():
    view = request.args.get("status", "all")
    if view not in _VALID_VIEWS:
        view = "all"

    if view == "all":
        submissions = list_submissions()
    else:
        submissions = list_submissions(status=view)  # type: ignore[arg-type]

    counts = _submission_counts()

    return render_template(
        "admin/signs.html",
        active_page="admin",
        admin_section="signs",
        admin_view=view,
        submissions=submissions,
        counts=counts,
    )


@admin_bp.post("/submissions/<submission_id>/approve")
@admin_required
def approve_submission(submission_id: str):
    record = get_submission(submission_id)
    if record is None:
        return _respond_json_or_redirect(
            error="Submission not found.",
            redirect_endpoint="admin.admin_dashboard",
            status=404,
        )
    if record.status == "approved":
        return _respond_json_or_redirect(
            error="Submission is already approved.",
            redirect_endpoint="admin.admin_dashboard",
            status=400,
        )
    if record.status not in ("pending", "rejected"):
        return _respond_json_or_redirect(
            error="Submission cannot be approved from its current status.",
            redirect_endpoint="admin.admin_dashboard",
            status=400,
        )
    if not record.video:
        return _respond_json_or_redirect(
            error="Submission has no video file.",
            redirect_endpoint="admin.admin_dashboard",
            status=400,
        )

    record = update_submission_status(
        submission_id,
        status="approved",
        reviewer_id=current_user.id,
    )
    assert record is not None
    _sync_catalog(record)

    redirect_to = _redirect_after_review()
    return _respond_json_or_redirect(
        success_message=f"Approved sign for “{record.gloss}”.",
        redirect_endpoint=redirect_to,
    )


@admin_bp.post("/submissions/<submission_id>/reject")
@admin_required
def reject_submission(submission_id: str):
    record = get_submission(submission_id)
    if record is None:
        return _respond_json_or_redirect(
            error="Submission not found.",
            redirect_endpoint="admin.admin_dashboard",
            status=404,
        )
    if record.status != "pending":
        return _respond_json_or_redirect(
            error="Submission is not pending review.",
            redirect_endpoint="admin.admin_dashboard",
            status=400,
        )

    payload = request.get_json(silent=True) or {}
    note = str(payload.get("reviewNote", "") or request.form.get("review_note", ""))

    record = update_submission_status(
        submission_id,
        status="rejected",
        reviewer_id=current_user.id,
        review_note=note,
    )
    assert record is not None
    _sync_catalog(record)

    redirect_to = _redirect_after_review()
    return _respond_json_or_redirect(
        success_message=f"Rejected sign for “{record.gloss}”.",
        redirect_endpoint=redirect_to,
    )


@admin_bp.post("/submissions/<submission_id>/revoke")
@admin_required
def revoke_submission(submission_id: str):
    """Remove an approved sign from the public catalog (set back to pending)."""
    record = get_submission(submission_id)
    if record is None:
        return _respond_json_or_redirect(
            error="Submission not found.",
            redirect_endpoint="admin.admin_signs",
            status=404,
        )
    if record.status != "approved":
        return _respond_json_or_redirect(
            error="Only approved submissions can be revoked.",
            redirect_endpoint="admin.admin_signs",
            status=400,
        )

    record = update_submission_status(
        submission_id,
        status="pending",
        reviewer_id=current_user.id,
        review_note="Approval revoked by admin.",
    )
    assert record is not None
    _sync_catalog(record)

    return _respond_json_or_redirect(
        success_message=f"Revoked approval for “{record.gloss}”; it is pending again.",
        redirect_endpoint="admin.admin_signs",
    )


@admin_bp.post("/submissions/<submission_id>/update")
@admin_required
def update_submission(submission_id: str):
    record = get_submission(submission_id)
    if record is None:
        return _respond_json_or_redirect(
            error="Submission not found.",
            redirect_endpoint="admin.admin_signs",
            status=404,
        )

    english = request.form.get("english", record.english)
    gloss = request.form.get("gloss", record.gloss)
    notes = request.form.get("notes", record.notes)

    if not english.strip():
        return _respond_json_or_redirect(
            error="English phrase is required.",
            redirect_endpoint="admin.admin_signs",
            status=400,
        )

    record = update_submission_metadata(
        submission_id,
        english=english,
        gloss=gloss,
        notes=notes,
    )
    assert record is not None
    _sync_catalog(record)

    return _respond_json_or_redirect(
        success_message=f"Updated “{record.gloss}”.",
        redirect_endpoint="admin.admin_signs",
    )


@admin_bp.post("/submissions/<submission_id>/replace-video")
@admin_required
def replace_video(submission_id: str):
    record = get_submission(submission_id)
    if record is None:
        return _respond_json_or_redirect(
            error="Submission not found.",
            redirect_endpoint="admin.admin_signs",
            status=404,
        )

    video_file = request.files.get("video")
    try:
        record = replace_submission_video(submission_id, video_file)
    except ValueError as exc:
        return _respond_json_or_redirect(
            error=str(exc),
            redirect_endpoint="admin.admin_signs",
            status=400,
        )

    if record is None:
        return _respond_json_or_redirect(
            error="Submission not found.",
            redirect_endpoint="admin.admin_signs",
            status=404,
        )

    _sync_catalog(record)

    return _respond_json_or_redirect(
        success_message=f"Replaced video for “{record.gloss}”.",
        redirect_endpoint="admin.admin_signs",
    )


@admin_bp.post("/submissions/<submission_id>/delete")
@admin_required
def delete_submission_route(submission_id: str):
    record = get_submission(submission_id)
    if record is None:
        return _respond_json_or_redirect(
            error="Submission not found.",
            redirect_endpoint="admin.admin_signs",
            status=404,
        )

    gloss = record.gloss
    current_app.extensions["catalog"].remove_by_submission_id(submission_id)
    delete_submission(submission_id)
    _sync_catalog(None)

    return _respond_json_or_redirect(
        success_message=f"Deleted submission “{gloss}”.",
        redirect_endpoint="admin.admin_signs",
    )
