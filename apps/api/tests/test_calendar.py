from transport_api.services.calendar import generate_driver_ics


def test_generate_driver_ics():
    ics = generate_driver_ics(
        driver_name="Driver A",
        vehicle_name="Van 1",
        stops=[
            {
                "node_id": "p1",
                "person_name": "Anna",
                "eta_minutes": 15,
                "address": "Stockholm",
            }
        ],
    )
    assert "BEGIN:VCALENDAR" in ics
    assert "Pickup: Anna" in ics
    assert "END:VCALENDAR" in ics
