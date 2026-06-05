from unittest.mock import patch

from fastapi.testclient import TestClient
from transport_geospatial.geocoder import GeocodedAddress

from transport_api.main import app

client = TestClient(app)


@patch("transport_api.main.geocode_batch")
def test_geocode_batch_endpoint(mock_batch):
    mock_batch.return_value = [
        GeocodedAddress(
            query="Drottninggatan 1, Stockholm",
            latitude=59.33,
            longitude=18.06,
            display_name="Drottninggatan 1, Stockholm, Sweden",
            confidence=0.85,
        ),
        None,
    ]

    response = client.post(
        "/api/v1/addresses/geocode-batch",
        json={
            "items": [
                {"id": "a1", "name": "Anna", "address": "Drottninggatan 1, Stockholm"},
                {"id": "a2", "name": "Bob", "address": "nowhere invalid"},
            ],
            "country_bias": "se",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["geocoded_count"] == 1
    assert data["failed_count"] == 1
    assert data["results"][0]["geocoded"] is True
    assert data["results"][0]["latitude"] == 59.33
    assert data["results"][1]["geocoded"] is False


def test_csv_import_address_only():
    response = client.post(
        "/api/v1/addresses/bulk-import",
        json={
            "csv": "name,address\nAnna,Drottninggatan 1 Stockholm\n",
            "has_header": True,
        },
    )
    assert response.status_code == 200
    row = response.json()["rows"][0]
    assert row["name"] == "Anna"
    assert row["address"] == "Drottninggatan 1 Stockholm"
    assert row["latitude"] is None
    assert row["longitude"] is None


def test_csv_import_address_with_comma():
    response = client.post(
        "/api/v1/addresses/bulk-import",
        json={
            "csv": "name,address\nAnna Berg,Drottninggatan 1, Stockholm\n",
            "has_header": True,
        },
    )
    assert response.status_code == 200
    row = response.json()["rows"][0]
    assert row["name"] == "Anna Berg"
    assert row["address"] == "Drottninggatan 1, Stockholm"
