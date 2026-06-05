from fastapi.testclient import TestClient

from transport_api.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert data["ai_enabled"] is False


def test_optimize_stub():
    response = client.post(
        "/api/v1/routes/optimize",
        json={
            "pickups": [
                {"id": "p1", "name": "Alice", "latitude": 59.33, "longitude": 18.06},
                {"id": "p2", "name": "Bob", "latitude": 59.34, "longitude": 18.07},
            ],
            "vehicles": [{"id": "v1", "name": "Van 1", "capacity": 4}],
            "depot_latitude": 59.33,
            "depot_longitude": 18.06,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["routes"]) == 1
    assert len(data["routes"][0]["stops"]) == 2
    assert data["solver_status"] != "PHASE0_PLACEHOLDER"
    assert data["total_distance"] > 0


def test_csv_import():
    response = client.post(
        "/api/v1/addresses/bulk-import",
        json={
            "csv": "name,latitude,longitude\nAlice,59.33,18.06\nBob,59.34,18.07\n",
            "has_header": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["parsed_count"] == 2
    assert data["rows"][0]["name"] == "Alice"
