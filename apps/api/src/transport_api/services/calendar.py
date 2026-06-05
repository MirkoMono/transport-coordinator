"""iCalendar export for driver routes."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone


def _format_dt(dt: datetime) -> str:
    return dt.strftime("%Y%m%dT%H%M%SZ")


def generate_driver_ics(
    *,
    driver_name: str,
    vehicle_name: str,
    stops: list[dict],
    shoot_date: date | None = None,
    depot_departure_minutes: int = 0,
) -> str:
    """Generate a single-driver .ics calendar file."""
    base_date = shoot_date or date.today()
    tz = timezone.utc
    start = datetime(
        base_date.year,
        base_date.month,
        base_date.day,
        tzinfo=tz,
    ) + timedelta(minutes=depot_departure_minutes)

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Transport Coordinator//EN",
        "CALSCALE:GREGORIAN",
        f"X-WR-CALNAME:{vehicle_name} - {driver_name}",
    ]

    for stop in stops:
        event_start = start + timedelta(minutes=stop["eta_minutes"])
        event_end = event_start + timedelta(minutes=15)
        summary = f"Pickup: {stop.get('person_name', stop['node_id'])}"
        location = stop.get("address", "")
        uid = f"{stop['node_id']}@transport-coordinator"
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{_format_dt(datetime.now(tz))}",
                f"DTSTART:{_format_dt(event_start)}",
                f"DTEND:{_format_dt(event_end)}",
                f"SUMMARY:{summary}",
                f"LOCATION:{location}",
                f"DESCRIPTION:ETA {stop['eta_minutes']} min after depot departure",
                "END:VEVENT",
            ]
        )

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"
