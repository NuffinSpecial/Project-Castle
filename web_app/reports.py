"""User reports for incorrect glossing or sign videos."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from .db import get_db

ReportType = Literal["gloss", "video"]
ReportStatus = Literal["open", "resolved", "dismissed"]

_VALID_TYPES = frozenset({"gloss", "video"})
_VALID_STATUSES = frozenset({"open", "resolved", "dismissed"})


@dataclass
class ReportRecord:
    id: int
    report_type: ReportType
    original_sentence: str
    gloss_tokens: list[str]
    gloss_token: str | None
    submission_id: str | None
    message: str
    status: ReportStatus
    reporter_id: int | None
    reporter_username: str | None
    created_at: str
    reviewed_at: str | None
    reviewed_by: int | None
    admin_note: str | None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "reportType": self.report_type,
            "originalSentence": self.original_sentence,
            "glossTokens": self.gloss_tokens,
            "glossToken": self.gloss_token,
            "submissionId": self.submission_id,
            "message": self.message,
            "status": self.status,
            "reporterUsername": self.reporter_username,
            "createdAt": self.created_at,
            "reviewedAt": self.reviewed_at,
            "adminNote": self.admin_note,
        }


def _row_to_record(row) -> ReportRecord:
    gloss_raw = row["gloss_tokens"] or "[]"
    try:
        gloss_tokens = json.loads(gloss_raw)
        if not isinstance(gloss_tokens, list):
            gloss_tokens = []
    except json.JSONDecodeError:
        gloss_tokens = []

    status = row["status"]
    if status not in _VALID_STATUSES:
        status = "open"

    report_type = row["report_type"]
    if report_type not in _VALID_TYPES:
        report_type = "gloss"

    return ReportRecord(
        id=int(row["id"]),
        report_type=report_type,  # type: ignore[arg-type]
        original_sentence=row["original_sentence"],
        gloss_tokens=[str(token) for token in gloss_tokens],
        gloss_token=row["gloss_token"],
        submission_id=row["submission_id"],
        message=row["message"],
        status=status,  # type: ignore[arg-type]
        reporter_id=row["reporter_id"],
        reporter_username=row["reporter_username"],
        created_at=row["created_at"],
        reviewed_at=row["reviewed_at"],
        reviewed_by=row["reviewed_by"],
        admin_note=row["admin_note"],
    )


def create_report(
    *,
    report_type: str,
    original_sentence: str,
    message: str,
    gloss_tokens: list[str] | None = None,
    gloss_token: str | None = None,
    submission_id: str | None = None,
    reporter_id: int | None = None,
    reporter_username: str | None = None,
) -> ReportRecord:
    if report_type not in _VALID_TYPES:
        raise ValueError("Invalid report type.")
    original_sentence = original_sentence.strip()
    message = message.strip()
    if not original_sentence:
        raise ValueError("Original sentence is required.")
    if len(message) < 5:
        raise ValueError("Please describe the issue in at least 5 characters.")

    gloss_json = json.dumps(gloss_tokens or [])
    created_at = datetime.now(UTC).isoformat()

    with get_db() as connection:
        cursor = connection.execute(
            """
            INSERT INTO reports (
                report_type, original_sentence, gloss_tokens, gloss_token,
                submission_id, message, status, reporter_id, reporter_username, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 'open', ?, ?, ?)
            """,
            (
                report_type,
                original_sentence,
                gloss_json,
                (gloss_token or "").strip() or None,
                (submission_id or "").strip() or None,
                message,
                reporter_id,
                reporter_username,
                created_at,
            ),
        )
        report_id = int(cursor.lastrowid)
        row = connection.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()

    assert row is not None
    return _row_to_record(row)


def get_report(report_id: int) -> ReportRecord | None:
    with get_db() as connection:
        row = connection.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
    return _row_to_record(row) if row else None


def list_reports(*, status: ReportStatus | None = None) -> list[ReportRecord]:
    query = "SELECT * FROM reports"
    params: tuple = ()
    if status is not None:
        query += " WHERE status = ?"
        params = (status,)
    query += " ORDER BY created_at DESC"

    with get_db() as connection:
        rows = connection.execute(query, params).fetchall()
    return [_row_to_record(row) for row in rows]


def count_reports(*, status: ReportStatus | None = None) -> int:
    query = "SELECT COUNT(*) AS count FROM reports"
    params: tuple = ()
    if status is not None:
        query += " WHERE status = ?"
        params = (status,)

    with get_db() as connection:
        row = connection.execute(query, params).fetchone()
    return int(row["count"]) if row else 0


def update_report_status(
    report_id: int,
    *,
    status: ReportStatus,
    reviewer_id: int,
    admin_note: str = "",
) -> ReportRecord | None:
    if status not in _VALID_STATUSES:
        raise ValueError("Invalid status.")

    reviewed_at = datetime.now(UTC).isoformat()
    with get_db() as connection:
        connection.execute(
            """
            UPDATE reports
            SET status = ?, reviewed_at = ?, reviewed_by = ?, admin_note = ?
            WHERE id = ?
            """,
            (status, reviewed_at, reviewer_id, admin_note.strip(), report_id),
        )
        row = connection.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()

    return _row_to_record(row) if row else None
