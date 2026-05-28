"""Crowdsourced community sign catalog and URL resolution."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


def project_data_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "data"


@dataclass(frozen=True)
class SignEntry:
    """A community-contributed sign video mapped to gloss and English forms."""

    gloss: str
    english: str
    submission_id: str
    video: str

    @property
    def video_api_path(self) -> str:
        return f"/api/signs/{self.gloss}/video"


class CommunitySignCatalog:
    """Load and register crowdsourced signs from disk."""

    def __init__(self, data_dir: Path | None = None) -> None:
        root = data_dir or project_data_dir()
        self._catalog_path = root / "signs" / "catalog.json"
        self._submission_dirs = [root / "submissions"]
        self._by_gloss: dict[str, SignEntry] = {}
        self._reload()

    def _reload(self) -> None:
        self._by_gloss.clear()
        if self._catalog_path.exists():
            payload = json.loads(self._catalog_path.read_text(encoding="utf-8"))
            for raw in payload.get("entries", []):
                self._register_entry(raw, persist=False)
        for folder in self._submission_dirs:
            self._scan_submissions(folder, persist=False)
        self._save_catalog()

    def _scan_submissions(self, submissions_dir: Path, *, persist: bool) -> None:
        if not submissions_dir.exists():
            return
        for folder in submissions_dir.iterdir():
            if not folder.is_dir():
                continue
            meta_path = folder / "metadata.json"
            if not meta_path.exists():
                continue
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if not meta.get("video"):
                continue
            status = meta.get("status") or "pending"
            if status != "approved":
                continue
            self._register_entry(
                {
                    "gloss": meta.get("gloss") or meta.get("english", ""),
                    "english": meta.get("english", ""),
                    "submissionId": meta.get("id", folder.name),
                    "video": meta["video"],
                },
                persist=persist,
            )

    def _normalize_gloss(self, value: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9+\-]", "", value.upper())
        return cleaned or value.upper()

    def _register_entry(self, raw: dict, *, persist: bool) -> SignEntry | None:
        english = str(raw.get("english", "")).strip()
        gloss_raw = str(raw.get("gloss") or english).strip()
        if not english and not gloss_raw:
            return None
        gloss = self._normalize_gloss(gloss_raw)
        submission_id = str(raw.get("submissionId", "")).strip()
        video = str(raw.get("video", "")).strip()
        if not submission_id or not video:
            return None
        entry = SignEntry(
            gloss=gloss,
            english=english.lower(),
            submission_id=submission_id,
            video=video,
        )
        self._by_gloss[gloss] = entry
        if english:
            self._by_gloss[self._normalize_gloss(english)] = entry
        if persist:
            self._save_catalog()
        return entry

    def _save_catalog(self) -> None:
        self._catalog_path.parent.mkdir(parents=True, exist_ok=True)
        seen: set[str] = set()
        entries: list[dict] = []
        for entry in self._by_gloss.values():
            if entry.submission_id in seen:
                continue
            seen.add(entry.submission_id)
            entries.append(
                {
                    "gloss": entry.gloss,
                    "english": entry.english,
                    "submissionId": entry.submission_id,
                    "video": entry.video,
                }
            )
        self._catalog_path.write_text(
            json.dumps({"entries": entries}, indent=2) + "\n",
            encoding="utf-8",
        )

    def register(
        self,
        *,
        english: str,
        submission_id: str,
        video: str,
        gloss: str | None = None,
    ) -> SignEntry:
        """Add or update a sign from a new community submission."""

        entry = self._register_entry(
            {
                "english": english,
                "gloss": gloss or english,
                "submissionId": submission_id,
                "video": video,
            },
            persist=True,
        )
        assert entry is not None
        return entry

    def lookup(self, gloss_token: str) -> SignEntry | None:
        key = self._normalize_gloss(gloss_token)
        return self._by_gloss.get(key)

    def video_path(self, gloss_token: str) -> Path | None:
        entry = self.lookup(gloss_token)
        if entry is None:
            return None
        for root in self._submission_dirs:
            path = root / entry.submission_id / entry.video
            if path.is_file():
                return path
        return None

    def list_entries(self) -> list[SignEntry]:
        seen: set[str] = set()
        result: list[SignEntry] = []
        for entry in self._by_gloss.values():
            if entry.submission_id in seen:
                continue
            seen.add(entry.submission_id)
            result.append(entry)
        return sorted(result, key=lambda item: item.gloss)


class CommunitySignLinker:
    """Resolve gloss tokens to community sign video API paths."""

    def __init__(self, catalog: CommunitySignCatalog | None = None) -> None:
        self.catalog = catalog or CommunitySignCatalog()

    def links_for(self, gloss_tokens: Iterable[str]) -> list[str | None]:
        return [self.link_for_token(token) for token in gloss_tokens]

    def availability_for(self, gloss_tokens: Iterable[str]) -> list[bool]:
        return [self.link_for_token(token) is not None for token in gloss_tokens]

    def link_for_token(self, gloss_token: str) -> str | None:
        entry = self.catalog.lookup(gloss_token)
        if entry is None:
            return None
        if self.catalog.video_path(gloss_token) is None:
            return None
        return entry.video_api_path
