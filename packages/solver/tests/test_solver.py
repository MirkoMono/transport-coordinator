"""Golden-file tests for the VRP solver."""

import pytest

from transport_solver.solver import PickupNode, SolveRequest, Vehicle, solve_vrp


def test_twelve_pickups_three_vehicles():
    """12 people, 12 addresses, 3 vans (capacity 4 each) — classic production scenario."""
    pickups = [
        PickupNode(id=f"p{i}", name=f"Crew {i}", latitude=59.33 + i * 0.01, longitude=18.06)
        for i in range(12)
    ]
    vehicles = [
        Vehicle(id="v1", name="Van 1", capacity=4, driver_name="Driver A"),
        Vehicle(id="v2", name="Van 2", capacity=4, driver_name="Driver B"),
        Vehicle(id="v3", name="Van 3", capacity=4, driver_name="Driver C"),
    ]
    request = SolveRequest(
        pickups=pickups,
        vehicles=vehicles,
        depot_latitude=59.33,
        depot_longitude=18.06,
    )

    result = solve_vrp(request)

    assert len(result.routes) == 3
    assigned = sum(len(r.stops) for r in result.routes)
    assert assigned == 12
    for route in result.routes:
        assert len(route.stops) <= 4


def test_insufficient_capacity_raises():
    pickups = [PickupNode(id="p1", name="Solo", latitude=59.33, longitude=18.06)]
    vehicles = [Vehicle(id="v1", name="Tiny", capacity=0)]

    with pytest.raises(ValueError, match="Insufficient capacity"):
        solve_vrp(
            SolveRequest(
                pickups=pickups,
                vehicles=vehicles,
                depot_latitude=59.33,
                depot_longitude=18.06,
            )
        )
