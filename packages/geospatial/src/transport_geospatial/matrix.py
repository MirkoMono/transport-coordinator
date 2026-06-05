"""Distance matrix helpers."""

from __future__ import annotations

import math


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    r = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return int(2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


def build_haversine_matrix(coordinates: list[tuple[float, float]]) -> list[list[int]]:
    """Build a symmetric distance matrix from (lat, lng) pairs."""
    size = len(coordinates)
    matrix = [[0] * size for _ in range(size)]
    for i in range(size):
        for j in range(size):
            if i != j:
                lat1, lon1 = coordinates[i]
                lat2, lon2 = coordinates[j]
                matrix[i][j] = haversine_meters(lat1, lon1, lat2, lon2)
    return matrix
