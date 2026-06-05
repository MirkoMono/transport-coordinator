"""Persist optimization runs to PostgreSQL."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from transport_api.db.models import OptimizationRun, SavedRoute, SavedRouteStop
from transport_api.db.session import get_session_factory
from transport_api.services.diff import (
    build_assignment_map,
    build_eta_map,
    diff_assignments,
    diff_etas,
)


def save_optimization_run(
    *,
    solver_status: str,
    total_distance: int,
    input_payload: dict,
    routes: list[dict],
) -> uuid.UUID | None:
    """Save run to database. Returns run id or None if DB unavailable."""
    try:
        session_factory = get_session_factory()
    except Exception:
        return None

    session = session_factory()
    try:
        run = OptimizationRun(
            solver_status=solver_status,
            total_distance=total_distance,
            input_payload=input_payload,
        )
        session.add(run)
        session.flush()

        for route in routes:
            saved = SavedRoute(
                run_id=run.id,
                vehicle_id=route["vehicle_id"],
                vehicle_name=route["vehicle_name"],
                driver_name=route.get("driver_name", ""),
                total_distance=route["total_distance"],
            )
            session.add(saved)
            session.flush()

            for stop in route["stops"]:
                session.add(
                    SavedRouteStop(
                        route_id=saved.id,
                        node_id=stop["node_id"],
                        person_name=stop.get("person_name", stop["node_id"]),
                        sequence=stop["sequence"],
                        eta_minutes=stop["eta_minutes"],
                        address=stop.get("address", ""),
                    )
                )

        session.commit()
        return run.id
    except SQLAlchemyError:
        session.rollback()
        return None
    finally:
        session.close()


def _run_to_dict(run: OptimizationRun) -> dict:
    routes = []
    for route in run.routes:
        routes.append(
            {
                "vehicle_id": route.vehicle_id,
                "vehicle_name": route.vehicle_name,
                "driver_name": route.driver_name,
                "total_distance": route.total_distance,
                "stops": [
                    {
                        "node_id": stop.node_id,
                        "person_name": stop.person_name,
                        "sequence": stop.sequence,
                        "eta_minutes": stop.eta_minutes,
                        "address": stop.address,
                        "checked_in_at": (
                            stop.checked_in_at.isoformat() if stop.checked_in_at else None
                        ),
                        "delay_minutes": stop.delay_minutes,
                        "delay_note": stop.delay_note or "",
                    }
                    for stop in route.stops
                ],
            }
        )
    return {
        "id": str(run.id),
        "solver_status": run.solver_status,
        "total_distance": run.total_distance,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "routes": routes,
    }


def list_runs(limit: int = 20) -> list[dict]:
    try:
        session_factory = get_session_factory()
    except Exception:
        return []

    session = session_factory()
    try:
        runs = session.scalars(
            select(OptimizationRun).order_by(OptimizationRun.created_at.desc()).limit(limit)
        ).all()
        return [
            {
                "id": str(run.id),
                "solver_status": run.solver_status,
                "total_distance": run.total_distance,
                "created_at": run.created_at.isoformat() if run.created_at else None,
            }
            for run in runs
        ]
    except SQLAlchemyError:
        return []
    finally:
        session.close()


def get_run(run_id: uuid.UUID) -> dict | None:
    try:
        session_factory = get_session_factory()
    except Exception:
        return None

    session = session_factory()
    try:
        run = session.scalar(
            select(OptimizationRun)
            .where(OptimizationRun.id == run_id)
            .options(
                joinedload(OptimizationRun.routes).joinedload(SavedRoute.stops),
            )
        )
        if not run:
            return None
        return _run_to_dict(run)
    except SQLAlchemyError:
        return None
    finally:
        session.close()


def diff_runs(run_id_a: uuid.UUID, run_id_b: uuid.UUID) -> dict | None:
    run_a = get_run(run_id_a)
    run_b = get_run(run_id_b)
    if not run_a or not run_b:
        return None

    names: dict[str, str] = {}
    for run in (run_a, run_b):
        for route in run["routes"]:
            for stop in route["stops"]:
                names[stop["node_id"]] = stop["person_name"]

    before_assign = build_assignment_map(run_a["routes"])
    after_assign = build_assignment_map(run_b["routes"])
    before_eta = build_eta_map(run_a["routes"])
    after_eta = build_eta_map(run_b["routes"])

    return {
        "run_a": run_a["id"],
        "run_b": run_b["id"],
        "assignments": diff_assignments(before_assign, after_assign, names=names),
        "eta_changes": diff_etas(before_eta, after_eta, names=names),
        "distance_delta_meters": run_b["total_distance"] - run_a["total_distance"],
    }


def get_driver_manifest(run_id: uuid.UUID, vehicle_id: str) -> dict | None:
    run = get_run(run_id)
    if not run:
        return None
    for route in run["routes"]:
        if route["vehicle_id"] == vehicle_id:
            return {
                "run_id": run["id"],
                "vehicle_id": route["vehicle_id"],
                "vehicle_name": route["vehicle_name"],
                "driver_name": route["driver_name"],
                "stops": route["stops"],
            }
    return None


def record_check_in(run_id: uuid.UUID, vehicle_id: str, node_id: str) -> bool:
    return _update_stop(run_id, vehicle_id, node_id, checked_in=True)


def record_delay(
    run_id: uuid.UUID,
    vehicle_id: str,
    node_id: str,
    delay_minutes: int,
    note: str = "",
) -> bool:
    return _update_stop(
        run_id,
        vehicle_id,
        node_id,
        delay_minutes=delay_minutes,
        delay_note=note,
    )


def _update_stop(
    run_id: uuid.UUID,
    vehicle_id: str,
    node_id: str,
    *,
    checked_in: bool = False,
    delay_minutes: int | None = None,
    delay_note: str = "",
) -> bool:
    try:
        session_factory = get_session_factory()
    except Exception:
        return False

    session = session_factory()
    try:
        run = session.scalar(
            select(OptimizationRun)
            .where(OptimizationRun.id == run_id)
            .options(joinedload(OptimizationRun.routes).joinedload(SavedRoute.stops))
        )
        if not run:
            return False

        target: SavedRouteStop | None = None
        for route in run.routes:
            if route.vehicle_id != vehicle_id:
                continue
            for stop in route.stops:
                if stop.node_id == node_id:
                    target = stop
                    break

        if not target:
            return False

        if checked_in:
            target.checked_in_at = datetime.now(timezone.utc)
        if delay_minutes is not None:
            target.delay_minutes = delay_minutes
            target.delay_note = delay_note

        session.commit()
        return True
    except SQLAlchemyError:
        session.rollback()
        return False
    finally:
        session.close()
