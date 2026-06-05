"""Vehicle Routing Problem solver using Google OR-Tools."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PickupNode:
    id: str
    name: str
    latitude: float
    longitude: float
    demand: int = 1


@dataclass(frozen=True)
class Vehicle:
    id: str
    name: str
    capacity: int
    driver_name: str = ""


@dataclass
class SolveRequest:
    pickups: list[PickupNode]
    vehicles: list[Vehicle]
    depot_latitude: float
    depot_longitude: float
    distance_matrix: list[list[int]] | None = None


@dataclass
class RouteStop:
    node_id: str
    sequence: int
    eta_minutes: int = 0


@dataclass
class VehicleRoute:
    vehicle_id: str
    stops: list[RouteStop] = field(default_factory=list)
    total_distance: int = 0


@dataclass
class SolveResult:
    routes: list[VehicleRoute]
    total_distance: int
    solver_status: str


def solve_vrp(request: SolveRequest) -> SolveResult:
    """Solve a capacitated VRP with pickups.

    Phase 0 stub: validates input and returns a placeholder result.
    Full OR-Tools implementation arrives in Phase 1.
    """
    if not request.pickups:
        raise ValueError("At least one pickup is required")
    if not request.vehicles:
        raise ValueError("At least one vehicle is required")

    total_capacity = sum(v.capacity for v in request.vehicles)
    total_demand = sum(p.demand for p in request.pickups)
    if total_demand > total_capacity:
        raise ValueError(
            f"Insufficient capacity: {total_demand} passengers, {total_capacity} seats"
        )

    # Phase 0: round-robin assignment placeholder
    routes: list[VehicleRoute] = []
    pickup_idx = 0
    for vehicle in request.vehicles:
        stops: list[RouteStop] = []
        load = 0
        sequence = 0
        while pickup_idx < len(request.pickups) and load < vehicle.capacity:
            node = request.pickups[pickup_idx]
            stops.append(RouteStop(node_id=node.id, sequence=sequence))
            sequence += 1
            load += node.demand
            pickup_idx += 1
        if stops:
            routes.append(
                VehicleRoute(vehicle_id=vehicle.id, stops=stops, total_distance=0)
            )

    return SolveResult(
        routes=routes,
        total_distance=0,
        solver_status="PHASE0_PLACEHOLDER",
    )
