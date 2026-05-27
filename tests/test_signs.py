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
            }
        ),
        encoding="utf-8",
    )

    catalog = CommunitySignCatalog(tmp_path)
    assert catalog.lookup("ZZZTEST") is not None
    assert catalog.video_path("ZZZTEST") == folder / "sign.webm"
    assert catalog.lookup("ZZZTEST").video_api_path == "/api/signs/ZZZTEST/video"
