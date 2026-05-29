import json
import os


def test_translate_returns_sign_variants_with_context(tmp_path):
    data = tmp_path / "data"
    submissions = data / "submissions"
    submissions.mkdir(parents=True)
    (data / "signs").mkdir()

    for submission_id, notes in (("aaa", "financial institution"), ("bbb", "river edge")):
        folder = submissions / submission_id
        folder.mkdir()
        (folder / "sign.webm").write_bytes(b"video")
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

    os.environ["CASTLE_DATA_DIR"] = str(data)
    os.environ["CASTLE_DATABASE"] = str(data / "castle.db")
    os.environ["FLASK_SECRET_KEY"] = "test-secret"

    from web_app import create_app

    application = create_app()
    application.config["TESTING"] = True
    client = application.test_client()

    response = client.post("/translate", json={"sentences": ["I went to the bank"]})
    payload = response.get_json()
    assert response.status_code == 200

    bank_index = payload["results"][0]["glossTokens"].index("BANK")
    variants = payload["results"][0]["signVariants"][bank_index]
    assert len(variants) == 2
    contexts = {variant["context"] for variant in variants}
    assert contexts == {"financial institution", "river edge"}


def test_sign_video_endpoint_supports_submission_query(tmp_path):
    data = tmp_path / "data"
    submissions = data / "submissions"
    folder = submissions / "only"
    folder.mkdir(parents=True)
    (data / "signs").mkdir()
    (folder / "sign.webm").write_bytes(b"video-bytes")
    (folder / "metadata.json").write_text(
        json.dumps(
            {
                "id": "only",
                "english": "wave",
                "gloss": "WAVE",
                "notes": "greeting",
                "video": "sign.webm",
                "status": "approved",
            }
        ),
        encoding="utf-8",
    )

    os.environ["CASTLE_DATA_DIR"] = str(data)
    os.environ["CASTLE_DATABASE"] = str(data / "castle.db")
    os.environ["FLASK_SECRET_KEY"] = "test-secret"

    from web_app import create_app

    application = create_app()
    application.config["TESTING"] = True
    client = application.test_client()

    response = client.get("/api/signs/WAVE/video?submission=only")
    assert response.status_code == 200
    assert response.data == b"video-bytes"


def test_second_variant_video_served(tmp_path):
    data = tmp_path / "data"
    submissions = data / "submissions"
    submissions.mkdir(parents=True)
    (data / "signs").mkdir()

    for submission_id, body in (("first", b"one"), ("second", b"two")):
        folder = submissions / submission_id
        folder.mkdir()
        (folder / "sign.webm").write_bytes(body)
        (folder / "metadata.json").write_text(
            json.dumps(
                {
                    "id": submission_id,
                    "english": "run",
                    "gloss": "RUN",
                    "notes": submission_id,
                    "video": "sign.webm",
                    "status": "approved",
                }
            ),
            encoding="utf-8",
        )

    os.environ["CASTLE_DATA_DIR"] = str(data)
    os.environ["CASTLE_DATABASE"] = str(data / "castle.db")
    os.environ["FLASK_SECRET_KEY"] = "test-secret"

    from web_app import create_app

    application = create_app()
    application.config["TESTING"] = True
    client = application.test_client()

    assert client.get("/api/signs/RUN/video?submission=second").data == b"two"
