"""Driver manifest PDF generation."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from datetime import date
from io import BytesIO

from fpdf import FPDF


def _pdf_text(value: str) -> str:
    """Fold unicode to Latin-1-safe ASCII for built-in Helvetica."""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return ascii_text.replace("--", "-")


@dataclass
class ManifestStop:
    sequence: int
    person_name: str
    address: str
    eta_minutes: int


@dataclass
class ManifestRoute:
    vehicle_name: str
    driver_name: str
    total_distance: int
    stops: list[ManifestStop]


def generate_manifest_pdf(
    routes: list[ManifestRoute],
    *,
    production_name: str = "Transport Coordinator",
    shoot_date: date | None = None,
) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    for route in routes:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, _pdf_text(production_name), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 8, _pdf_text(f"Vehicle: {route.vehicle_name}"), new_x="LMARGIN", new_y="NEXT")
        if route.driver_name:
            pdf.cell(0, 8, _pdf_text(f"Driver: {route.driver_name}"), new_x="LMARGIN", new_y="NEXT")
        if shoot_date:
            pdf.cell(0, 8, f"Date: {shoot_date.isoformat()}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(
            0,
            8,
            f"Route distance: {route.total_distance / 1000:.1f} km",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.ln(4)

        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Pickup order", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        pdf.set_font("Helvetica", "", 10)
        for stop in route.stops:
            line = f"{stop.sequence + 1}. {stop.person_name} - ETA {stop.eta_minutes} min"
            pdf.cell(0, 7, _pdf_text(line), new_x="LMARGIN", new_y="NEXT")
            if stop.address:
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(90, 90, 90)
                pdf.cell(0, 6, _pdf_text(f"   {stop.address}"), new_x="LMARGIN", new_y="NEXT")
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("Helvetica", "", 10)
            pdf.ln(1)

    buffer = BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()
