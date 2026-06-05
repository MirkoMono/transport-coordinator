from transport_geospatial.matrix import build_haversine_matrix, haversine_meters


def test_haversine_same_point_is_zero():
    assert haversine_meters(59.33, 18.06, 59.33, 18.06) == 0


def test_build_matrix_symmetry():
    coords = [(59.33, 18.06), (59.34, 18.07), (59.35, 18.08)]
    matrix = build_haversine_matrix(coords)
    assert matrix[0][0] == 0
    assert matrix[1][2] == matrix[2][1]
    assert matrix[0][1] > 0
