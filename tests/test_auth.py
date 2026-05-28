import os
from io import BytesIO

from tests.conftest import register_and_login


def test_register_and_login(client):
    response = client.post(
        "/auth/register",
        data={
            "email": "alice@example.com",
            "username": "alice",
            "password": "securepass1",
            "confirm_password": "securepass1",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    client.post("/auth/logout", follow_redirects=True)  # POST logout

    response = client.post(
        "/auth/login",
        data={"email": "alice@example.com", "password": "securepass1"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"alice" in response.data


def test_submit_requires_login(client):
    response = client.post("/api/submissions", data={"english": "hello"})
    assert response.status_code == 302


def test_submission_pending_until_approved(client):
    register_and_login(client, email="bob@example.com", username="bob")

    response = client.post(
        "/api/submissions",
        data={
            "english": "hello",
            "notes": "test",
            "video": (BytesIO(b"fake-video"), "sign.webm"),
        },
        content_type="multipart/form-data",
    )
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["status"] == "pending"
    assert "review" in payload["message"].lower()

    video = client.get("/api/signs/HELLO/video")
    assert video.status_code == 404


def test_admin_approve_submission(tmp_path):
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

    client.post(
        "/auth/login",
        data={"email": "admin@castle.test", "password": "adminpass123"},
        follow_redirects=True,
    )

    client.post("/auth/logout", follow_redirects=True)  # POST logout

    client.post(
        "/auth/register",
        data={
            "email": "contributor@example.com",
            "username": "contributor",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=True,
    )

    submit = client.post(
        "/api/submissions",
        data={
            "english": "wave",
            "video": (BytesIO(b"fake-video"), "sign.webm"),
        },
        content_type="multipart/form-data",
    )
    submission_id = submit.get_json()["id"]

    client.post("/auth/logout", follow_redirects=True)  # POST logout
    client.post(
        "/auth/login",
        data={"email": "admin@castle.test", "password": "adminpass123"},
        follow_redirects=True,
    )

    approve = client.post(
        f"/admin/submissions/{submission_id}/approve",
        headers={"Accept": "application/json"},
    )
    assert approve.status_code == 200

    video = client.get("/api/signs/WAVE/video")
    assert video.status_code == 200


def test_non_admin_cannot_access_admin(client):
    register_and_login(client, email="member@example.com", username="member")
    response = client.get("/admin/")
    assert response.status_code == 403
