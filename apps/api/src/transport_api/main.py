import csv
import io
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from transport_api import __version__
from transport_api.config import settings
from transport_geospatial import geocode_address
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
    address: str = ""


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
    vehicle_name: str
    driver_name: str
    stops: list[RouteStopOutput]
    total_distance: int


class OptimizeResponse(BaseModel):
    routes: list[VehicleRouteOutput]
    total_distance: int
    solver_status: str


class CsvImportRequest(BaseModel):
    csv: str
    has_header: bool = True


class CsvImportRow(BaseModel):
    id: str
    name: str
    latitude: float | None = None
    longitude: float | None = None
    address: str = ""


class CsvImportResponse(BaseModel):
    rows: list[CsvImportRow]
    parsed_count: int


class GeocodeRequest(BaseModel):
    address: str
    country_bias: str = ""


class GeocodeResponse(BaseModel):
    query: str
    latitude: float
    longitude: float
    display_name: str
    confidence: float


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


def _vehicle_lookup(vehicles: list[VehicleInput]) -> dict[str, VehicleInput]:
    return {v.id: v for v in vehicles}


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=__version__,
        ai_enabled=settings.ai_enabled,
    )


@app.post("/api/v1/addresses/bulk-import", response_model=CsvImportResponse)
def bulk_import_csv(body: CsvImportRequest) -> CsvImportResponse:
    reader = csv.DictReader(io.StringIO(body.csv)) if body.has_header else None
    rows: list[CsvImportRow] = []

    if reader:
        for raw in reader:
            name = (raw.get("name") or raw.get("Name") or "").strip()
            if not name:
                continue
            lat = _parse_float(raw.get("latitude") or raw.get("lat") or raw.get("Latitude"))
            lng = _parse_float(raw.get("longitude") or raw.get("lng") or raw.get("Longitude"))
            address = (raw.get("address") or raw.get("Address") or "").strip()
            rows.append(
                CsvImportRow(
                    id=str(uuid.uuid4()),
                    name=name,
                    latitude=lat,
                    longitude=lng,
                    address=address,
                )
            )
    else:
        for line in body.csv.strip().splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 1 or not parts[0]:
                continue
            name = parts[0]
            lat = _parse_float(parts[1]) if len(parts) > 1 else None
            lng = _parse_float(parts[2]) if len(parts) > 2 else None
            address = parts[3] if len(parts) > 3 else ""
            rows.append(
                CsvImportRow(
                    id=str(uuid.uuid4()),
                    name=name,
                    latitude=lat,
                    longitude=lng,
                    address=address,
                )
            )

    if not rows:
        raise HTTPException(status_code=400, detail="No valid rows found in CSV")

    return CsvImportResponse(rows=rows, parsed_count=len(rows))


@app.post("/api/v1/addresses/geocode", response_model=GeocodeResponse)
def geocode(body: GeocodeRequest) -> GeocodeResponse:
    try:
        result = geocode_address(body.address, country_bias=body.country_bias)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Geocoding failed: {exc}") from exc

    return GeocodeResponse(
        query=result.query,
        latitude=result.latitude,
        longitude=result.longitude,
        display_name=result.display_name,
        confidence=result.confidence,
    )


@app.post("/api/v1/routes/optimize", response_model=OptimizeResponse)
def optimize_routes(body: OptimizeRequest) -> OptimizeResponse:
    for pickup in body.pickups:
        if pickup.latitude is None or pickup.longitude is None:
            raise HTTPException(
                status_code=400,
                detail=f"Pickup '{pickup.name}' is missing coordinates. Geocode first.",
            )

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

    try:
        result = solve_vrp(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    lookup = _vehicle_lookup(body.vehicles)
    return OptimizeResponse(
        routes=[
            VehicleRouteOutput(
                vehicle_id=r.vehicle_id,
                vehicle_name=lookup[r.vehicle_id].name,
                driver_name=lookup[r.vehicle_id].driver_name,
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


def _parse_float(value: str | None) -> float | None:
    if value is None or value.strip() == "":
        return None
    try:
        return float(value.strip())
    except ValueError:
        return None
