import fakeredis

from transport_api.services.matrix_cache import MatrixCache


def test_matrix_cache_roundtrip():
    server = fakeredis.FakeServer()
    client = fakeredis.FakeRedis(server=server, decode_responses=True)
    cache = MatrixCache("redis://unused")
    cache._redis = client
    cache._available = True

    coords = [(59.33, 18.06), (59.34, 18.07)]
    matrix1, hit1 = cache.get_or_build(coords)
    matrix2, hit2 = cache.get_or_build(coords)

    assert hit1 is False
    assert hit2 is True
    assert matrix1 == matrix2
    assert matrix1[0][1] > 0
