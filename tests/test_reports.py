import os

from tests.conftest import register_and_login


def test_report_requires_login(client):
    response = client.post(
        "/api/reports",
        json={
            "type": "gloss",
            "originalSentence": "Hello world",
            "glossTokens": ["HELLO", "WORLD"],
            "message": "Wrong gloss order",
        },
    )
    assert response.status_code == 302


def test_create_gloss_report(client):
    register_and_login(client, email="reporter@example.com", username="reporter")

    response = client.post(
        "/api/reports",
        json={
            "type": "gloss",
            "originalSentence": "I am happy",
            "glossTokens": ["HAPPY", "I"],
            "message": "Gloss order does not match ASL grammar",
        },
    )
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["id"] >= 1


def test_create_video_report(client):
    register_and_login(client, email="vid@example.com", username="vidreporter")

    response = client.post(
        "/api/reports",
        json={
            "type": "video",
            "originalSentence": "Hello",
            "glossTokens": ["HELLO"],
            "glossToken": "HELLO",
            "submissionId": "sub-abc-123",
            "message": "Video shows the wrong sign",
        },
    )
    assert response.status_code == 200


def test_report_message_too_short(client):
    register_and_login(client, email="short@example.com", username="short")

    response = client.post(
        "/api/reports",
        json={
            "type": "gloss",
            "originalSentence": "Test",
            "glossTokens": ["TEST"],
            "message": "bad",
        },
    )
    payload = response.get_json()
    assert response.status_code == 400
    assert "5 characters" in payload["error"]


def test_translate_includes_submission_ids(client):
    response = client.post(
        "/translate",
        json={"sentences": ["Hello"]},
        headers={"Accept": "application/json"},
    )
    payload = response.get_json()
    assert response.status_code == 200
    result = payload["results"][0]
    assert "submissionIds" in result
    assert "signVariants" in result
    assert len(result["submissionIds"]) == len(result["glossTokens"])
    assert len(result["signVariants"]) == len(result["glossTokens"])


def test_admin_reports_flow(tmp_path):
    data = tmp_path / "data"
    data.mkdir(parents=True)
    (data / "submissions").mkdir()
    (data / "signs").mkdir()

    os.environ["CASTLE_DATA_DIR"] = str(data)
    os.environ["CASTLE_DATABASE"] = str(data / "castle.db")
    os.environ["FLASK_SECRET_KEY"] = "test-secret"
    os.environ["CASTLE_ADMIN_EMAIL"] = "admin@castle.test"
    os.environ["CASTLE_ADMIN_PASSWORD"] = "adminpass123"
    os.environ["CASTLE_ADMIN_USERNAME"] = "admin"

    from web_app import create_app

    application = create_app()
    application.config["TESTING"] = True
    client = application.test_client()

    register_and_login(client, email="user@castle.test", username="user")
    create = client.post(
        "/api/reports",
        json={
            "type": "gloss",
            "originalSentence": "Good morning",
            "glossTokens": ["MORNING", "GOOD"],
            "message": "Should be GOOD MORNING gloss",
        },
    )
    report_id = create.get_json()["id"]

    client.post("/auth/logout", follow_redirects=True)
    client.post(
        "/auth/login",
        data={"email": "admin@castle.test", "password": "adminpass123"},
        follow_redirects=True,
    )

    page = client.get("/admin/reports")
    assert page.status_code == 200
    assert b"Good morning" in page.data

    resolve = client.post(
        f"/admin/reports/{report_id}/resolve",
        json={"adminNote": "Fixed in catalog"},
        headers={"Accept": "application/json"},
    )
    assert resolve.status_code == 200

    from web_app.reports import get_report

    record = get_report(report_id)
    assert record is not None
    assert record.status == "resolved"
    assert record.admin_note == "Fixed in catalog"
