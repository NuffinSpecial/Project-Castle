from web_app import create_app


def test_index_page_renders():
    app = create_app()
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"Contextual ASL Translator" in response.data


def test_translate_endpoint_returns_gloss():
    app = create_app()
    client = app.test_client()

    response = client.post("/translate", json={"sentences": ["I will eat an apple tomorrow"]})
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["sentences"] == ["I will eat an apple tomorrow"]
    assert payload["results"][0]["glossTokens"][0] == "FUTURE"
    assert payload["results"][0]["links"]
