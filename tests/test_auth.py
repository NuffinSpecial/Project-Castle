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


def _admin_client(tmp_path):
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
    return client, data


def test_admin_signs_list_page(tmp_path):
    client, _ = _admin_client(tmp_path)
    response = client.get("/admin/signs")
    assert response.status_code == 200
    assert b"Manage signs" in response.data


def test_admin_delete_submission(tmp_path):
    client, data = _admin_client(tmp_path)

    client.post("/auth/logout", follow_redirects=True)
    client.post(
        "/auth/register",
        data={
            "email": "c@example.com",
            "username": "contributor",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=True,
    )

    submit = client.post(
        "/api/submissions",
        data={
            "english": "thanks",
            "video": (BytesIO(b"fake-video"), "sign.webm"),
        },
        content_type="multipart/form-data",
    )
    submission_id = submit.get_json()["id"]

    client.post("/auth/logout", follow_redirects=True)
    client.post(
        "/auth/login",
        data={"email": "admin@castle.test", "password": "adminpass123"},
        follow_redirects=True,
    )

    client.post(f"/admin/submissions/{submission_id}/approve")
    assert client.get("/api/signs/THANKS/video").status_code == 200

    delete = client.post(f"/admin/submissions/{submission_id}/delete", follow_redirects=True)
    assert delete.status_code == 200
    assert not (data / "submissions" / submission_id).exists()
    assert client.get("/api/signs/THANKS/video").status_code == 404


def test_admin_replace_video(tmp_path):
    client, _ = _admin_client(tmp_path)

    submit = client.post(
        "/api/submissions",
        data={
            "english": "hello",
            "video": (BytesIO(b"old-video"), "sign.webm"),
        },
        content_type="multipart/form-data",
    )
    submission_id = submit.get_json()["id"]

    replace = client.post(
        f"/admin/submissions/{submission_id}/replace-video",
        data={"video": (BytesIO(b"new-video-content"), "new.webm")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert replace.status_code == 200

    record_path = tmp_path / "data" / "submissions" / submission_id / "metadata.json"
    import json

    meta = json.loads(record_path.read_text(encoding="utf-8"))
    assert meta["video"] == "new.webm"


def test_admin_revoke_approval(tmp_path):
    client, _ = _admin_client(tmp_path)

    submit = client.post(
        "/api/submissions",
        data={
            "english": "wave",
            "video": (BytesIO(b"fake"), "sign.webm"),
        },
        content_type="multipart/form-data",
    )
    submission_id = submit.get_json()["id"]
    client.post(f"/admin/submissions/{submission_id}/approve")
    assert client.get("/api/signs/WAVE/video").status_code == 200

    client.post(f"/admin/submissions/{submission_id}/revoke", follow_redirects=True)
    assert client.get("/api/signs/WAVE/video").status_code == 404
