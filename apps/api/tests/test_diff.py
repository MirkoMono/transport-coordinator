from transport_api.services.diff import (
    build_assignment_map,
    build_eta_map,
    diff_assignments,
    diff_etas,
)


def test_diff_assignments_moved():
    before = {"p1": "Van 1", "p2": "Van 1"}
    after = {"p1": "Van 2", "p2": "Van 1"}
    result = diff_assignments(before, after, names={"p1": "Anna", "p2": "Bob"})
    assert len(result["moved"]) == 1
    assert result["moved"][0]["person_name"] == "Anna"
    assert result["moved"][0]["from_vehicle"] == "Van 1"
    assert result["moved"][0]["to_vehicle"] == "Van 2"


def test_diff_etas():
    changes = diff_etas({"p1": 10}, {"p1": 18}, names={"p1": "Anna"}, threshold=5)
    assert len(changes) == 1
    assert changes[0]["delta_minutes"] == 8


def test_build_maps():
    routes = [
        {
            "vehicle_id": "v1",
            "vehicle_name": "Van 1",
            "stops": [{"node_id": "p1", "eta_minutes": 12}],
        }
    ]
    assert build_assignment_map(routes) == {"p1": "Van 1"}
    assert build_eta_map(routes) == {"p1": 12}
