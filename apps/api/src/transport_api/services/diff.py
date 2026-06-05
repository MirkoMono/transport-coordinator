"""Compare two optimization runs."""

from __future__ import annotations


def diff_assignments(
    before: dict[str, str],
    after: dict[str, str],
    *,
    names: dict[str, str] | None = None,
) -> dict:
    """Diff person -> vehicle assignments between two runs."""
    names = names or {}
    all_people = set(before) | set(after)
    moved = []
    added = []
    removed = []

    for person_id in sorted(all_people):
        label = names.get(person_id, person_id)
        old_vehicle = before.get(person_id)
        new_vehicle = after.get(person_id)
        if old_vehicle and new_vehicle and old_vehicle != new_vehicle:
            moved.append(
                {
                    "person_id": person_id,
                    "person_name": label,
                    "from_vehicle": old_vehicle,
                    "to_vehicle": new_vehicle,
                }
            )
        elif not old_vehicle and new_vehicle:
            added.append(
                {"person_id": person_id, "person_name": label, "vehicle": new_vehicle}
            )
        elif old_vehicle and not new_vehicle:
            removed.append(
                {"person_id": person_id, "person_name": label, "vehicle": old_vehicle}
            )

    return {"moved": moved, "added": added, "removed": removed}


def diff_etas(
    before: dict[str, int],
    after: dict[str, int],
    *,
    names: dict[str, str] | None = None,
    threshold: int = 2,
) -> list[dict]:
    names = names or {}
    changes = []
    for person_id in sorted(set(before) & set(after)):
        old_eta = before[person_id]
        new_eta = after[person_id]
        if abs(new_eta - old_eta) >= threshold:
            changes.append(
                {
                    "person_id": person_id,
                    "person_name": names.get(person_id, person_id),
                    "old_eta_minutes": old_eta,
                    "new_eta_minutes": new_eta,
                    "delta_minutes": new_eta - old_eta,
                }
            )
    return changes


def build_assignment_map(routes: list[dict]) -> dict[str, str]:
    """Map node_id -> vehicle_name from saved route payloads."""
    result: dict[str, str] = {}
    for route in routes:
        vehicle = route.get("vehicle_name") or route.get("vehicle_id", "")
        for stop in route.get("stops", []):
            result[stop["node_id"]] = vehicle
    return result


def build_eta_map(routes: list[dict]) -> dict[str, int]:
    result: dict[str, int] = {}
    for route in routes:
        for stop in route.get("stops", []):
            result[stop["node_id"]] = stop["eta_minutes"]
    return result
