from io import BytesIO

from tests.conftest import register_and_login


def test_home_page_renders(client):

    response = client.get("/")

    assert response.status_code == 200
    assert b"Project Castle" in response.data
    assert b"Translate" in response.data


def test_translation_page_renders(client):
    response = client.get("/translation")

    assert response.status_code == 200
    assert b"ASL Gloss" in response.data
    assert b"Back" in response.data
    assert b"ASL Gloss" in response.data


def test_submit_page_redirects_when_logged_out(client):
    response = client.get("/submit")
    assert response.status_code == 302


def test_submit_page_renders(client):
    register_and_login(client)
    response = client.get("/submit")

    assert response.status_code == 200
    assert b"Submit a Translation" in response.data


def test_info_page_renders(client):
    response = client.get("/info")

    assert response.status_code == 200
    assert b"About the Project" in response.data


def test_settings_page_renders(client):
    register_and_login(client)
    response = client.get("/settings")

    assert response.status_code == 200
    assert b"Account" in response.data
    assert b"<h2>Display</h2>" not in response.data


def test_translate_endpoint_returns_gloss(client):
    response = client.post("/translate", json={"sentences": ["I will eat an apple tomorrow"]})
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["sentences"] == ["I will eat an apple tomorrow"]
    assert payload["results"][0]["glossTokens"][0] == "FUTURE"
    assert "signAvailable" in payload["results"][0]
    assert "lemmas" in payload["results"][0]
    assert "analysisEngine" in payload["results"][0]


def test_sign_video_endpoint_404_when_missing(client):
    response = client.get("/api/signs/NOTASIGN/video")

    assert response.status_code == 404


def test_submission_endpoint_accepts_form(client):
    register_and_login(client)
    response = client.post(
        "/api/submissions",
        data={
            "english": "hello",
            "notes": "test note",
            "video": (BytesIO(b"fake-video"), "sign.webm"),
        },
        content_type="multipart/form-data",
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["status"] == "pending"
    assert "review" in payload["message"].lower()


def test_submission_rejects_missing_english(client):
    register_and_login(client)
    response = client.post("/api/submissions", data={"english": "  "})

    assert response.status_code == 400
    assert response.get_json()["error"]
