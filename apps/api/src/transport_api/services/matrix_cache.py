"""Redis-backed distance matrix cache."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING

from transport_geospatial.matrix import build_haversine_matrix

if TYPE_CHECKING:
    from redis import Redis


def _coords_key(coordinates: list[tuple[float, float]]) -> str:
    payload = json.dumps(
        [[round(lat, 5), round(lng, 5)] for lat, lng in coordinates],
        separators=(",", ":"),
    )
    digest = hashlib.sha256(payload.encode()).hexdigest()[:24]
    return f"matrix:{digest}"


class MatrixCache:
    def __init__(self, redis_url: str, ttl_seconds: int = 86_400) -> None:
        self._ttl = ttl_seconds
        self._redis: Redis | None = None
        self._available = False
        try:
            import redis

            client = redis.from_url(redis_url, decode_responses=True)
            client.ping()
            self._redis = client
            self._available = True
        except Exception:
            self._redis = None
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def get_or_build(self, coordinates: list[tuple[float, float]]) -> tuple[list[list[int]], bool]:
        """Return matrix and whether it was served from cache."""
        if self._redis is not None:
            cached = self._redis.get(_coords_key(coordinates))
            if cached:
                return json.loads(cached), True

        matrix = build_haversine_matrix(coordinates)

        if self._redis is not None:
            self._redis.set(_coords_key(coordinates), json.dumps(matrix), ex=self._ttl)

        return matrix, False
