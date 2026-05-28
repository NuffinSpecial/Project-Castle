"""Flask-Login user model."""

from __future__ import annotations

from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, row) -> None:
        self.id = int(row["id"])
        self.email = row["email"]
        self.username = row["username"]
        self.is_admin = bool(row["is_admin"])
        self.created_at = row["created_at"]

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_active(self) -> bool:
        return True
