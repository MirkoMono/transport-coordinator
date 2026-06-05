"""Vehicle Routing Problem solver using Google OR-Tools."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from ortools.constraint_solver import pywrapcp, routing_enums_pb2


@dataclass(frozen=True)
class PickupNode:
    id: str
    name: str
    latitude: float
    longitude: float
    demand: int = 1
    ready_minutes: int = 0
    due_minutes: int = 24 * 60


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
    locked_assignments: dict[str, str] | None = None
    max_route_minutes: int = 480


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


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    """Great-circle distance in meters."""
    r = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return int(2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


def build_distance_matrix(
    depot_latitude: float,
    depot_longitude: float,
    pickups: list[PickupNode],
) -> list[list[int]]:
    """Build distance matrix: index 0 = depot, 1..n = pickups."""
    points = [(depot_latitude, depot_longitude)] + [
        (p.latitude, p.longitude) for p in pickups
    ]
    size = len(points)
    matrix = [[0] * size for _ in range(size)]
    for i in range(size):
        for j in range(size):
            if i != j:
                lat1, lon1 = points[i]
                lat2, lon2 = points[j]
                matrix[i][j] = haversine_meters(lat1, lon1, lat2, lon2)
    return matrix


def travel_minutes(distance_meters: int, speed_kmh: float = 35.0) -> int:
    if distance_meters <= 0:
        return 0
    meters_per_minute = speed_kmh * 1000 / 60
    return max(1, round(distance_meters / meters_per_minute))


def solve_vrp(request: SolveRequest) -> SolveResult:
    """Solve a capacitated VRP with optional time windows and locked assignments."""
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

    locked = request.locked_assignments or {}
    vehicle_index = {v.id: idx for idx, v in enumerate(request.vehicles)}
    locked_by_vehicle: dict[str, int] = {}
    for node_id, vehicle_id in locked.items():
        if vehicle_id not in vehicle_index:
            raise ValueError(f"Unknown locked vehicle: {vehicle_id}")
        if not any(p.id == node_id for p in request.pickups):
            raise ValueError(f"Unknown locked pickup: {node_id}")
        locked_by_vehicle[vehicle_id] = locked_by_vehicle.get(vehicle_id, 0) + 1

    for vehicle in request.vehicles:
        locked_count = locked_by_vehicle.get(vehicle.id, 0)
        if locked_count > vehicle.capacity:
            raise ValueError(
                f"Vehicle '{vehicle.name}' has {locked_count} locked pickups "
                f"but capacity is {vehicle.capacity}"
            )

    matrix = request.distance_matrix or build_distance_matrix(
        request.depot_latitude,
        request.depot_longitude,
        request.pickups,
    )

    num_vehicles = len(request.vehicles)
    depot = 0
    manager = pywrapcp.RoutingIndexManager(len(matrix), num_vehicles, depot)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index: int, to_index: int) -> int:
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return matrix[from_node][to_node]

    def time_callback(from_index: int, to_index: int) -> int:
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return travel_minutes(matrix[from_node][to_node])

    distance_callback_index = routing.RegisterTransitCallback(distance_callback)
    time_callback_index = routing.RegisterTransitCallback(time_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(distance_callback_index)

    demands = [0] + [p.demand for p in request.pickups]

    def demand_callback(from_index: int) -> int:
        from_node = manager.IndexToNode(from_index)
        return demands[from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,
        [v.capacity for v in request.vehicles],
        True,
        "Capacity",
    )

    routing.AddDimension(
        time_callback_index,
        30,
        request.max_route_minutes,
        False,
        "Time",
    )
    time_dimension = routing.GetDimensionOrDie("Time")

    solver = routing.solver()
    for node_idx, pickup in enumerate(request.pickups, start=1):
        index = manager.NodeToIndex(node_idx)
        if pickup.due_minutes > pickup.ready_minutes:
            time_dimension.CumulVar(index).SetRange(pickup.ready_minutes, pickup.due_minutes)

        if pickup.id in locked:
            vehicle_idx = vehicle_index[locked[pickup.id]]
            solver.Add(routing.VehicleVar(index) == vehicle_idx)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.seconds = 10

    solution = routing.SolveWithParameters(search_parameters)
    if solution is None:
        raise RuntimeError(
            "OR-Tools could not find a feasible solution. "
            "Check that addresses geocoded to the correct city, call time allows enough "
            "travel, fleet capacity is sufficient, and locked assignments fit each van."
        )

    node_id_by_index = ["depot"] + [p.id for p in request.pickups]
    routes: list[VehicleRoute] = []
    total_distance = 0

    for vehicle_idx, vehicle in enumerate(request.vehicles):
        index = routing.Start(vehicle_idx)
        stops: list[RouteStop] = []
        route_distance = 0
        sequence = 0
        prev_node = depot

        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            if node != depot:
                leg = matrix[prev_node][node]
                route_distance += leg
                eta = solution.Value(time_dimension.CumulVar(index))
                stops.append(
                    RouteStop(
                        node_id=node_id_by_index[node],
                        sequence=sequence,
                        eta_minutes=eta,
                    )
                )
                sequence += 1
                prev_node = node
            index = solution.Value(routing.NextVar(index))

        if stops:
            leg = matrix[prev_node][depot]
            route_distance += leg
            routes.append(
                VehicleRoute(
                    vehicle_id=vehicle.id,
                    stops=stops,
                    total_distance=route_distance,
                )
            )
            total_distance += route_distance

    return SolveResult(
        routes=routes,
        total_distance=total_distance,
        solver_status="ROUTING_SUCCESS",
    )
