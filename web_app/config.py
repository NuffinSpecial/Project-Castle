"""Application configuration."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def data_dir() -> Path:
    override = os.environ.get("CASTLE_DATA_DIR")
    if override:
        return Path(override)
    return PROJECT_ROOT / "data"


def database_path() -> Path:
    override = os.environ.get("CASTLE_DATABASE")
    if override:
        return Path(override)
    return data_dir() / "castle.db"


def secret_key() -> str:
    return os.environ.get("FLASK_SECRET_KEY", "dev-only-change-in-production")
