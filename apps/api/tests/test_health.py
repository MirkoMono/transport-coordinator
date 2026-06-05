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
    assert data["ai_status"] == "disabled"
    assert "redis" in data
    assert "database" in data


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
    assert "matrix_cache_hit" in data


def test_manifest_pdf_endpoint():
    response = client.post(
        "/api/v1/routes/manifest.pdf",
        json={
            "production_name": "Demo Shoot",
            "routes": [
                {
                    "vehicle_name": "Van 1",
                    "driver_name": "Driver A",
                    "total_distance": 5000,
                    "stops": [
                        {
                            "node_id": "p1",
                            "person_name": "Alice",
                            "sequence": 0,
                            "eta_minutes": 10,
                            "address": "Stockholm",
                        }
                    ],
                }
            ],
        },
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_runs_list():
    response = client.get("/api/v1/runs")
    assert response.status_code == 200
    assert "runs" in response.json()


def test_calendar_endpoint():
    response = client.post(
        "/api/v1/routes/calendar.ics",
        json={
            "vehicle_name": "Van 1",
            "driver_name": "Driver A",
            "stops": [
                {
                    "node_id": "p1",
                    "person_name": "Alice",
                    "sequence": 0,
                    "eta_minutes": 10,
                    "address": "Stockholm",
                }
            ],
        },
    )
    assert response.status_code == 200
    assert "text/calendar" in response.headers["content-type"]
    assert "BEGIN:VCALENDAR" in response.text


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
