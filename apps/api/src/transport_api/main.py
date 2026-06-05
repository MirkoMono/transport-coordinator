import csv
import io
import uuid
from datetime import date
from functools import lru_cache

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

from transport_api import __version__
from transport_api.config import settings
from transport_api.services.calendar import generate_driver_ics
from transport_api.services.manifest import ManifestRoute, ManifestStop, generate_manifest_pdf
from transport_api.services.matrix_cache import MatrixCache
from transport_api.services.persistence import (
    diff_runs,
    get_driver_manifest,
    get_run,
    list_runs,
    record_check_in,
    record_delay,
    save_optimization_run,
)
from transport_ai import get_provider, parse_call_sheet_text
from transport_geospatial import geocode_address, geocode_batch
from transport_solver import SolveRequest as SolverRequest
from transport_solver.solver import PickupNode, Vehicle, solve_vrp


class HealthResponse(BaseModel):
    status: str
    version: str
    ai_enabled: bool
    ai_status: str
    redis: str
    database: str


class PickupInput(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    demand: int = 1
    address: str = ""
    must_arrive_by_minutes: int | None = None


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
    save_run: bool = True
    call_time_minutes: int = Field(default=480, ge=0, le=24 * 60)
    locked_assignments: dict[str, str] = Field(default_factory=dict)


class CheckInRequest(BaseModel):
    run_id: str
    vehicle_id: str
    node_id: str


class DelayRequest(BaseModel):
    run_id: str
    vehicle_id: str
    node_id: str
    delay_minutes: int = Field(ge=0, le=180)
    note: str = ""


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
    run_id: str | None = None
    matrix_cache_hit: bool = False


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


class GeocodeBatchItem(BaseModel):
    id: str
    name: str
    address: str


class GeocodeBatchRequest(BaseModel):
    items: list[GeocodeBatchItem] = Field(min_length=1)
    country_bias: str = ""


class GeocodeBatchResult(BaseModel):
    id: str
    name: str
    address: str
    latitude: float | None = None
    longitude: float | None = None
    display_name: str = ""
    geocoded: bool = False
    error: str = ""


class GeocodeBatchResponse(BaseModel):
    results: list[GeocodeBatchResult]
    geocoded_count: int
    failed_count: int


class AIParseRequest(BaseModel):
    text: str = Field(min_length=10)


class AIParseRow(BaseModel):
    name: str
    address: str


class AIParseResponse(BaseModel):
    rows: list[AIParseRow]
    parsed_count: int
    ai_model: str


class ManifestStopInput(BaseModel):
    node_id: str
    person_name: str
    sequence: int
    eta_minutes: int
    address: str = ""


class ManifestRouteInput(BaseModel):
    vehicle_name: str
    driver_name: str = ""
    total_distance: int
    stops: list[ManifestStopInput]


class ManifestRequest(BaseModel):
    routes: list[ManifestRouteInput] = Field(min_length=1)
    production_name: str = "Transport Coordinator"


class CalendarRequest(BaseModel):
    vehicle_name: str
    driver_name: str = ""
    stops: list[ManifestStopInput]
    shoot_date: date | None = None
    depot_departure_minutes: int = 0


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


@lru_cache
def get_matrix_cache() -> MatrixCache:
    return MatrixCache(settings.redis_url, ttl_seconds=settings.matrix_cache_ttl)


@lru_cache
def get_ai_provider():
    return get_provider(
        enabled=settings.ai_enabled,
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
    )


def _ai_status() -> str:
    if not settings.ai_enabled:
        return "disabled"
    return "ok" if get_ai_provider().available else "unavailable"


def _vehicle_lookup(vehicles: list[VehicleInput]) -> dict[str, VehicleInput]:
    return {v.id: v for v in vehicles}


def _check_database() -> str:
    try:
        from sqlalchemy import text

        from transport_api.db.session import get_engine

        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        return "unavailable"


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    cache = get_matrix_cache()
    return HealthResponse(
        status="ok",
        version=__version__,
        ai_enabled=settings.ai_enabled,
        ai_status=_ai_status(),
        redis="ok" if cache.available else "unavailable",
        database=_check_database(),
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
            address = _parse_csv_address(raw)
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
            address = ", ".join(parts[3:]).strip() if len(parts) > 3 else ""
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
        bias = body.country_bias or settings.geocode_country_bias
        result = geocode_address(body.address, country_bias=bias)
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


@app.post("/api/v1/addresses/geocode-batch", response_model=GeocodeBatchResponse)
def geocode_batch_endpoint(body: GeocodeBatchRequest) -> GeocodeBatchResponse:
    """Geocode real addresses via Nominatim (accurate pins — not LLM coordinates)."""
    bias = body.country_bias or settings.geocode_country_bias
    addresses = [item.address or item.name for item in body.items]
    geocoded = geocode_batch(addresses, country_bias=bias)

    results: list[GeocodeBatchResult] = []
    ok = 0
    failed = 0
    for item, hit in zip(body.items, geocoded, strict=True):
        if hit is None:
            failed += 1
            results.append(
                GeocodeBatchResult(
                    id=item.id,
                    name=item.name,
                    address=item.address,
                    geocoded=False,
                    error="Address not found",
                )
            )
        else:
            ok += 1
            results.append(
                GeocodeBatchResult(
                    id=item.id,
                    name=item.name,
                    address=item.address or hit.display_name,
                    latitude=hit.latitude,
                    longitude=hit.longitude,
                    display_name=hit.display_name,
                    geocoded=True,
                )
            )
    return GeocodeBatchResponse(results=results, geocoded_count=ok, failed_count=failed)


@app.post("/api/v1/ai/parse-call-sheet", response_model=AIParseResponse)
def ai_parse_call_sheet(body: AIParseRequest) -> AIParseResponse:
    """Use local Gemma to extract name+address rows from messy production text."""
    provider = get_ai_provider()
    if not settings.ai_enabled:
        raise HTTPException(status_code=503, detail="AI is disabled. Set AI_ENABLED=true")
    try:
        rows = parse_call_sheet_text(body.text, provider)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI parse failed: {exc}") from exc

    return AIParseResponse(
        rows=[AIParseRow(name=r["name"], address=r["address"]) for r in rows],
        parsed_count=len(rows),
        ai_model=settings.ollama_model,
    )


@app.post("/api/v1/routes/optimize", response_model=OptimizeResponse)
def optimize_routes(body: OptimizeRequest) -> OptimizeResponse:
    for pickup in body.pickups:
        if pickup.latitude is None or pickup.longitude is None:
            raise HTTPException(
                status_code=400,
                detail=f"Pickup '{pickup.name}' is missing coordinates. Geocode first.",
            )

    coordinates = [(body.depot_latitude, body.depot_longitude)] + [
        (p.latitude, p.longitude) for p in body.pickups
    ]
    matrix, cache_hit = get_matrix_cache().get_or_build(coordinates)

    request = SolverRequest(
        pickups=[
            PickupNode(
                id=p.id,
                name=p.name,
                latitude=p.latitude,
                longitude=p.longitude,
                demand=p.demand,
                ready_minutes=0,
                due_minutes=p.must_arrive_by_minutes or body.call_time_minutes,
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
        distance_matrix=matrix,
        locked_assignments=body.locked_assignments or None,
    )

    try:
        result = solve_vrp(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    pickup_lookup = {p.id: p for p in body.pickups}
    vehicle_lookup = _vehicle_lookup(body.vehicles)

    route_outputs = [
        VehicleRouteOutput(
            vehicle_id=r.vehicle_id,
            vehicle_name=vehicle_lookup[r.vehicle_id].name,
            driver_name=vehicle_lookup[r.vehicle_id].driver_name,
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
    ]

    run_id: str | None = None
    if body.save_run:
        saved_id = save_optimization_run(
            solver_status=result.solver_status,
            total_distance=result.total_distance,
            input_payload=body.model_dump(),
            routes=[
                {
                    "vehicle_id": route.vehicle_id,
                    "vehicle_name": route.vehicle_name,
                    "driver_name": route.driver_name,
                    "total_distance": route.total_distance,
                    "stops": [
                        {
                            "node_id": stop.node_id,
                            "person_name": pickup_lookup[stop.node_id].name,
                            "sequence": stop.sequence,
                            "eta_minutes": stop.eta_minutes,
                            "address": pickup_lookup[stop.node_id].address,
                        }
                        for stop in route.stops
                    ],
                }
                for route in route_outputs
            ],
        )
        if saved_id:
            run_id = str(saved_id)

    return OptimizeResponse(
        routes=route_outputs,
        total_distance=result.total_distance,
        solver_status=result.solver_status,
        run_id=run_id,
        matrix_cache_hit=cache_hit,
    )


@app.post("/api/v1/routes/manifest.pdf")
def manifest_pdf(body: ManifestRequest) -> Response:
    pdf_bytes = generate_manifest_pdf(
        [
            ManifestRoute(
                vehicle_name=route.vehicle_name,
                driver_name=route.driver_name,
                total_distance=route.total_distance,
                stops=[
                    ManifestStop(
                        sequence=stop.sequence,
                        person_name=stop.person_name,
                        address=stop.address,
                        eta_minutes=stop.eta_minutes,
                    )
                    for stop in route.stops
                ],
            )
            for route in body.routes
        ],
        production_name=body.production_name,
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="driver-manifests.pdf"'},
    )


@app.get("/api/v1/runs")
def runs_list(limit: int = 20) -> dict:
    return {"runs": list_runs(limit=limit)}


@app.get("/api/v1/runs/{run_id}")
def runs_get(run_id: str) -> dict:
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid run id") from exc
    run = get_run(run_uuid)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@app.get("/api/v1/runs/{run_id}/diff/{other_id}")
def runs_diff(run_id: str, other_id: str) -> dict:
    try:
        a = uuid.UUID(run_id)
        b = uuid.UUID(other_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid run id") from exc
    diff = diff_runs(a, b)
    if not diff:
        raise HTTPException(status_code=404, detail="One or both runs not found")
    return diff


@app.get("/api/v1/drivers/{vehicle_id}/manifest")
def driver_manifest(vehicle_id: str, run_id: str) -> dict:
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid run id") from exc
    manifest = get_driver_manifest(run_uuid, vehicle_id)
    if not manifest:
        raise HTTPException(status_code=404, detail="Manifest not found")
    return manifest


@app.post("/api/v1/drivers/check-in")
def driver_check_in(body: CheckInRequest) -> dict:
    try:
        run_uuid = uuid.UUID(body.run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid run id") from exc
    if not record_check_in(run_uuid, body.vehicle_id, body.node_id):
        raise HTTPException(status_code=404, detail="Stop not found or database unavailable")
    return {"status": "checked_in"}


@app.post("/api/v1/drivers/delay")
def driver_delay(body: DelayRequest) -> dict:
    try:
        run_uuid = uuid.UUID(body.run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid run id") from exc
    if not record_delay(run_uuid, body.vehicle_id, body.node_id, body.delay_minutes, body.note):
        raise HTTPException(status_code=404, detail="Stop not found or database unavailable")
    return {"status": "delay_recorded", "delay_minutes": body.delay_minutes}


@app.post("/api/v1/routes/calendar.ics")
def route_calendar(body: CalendarRequest) -> Response:
    ics = generate_driver_ics(
        driver_name=body.driver_name,
        vehicle_name=body.vehicle_name,
        stops=[s.model_dump() for s in body.stops],
        shoot_date=body.shoot_date,
        depot_departure_minutes=body.depot_departure_minutes,
    )
    filename = f"{body.vehicle_name.replace(' ', '-').lower()}.ics"
    return Response(
        content=ics,
        media_type="text/calendar",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _parse_csv_address(raw: dict[str, str | list[str] | None]) -> str:
    """Join address column plus any extra CSV fields (commas in addresses are common)."""
    address = (
        raw.get("address")
        or raw.get("Address")
        or raw.get("location")
        or raw.get("Location")
        or ""
    )
    if isinstance(address, list):
        address = ", ".join(str(part).strip() for part in address if str(part).strip())
    else:
        address = str(address).strip()

    extras = raw.get(None)
    if extras:
        if isinstance(extras, list):
            address = ", ".join(
                [part for part in [address, *[str(x).strip() for x in extras if str(x).strip()]] if part]
            )
        else:
            extra = str(extras).strip()
            address = ", ".join([part for part in [address, extra] if part])

    return address


def _parse_float(value: str | None) -> float | None:
    if value is None or value.strip() == "":
        return None
    try:
        return float(value.strip())
    except ValueError:
        return None
