"""Small hand-made features for tests, laid out in metres around 6°E 45°N."""

import math

from busyness.partition import Feature

LAT0, LON0 = 45.0, 6.0
KX = math.cos(math.radians(LAT0)) * 111_320


def ll(*pts):
    """(x metres east, y metres north, altitude) -> (lon, lat, altitude)."""
    return [(LON0 + x / KX, LAT0 + y / 111_320, z) for x, y, z in pts]


def run(rid, *pts, grade=1):
    f = Feature("run", rid, rid, ll(*pts), grade=grade)
    length = sum(math.dist(a[:2], b[:2]) for a, b in zip(pts, pts[1:], strict=False))
    f.grad = abs(pts[0][2] - pts[-1][2]) / length
    return f


def lift(lid, *pts, type="chair_lift", cap=2000):
    return Feature("lift", lid, lid, ll(*pts), type=type, cap=cap, cap_known=True)
