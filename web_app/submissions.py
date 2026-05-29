"""Crowdsourced sign submission storage and review workflow."""

from __future__ import annotations

import json
import shutil
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from .config import data_dir

SubmissionStatus = Literal["pending", "approved", "rejected"]

_MAX_UPLOAD_BYTES = 25 * 1024 * 1024
_ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov"}


@dataclass
class SubmissionRecord:
    id: str
    english: str
    gloss: str
    notes: str
    video: str | None
    status: SubmissionStatus
    submitted_at: str
    submitted_by: int | None
    submitted_by_username: str | None
    reviewed_at: str | None
    reviewed_by: int | None
    review_note: str | None

    @property
    def folder(self) -> Path:
        return submissions_root() / self.id

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "english": self.english,
            "gloss": self.gloss,
            "notes": self.notes,
            "video": self.video,
            "status": self.status,
            "submittedAt": self.submitted_at,
            "submittedBy": self.submitted_by,
            "submittedByUsername": self.submitted_by_username,
            "reviewedAt": self.reviewed_at,
            "reviewedBy": self.reviewed_by,
            "reviewNote": self.review_note,
        }


def submissions_root() -> Path:
    root = data_dir() / "submissions"
    root.mkdir(parents=True, exist_ok=True)
    return root


def allowed_video(filename: str) -> bool:
    return Path(filename).suffix.lower() in _ALLOWED_VIDEO_EXTENSIONS


def _read_metadata(folder: Path) -> dict | None:
    meta_path = folder / "metadata.json"
    if not meta_path.exists():
        return None
    return json.loads(meta_path.read_text(encoding="utf-8"))


def _write_metadata(folder: Path, metadata: dict) -> None:
    (folder / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def _record_from_meta(meta: dict) -> SubmissionRecord:
    status = meta.get("status", "approved")
    if status not in ("pending", "approved", "rejected"):
        status = "pending"
    return SubmissionRecord(
        id=meta["id"],
        english=meta.get("english", ""),
        gloss=meta.get("gloss") or meta.get("english", ""),
        notes=meta.get("notes", ""),
        video=meta.get("video"),
        status=status,
        submitted_at=meta.get("submittedAt", ""),
        submitted_by=meta.get("submittedBy"),
        submitted_by_username=meta.get("submittedByUsername"),
        reviewed_at=meta.get("reviewedAt"),
        reviewed_by=meta.get("reviewedBy"),
        review_note=meta.get("reviewNote"),
    )


def create_submission(
    *,
    english: str,
    gloss: str | None,
    notes: str,
    video_file,
    user_id: int | None,
    username: str | None,
) -> SubmissionRecord:
    submission_id = uuid.uuid4().hex
    folder = submissions_root() / submission_id
    folder.mkdir(parents=True, exist_ok=True)

    saved_video: str | None = None
    if video_file:
        from werkzeug.utils import secure_filename

        original_name = video_file.filename or "upload.webm"
        if not allowed_video(original_name):
            raise ValueError("Unsupported video format. Use MP4, WebM, or MOV.")

        video_file.seek(0, 2)
        size = video_file.tell()
        video_file.seek(0)
        if size > _MAX_UPLOAD_BYTES:
            raise ValueError("Video file exceeds 25 MB limit.")

        saved_video = secure_filename(original_name) or "upload.webm"
        video_file.save(folder / saved_video)

    metadata = {
        "id": submission_id,
        "english": english,
        "gloss": gloss or english,
        "notes": notes,
        "video": saved_video,
        "status": "pending",
        "submittedAt": datetime.now(UTC).isoformat(),
        "submittedBy": user_id,
        "submittedByUsername": username,
        "reviewedAt": None,
        "reviewedBy": None,
        "reviewNote": None,
    }
    _write_metadata(folder, metadata)
    return _record_from_meta(metadata)


def list_submissions(*, status: SubmissionStatus | None = None) -> list[SubmissionRecord]:
    records: list[SubmissionRecord] = []
    root = submissions_root()
    if not root.exists():
        return records

    for folder in root.iterdir():
        if not folder.is_dir():
            continue
        meta = _read_metadata(folder)
        if meta is None:
            continue
        record = _record_from_meta(meta)
        if status is None or record.status == status:
            records.append(record)

    records.sort(key=lambda item: item.submitted_at, reverse=True)
    return records


def get_submission(submission_id: str) -> SubmissionRecord | None:
    folder = submissions_root() / submission_id
    meta = _read_metadata(folder)
    if meta is None:
        return None
    return _record_from_meta(meta)


def update_submission_status(
    submission_id: str,
    *,
    status: SubmissionStatus,
    reviewer_id: int,
    review_note: str = "",
) -> SubmissionRecord | None:
    folder = submissions_root() / submission_id
    meta = _read_metadata(folder)
    if meta is None:
        return None

    meta["status"] = status
    meta["reviewedAt"] = datetime.now(UTC).isoformat()
    meta["reviewedBy"] = reviewer_id
    meta["reviewNote"] = review_note.strip()
    _write_metadata(folder, meta)
    return _record_from_meta(meta)


def update_submission_metadata(
    submission_id: str,
    *,
    english: str | None = None,
    gloss: str | None = None,
    notes: str | None = None,
) -> SubmissionRecord | None:
    folder = submissions_root() / submission_id
    meta = _read_metadata(folder)
    if meta is None:
        return None

    if english is not None:
        meta["english"] = english.strip()
    if gloss is not None:
        cleaned = gloss.strip()
        meta["gloss"] = cleaned or meta.get("english", "")
    if notes is not None:
        meta["notes"] = notes.strip()

    _write_metadata(folder, meta)
    return _record_from_meta(meta)


def _save_video_file(folder: Path, video_file) -> str:
    from werkzeug.utils import secure_filename

    original_name = video_file.filename or "upload.webm"
    if not allowed_video(original_name):
        raise ValueError("Unsupported video format. Use MP4, WebM, or MOV.")

    video_file.seek(0, 2)
    size = video_file.tell()
    video_file.seek(0)
    if size > _MAX_UPLOAD_BYTES:
        raise ValueError("Video file exceeds 25 MB limit.")

    for path in folder.iterdir():
        if path.is_file() and path.name != "metadata.json":
            path.unlink()

    saved_video = secure_filename(original_name) or "upload.webm"
    video_file.save(folder / saved_video)
    return saved_video


def replace_submission_video(submission_id: str, video_file) -> SubmissionRecord | None:
    folder = submissions_root() / submission_id
    meta = _read_metadata(folder)
    if meta is None:
        return None
    if not video_file or not getattr(video_file, "filename", None):
        raise ValueError("A video file is required.")

    saved_video = _save_video_file(folder, video_file)
    meta["video"] = saved_video
    _write_metadata(folder, meta)
    return _record_from_meta(meta)


def delete_submission(submission_id: str) -> bool:
    folder = submissions_root() / submission_id
    if not folder.is_dir():
        return False
    shutil.rmtree(folder)
    return True
