"""Crowdsourced community sign catalog and URL resolution."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote


def project_data_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "data"


@dataclass(frozen=True)
class SignEntry:
    """A community-contributed sign video mapped to gloss and English forms."""

    gloss: str
    english: str
    submission_id: str
    video: str
    notes: str = ""

    @property
    def video_api_path(self) -> str:
        submission = quote(self.submission_id, safe="")
        return f"/api/signs/{self.gloss}/video?submission={submission}"


class CommunitySignCatalog:
    """Load and register crowdsourced signs from disk."""

    def __init__(self, data_dir: Path | None = None) -> None:
        root = data_dir or project_data_dir()
        self._catalog_path = root / "signs" / "catalog.json"
        self._submission_dirs = [root / "submissions"]
        self._by_gloss: dict[str, list[SignEntry]] = {}
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
                    "notes": meta.get("notes", ""),
                    "submissionId": meta.get("id", folder.name),
                    "video": meta["video"],
                },
                persist=persist,
            )

    def _normalize_gloss(self, value: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9+\-]", "", value.upper())
        return cleaned or value.upper()

    def _append_entry(self, key: str, entry: SignEntry) -> None:
        bucket = self._by_gloss.setdefault(key, [])
        for index, existing in enumerate(bucket):
            if existing.submission_id == entry.submission_id:
                bucket[index] = entry
                return
        bucket.append(entry)

    def _register_entry(self, raw: dict, *, persist: bool) -> SignEntry | None:
        english = str(raw.get("english", "")).strip()
        gloss_raw = str(raw.get("gloss") or english).strip()
        if not english and not gloss_raw:
            return None
        gloss = self._normalize_gloss(gloss_raw)
        submission_id = str(raw.get("submissionId", "")).strip()
        video = str(raw.get("video", "")).strip()
        notes = str(raw.get("notes", "")).strip()
        if not submission_id or not video:
            return None
        entry = SignEntry(
            gloss=gloss,
            english=english.lower(),
            submission_id=submission_id,
            video=video,
            notes=notes,
        )
        self._append_entry(gloss, entry)
        if english:
            english_key = self._normalize_gloss(english)
            if english_key != gloss:
                self._append_entry(english_key, entry)
        if persist:
            self._save_catalog()
        return entry

    def _save_catalog(self) -> None:
        self._catalog_path.parent.mkdir(parents=True, exist_ok=True)
        seen: set[str] = set()
        entries: list[dict] = []
        for bucket in self._by_gloss.values():
            for entry in bucket:
                if entry.submission_id in seen:
                    continue
                seen.add(entry.submission_id)
                payload = {
                    "gloss": entry.gloss,
                    "english": entry.english,
                    "submissionId": entry.submission_id,
                    "video": entry.video,
                }
                if entry.notes:
                    payload["notes"] = entry.notes
                entries.append(payload)
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
        notes: str = "",
    ) -> SignEntry:
        """Add or update a sign from a new community submission."""

        entry = self._register_entry(
            {
                "english": english,
                "gloss": gloss or english,
                "submissionId": submission_id,
                "video": video,
                "notes": notes,
            },
            persist=True,
        )
        assert entry is not None
        return entry

    def lookup(self, gloss_token: str) -> SignEntry | None:
        entries = self.lookup_all(gloss_token)
        return entries[0] if entries else None

    def lookup_all(self, gloss_token: str) -> list[SignEntry]:
        key = self._normalize_gloss(gloss_token)
        return list(self._by_gloss.get(key, []))

    def video_path_for_entry(self, entry: SignEntry) -> Path | None:
        for root in self._submission_dirs:
            path = root / entry.submission_id / entry.video
            if path.is_file():
                return path
        return None

    def video_path(self, gloss_token: str, *, submission_id: str | None = None) -> Path | None:
        if submission_id:
            for bucket in self._by_gloss.values():
                for entry in bucket:
                    if entry.submission_id == submission_id:
                        return self.video_path_for_entry(entry)
            return None

        entry = self.lookup(gloss_token)
        if entry is None:
            return None
        return self.video_path_for_entry(entry)

    def list_entries(self) -> list[SignEntry]:
        seen: set[str] = set()
        result: list[SignEntry] = []
        for bucket in self._by_gloss.values():
            for entry in bucket:
                if entry.submission_id in seen:
                    continue
                seen.add(entry.submission_id)
                result.append(entry)
        return sorted(result, key=lambda item: item.gloss)

    def remove_by_submission_id(self, submission_id: str) -> bool:
        """Remove all catalog entries for a submission."""
        removed = False
        for key, bucket in list(self._by_gloss.items()):
            filtered = [entry for entry in bucket if entry.submission_id != submission_id]
            if len(filtered) != len(bucket):
                removed = True
                if filtered:
                    self._by_gloss[key] = filtered
                else:
                    del self._by_gloss[key]
        if removed:
            self._save_catalog()
        return removed

    def entry_for_submission(self, submission_id: str) -> SignEntry | None:
        for bucket in self._by_gloss.values():
            for entry in bucket:
                if entry.submission_id == submission_id:
                    return entry
        return None


class CommunitySignLinker:
    """Resolve gloss tokens to community sign video API paths."""

    def __init__(self, catalog: CommunitySignCatalog | None = None) -> None:
        self.catalog = catalog or CommunitySignCatalog()

    def links_for(self, gloss_tokens: Iterable[str]) -> list[str | None]:
        return [self.link_for_token(token) for token in gloss_tokens]

    def availability_for(self, gloss_tokens: Iterable[str]) -> list[bool]:
        return [bool(self.variants_for_token(token)) for token in gloss_tokens]

    def variants_for_token(self, gloss_token: str) -> list[SignEntry]:
        entries = self.catalog.lookup_all(gloss_token)
        return [entry for entry in entries if self.catalog.video_path_for_entry(entry) is not None]

    def link_for_token(self, gloss_token: str) -> str | None:
        variants = self.variants_for_token(gloss_token)
        if not variants:
            return None
        return variants[0].video_api_path
