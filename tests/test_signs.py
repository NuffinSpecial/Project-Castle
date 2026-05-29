import json

from asl_translator.signs import CommunitySignCatalog


def test_catalog_registers_and_resolves_video(tmp_path):
    submissions = tmp_path / "submissions"
    folder = submissions / "abc123"
    folder.mkdir(parents=True)
    (folder / "sign.webm").write_bytes(b"fake-video")
    (folder / "metadata.json").write_text(
        json.dumps(
            {
                "id": "abc123",
                "english": "hello",
                "gloss": "ZZZTEST",
                "video": "sign.webm",
                "status": "approved",
            }
        ),
        encoding="utf-8",
    )

    catalog = CommunitySignCatalog(tmp_path)
    assert catalog.lookup("ZZZTEST") is not None
    assert catalog.video_path("ZZZTEST") == folder / "sign.webm"
    entry = catalog.lookup("ZZZTEST")
    assert entry is not None
    assert entry.video_api_path.startswith("/api/signs/ZZZTEST/video?submission=")


def test_catalog_keeps_multiple_approved_signs_for_same_gloss(tmp_path):
    submissions = tmp_path / "submissions"
    for submission_id, notes in (("one", "first meaning"), ("two", "second meaning")):
        folder = submissions / submission_id
        folder.mkdir(parents=True)
        (folder / "sign.webm").write_bytes(b"fake-video")
        (folder / "metadata.json").write_text(
            json.dumps(
                {
                    "id": submission_id,
                    "english": "bank",
                    "gloss": "BANK",
                    "notes": notes,
                    "video": "sign.webm",
                    "status": "approved",
                }
            ),
            encoding="utf-8",
        )

    catalog = CommunitySignCatalog(tmp_path)
    variants = catalog.lookup_all("BANK")
    assert len(variants) == 2
    assert {entry.notes for entry in variants} == {"first meaning", "second meaning"}


def test_pending_submission_not_in_catalog(tmp_path):
    submissions = tmp_path / "submissions"
    folder = submissions / "pending1"
    folder.mkdir(parents=True)
    (folder / "sign.webm").write_bytes(b"fake-video")
    (folder / "metadata.json").write_text(
        json.dumps(
            {
                "id": "pending1",
                "english": "pending",
                "gloss": "PENDING",
                "video": "sign.webm",
                "status": "pending",
            }
        ),
        encoding="utf-8",
    )

    catalog = CommunitySignCatalog(tmp_path)
    assert catalog.lookup("PENDING") is None
