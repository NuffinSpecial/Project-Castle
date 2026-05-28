import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def pipeline():
    from asl_translator.pipeline import TranslationPipeline

    return TranslationPipeline(use_spacy=False)


@pytest.fixture
def app(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "submissions").mkdir()
    (data / "signs").mkdir()

    os.environ["CASTLE_DATA_DIR"] = str(data)
    os.environ["CASTLE_DATABASE"] = str(data / "castle.db")
    os.environ["FLASK_SECRET_KEY"] = "test-secret-key"

    from web_app import create_app

    application = create_app()
    application.config["TESTING"] = True
    application.config["WTF_CSRF_ENABLED"] = False
    return application


@pytest.fixture
def client(app):
    return app.test_client()


def register_and_login(
    client,
    *,
    email="user@example.com",
    username="testuser",
    password="password123",
):
    client.post(
        "/auth/register",
        data={
            "email": email,
            "username": username,
            "password": password,
            "confirm_password": password,
        },
        follow_redirects=True,
    )
