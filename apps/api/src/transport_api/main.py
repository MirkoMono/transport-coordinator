from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from transport_api import __version__
from transport_api.config import settings
from transport_solver import SolveRequest as SolverRequest
from transport_solver.solver import PickupNode, Vehicle, solve_vrp


class HealthResponse(BaseModel):
    status: str
    version: str
    ai_enabled: bool


class PickupInput(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    demand: int = 1


class VehicleInput(BaseModel):
    id: str
    name: str
    capacity: int
    driver_name: str = ""


class OptimizeRequest(BaseModel):
    pickups: list[PickupInput] = Field(min_length=1)
    vehicles: list[VehicleInput] = Field(min_length=1)
    depot_latitude: float
    depot_longitude: float


class RouteStopOutput(BaseModel):
    node_id: str
    sequence: int
    eta_minutes: int


class VehicleRouteOutput(BaseModel):
    vehicle_id: str
    stops: list[RouteStopOutput]
    total_distance: int


class OptimizeResponse(BaseModel):
    routes: list[VehicleRouteOutput]
    total_distance: int
    solver_status: str


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="Film production transport coordination API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=__version__,
        ai_enabled=settings.ai_enabled,
    )


@app.post("/api/v1/routes/optimize", response_model=OptimizeResponse)
def optimize_routes(body: OptimizeRequest) -> OptimizeResponse:
    request = SolverRequest(
        pickups=[
            PickupNode(
                id=p.id,
                name=p.name,
                latitude=p.latitude,
                longitude=p.longitude,
                demand=p.demand,
            )
            for p in body.pickups
        ],
        vehicles=[
            Vehicle(
                id=v.id,
                name=v.name,
                capacity=v.capacity,
                driver_name=v.driver_name,
            )
            for v in body.vehicles
        ],
        depot_latitude=body.depot_latitude,
        depot_longitude=body.depot_longitude,
    )
    result = solve_vrp(request)
    return OptimizeResponse(
        routes=[
            VehicleRouteOutput(
                vehicle_id=r.vehicle_id,
                stops=[
                    RouteStopOutput(
                        node_id=s.node_id,
                        sequence=s.sequence,
                        eta_minutes=s.eta_minutes,
                    )
                    for s in r.stops
                ],
                total_distance=r.total_distance,
            )
            for r in result.routes
        ],
        total_distance=result.total_distance,
        solver_status=result.solver_status,
    )
