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
    rate_limit: bool = True,
) -> GeocodedAddress:
    """Geocode a single address via Nominatim."""
    if not address.strip():
        raise ValueError("Empty address")

    params: dict[str, str] = {
        "q": address.strip(),
        "format": "json",
        "limit": "1",
    }
    if country_bias:
        params["countrycodes"] = country_bias

    owns_client = client is None
    http = client or httpx.Client(
        headers={"User-Agent": USER_AGENT},
        timeout=15.0,
    )

    try:
        if rate_limit:
            time.sleep(1.0)
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
            confidence=0.85,
        )
    finally:
        if owns_client:
            http.close()


def geocode_batch(
    addresses: list[str],
    *,
    country_bias: str = "",
) -> list[GeocodedAddress | None]:
    """Geocode multiple addresses (1 req/sec Nominatim policy)."""
    results: list[GeocodedAddress | None] = []
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=15.0) as client:
        for i, address in enumerate(addresses):
            if not address.strip():
                results.append(None)
                continue
            try:
                if i > 0:
                    time.sleep(1.0)
                params: dict[str, str] = {
                    "q": address.strip(),
                    "format": "json",
                    "limit": "1",
                }
                if country_bias:
                    params["countrycodes"] = country_bias
                response = client.get(NOMINATIM_URL, params=params)
                response.raise_for_status()
                hits = response.json()
                if not hits:
                    results.append(None)
                    continue
                hit = hits[0]
                results.append(
                    GeocodedAddress(
                        query=address,
                        latitude=float(hit["lat"]),
                        longitude=float(hit["lon"]),
                        display_name=hit.get("display_name", address),
                        confidence=0.85,
                    )
                )
            except Exception:
                results.append(None)
    return results
