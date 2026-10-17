from mocks.perf_tc17 import p95


def test_p95_nearest_rank():
    assert p95(list(range(1, 101))) == 95
    assert p95(list(range(100, 0, -1))) == 95  # order does not matter
    assert p95(list(range(1, 21))) == 19  # ceil(0.95 * 20) = 19th value
    assert p95([42]) == 42
