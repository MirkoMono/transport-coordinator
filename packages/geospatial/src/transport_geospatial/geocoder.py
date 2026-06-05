"""Address geocoding — Nominatim (OpenStreetMap) by default."""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "transport-coordinator/0.1.0"


@dataclass(frozen=True)
class GeocodedAddress:
    query: str
    latitude: float
    longitude: float
    display_name: str
    confidence: float


def geocode_address(
    address: str,
    *,
    client: httpx.Client | None = None,
    country_bias: str = "",
) -> GeocodedAddress:
    """Geocode a single address via Nominatim.

    Respects Nominatim usage policy: max 1 req/sec (enforced with sleep).
    For production, cache results in PostGIS (Phase 1b).
    """
    params: dict[str, str] = {
        "q": address,
        "format": "json",
        "limit": "1",
    }
    if country_bias:
        params["countrycodes"] = country_bias

    owns_client = client is None
    http = client or httpx.Client(
        headers={"User-Agent": USER_AGENT},
        timeout=10.0,
    )

    try:
        time.sleep(1.0)  # Nominatim rate limit
        response = http.get(NOMINATIM_URL, params=params)
        response.raise_for_status()
        results = response.json()
        if not results:
            raise ValueError(f"Address not found: {address}")

        hit = results[0]
        return GeocodedAddress(
            query=address,
            latitude=float(hit["lat"]),
            longitude=float(hit["lon"]),
            display_name=hit.get("display_name", address),
            confidence=0.8,
        )
    finally:
        if owns_client:
            http.close()
