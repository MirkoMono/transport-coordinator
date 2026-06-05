from unittest.mock import patch

from fastapi.testclient import TestClient

from transport_api.main import app

client = TestClient(app)


def test_ai_parse_disabled():
    response = client.post(
        "/api/v1/ai/parse-call-sheet",
        json={"text": "Camera - Anna - Drottninggatan 1"},
    )
    assert response.status_code == 503


@patch("transport_api.main.settings.ai_enabled", True)
@patch("transport_api.main.parse_call_sheet_text")
def test_ai_parse_ok(mock_parse):
    mock_parse.return_value = [{"name": "Anna", "address": "Drottninggatan 1, Stockholm"}]

    response = client.post(
        "/api/v1/ai/parse-call-sheet",
        json={"text": "Camera - Anna - Drottninggatan 1 Stockholm"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["parsed_count"] == 1
    assert data["rows"][0]["name"] == "Anna"
