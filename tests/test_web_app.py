from io import BytesIO

from web_app import create_app


def test_home_page_renders():
    app = create_app()
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"Project Castle" in response.data
    assert b"Translate" in response.data


def test_translation_page_renders():
    app = create_app()
    client = app.test_client()

    response = client.get("/translation")

    assert response.status_code == 200
    assert b"ASL Gloss" in response.data
    assert b"Back to Home" in response.data


def test_submit_page_renders():
    app = create_app()
    client = app.test_client()

    response = client.get("/submit")

    assert response.status_code == 200
    assert b"Submit a Translation" in response.data


def test_info_page_renders():
    app = create_app()
    client = app.test_client()

    response = client.get("/info")

    assert response.status_code == 200
    assert b"About the Project" in response.data


def test_settings_page_renders():
    app = create_app()
    client = app.test_client()

    response = client.get("/settings")

    assert response.status_code == 200
    assert b"Display" in response.data


def test_translate_endpoint_returns_gloss():
    app = create_app()
    client = app.test_client()

    response = client.post("/translate", json={"sentences": ["I will eat an apple tomorrow"]})
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["sentences"] == ["I will eat an apple tomorrow"]
    assert payload["results"][0]["glossTokens"][0] == "FUTURE"
    assert "signAvailable" in payload["results"][0]
    assert "lemmas" in payload["results"][0]
    assert "analysisEngine" in payload["results"][0]


def test_sign_video_endpoint_404_when_missing():
    app = create_app()
    client = app.test_client()

    response = client.get("/api/signs/NOTASIGN/video")

    assert response.status_code == 404


def test_submission_endpoint_accepts_form():
    app = create_app()
    client = app.test_client()

    response = client.post(
        "/api/submissions",
        data={
            "english": "hello",
            "notes": "test note",
            "video": (BytesIO(b"fake"), "sign.webm"),
        },
        content_type="multipart/form-data",
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["success"] is True
    assert "catalog" in payload["message"].lower()
    assert payload.get("videoUrl")


def test_submission_rejects_missing_english():
    app = create_app()
    client = app.test_client()

    response = client.post("/api/submissions", data={"english": "  "})

    assert response.status_code == 400
    assert response.get_json()["error"]
