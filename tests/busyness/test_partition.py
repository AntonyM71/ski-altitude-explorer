"""busyness-pipeline: domains are those the site shows, by id, never by name."""

import json

from busyness import params as P
from busyness.partition import Domain, eligible, partition


def area(aid, name):
    return {"properties": {"id": aid, "name": name}}


def run(fid, areas, coords, difficulty="easy", geom="LineString"):
    return {"type": "Feature", "properties": {
        "id": fid, "name": fid, "uses": ["downhill"], "status": "operating", "grooming": "classic",
        "difficulty": difficulty, "skiAreas": areas}, "geometry": {"type": geom, "coordinates": coords}}


def lift(fid, areas, coords, status="operating", capacity=2400, occupancy=None):
    return {"type": "Feature", "properties": {
        "id": fid, "name": fid, "status": status, "liftType": "chair_lift", "capacity": capacity, "duration": None,
        "occupancy": occupancy, "places": [], "skiAreas": areas},
        "geometry": {"type": "LineString", "coordinates": coords}}


def write(path, feats):
    # OpenSkiMap's layout: one feature per line.
    path.write_text('{"type":"FeatureCollection","features":[\n'
                    + ",\n".join(json.dumps(f, separators=(",", ":")) for f in feats) + "\n]}\n", encoding="utf-8")


LINE = [[6.0, 45.0, 2000], [6.001, 45.0, 1900]]


def test_partition_by_id_with_shared_names(tmp_path):
    # Two unrelated ski areas called "Valley"; one domain is a linked pair (A + its member B).
    write(tmp_path / "runs.geojson", [
        run("r1", [area("A", "Valley")], LINE),
        run("r2", [area("B", "Peak")], LINE),
        run("r3", [area("C", "Valley")], LINE),
        run("r4", [area("A", "Valley")], [[[6, 45], [6.1, 45], [6.1, 45.1], [6, 45]]], geom="Polygon"),
        run("r5", [area("C", "Valley")], [[6.0, 45.0, None], [6.001, 45.0, 1900]]),  # no altitude: unusable
    ])
    write(tmp_path / "lifts.geojson", [
        lift("l1", [area("A", "Valley")], LINE[::-1]),
        lift("l2", [area("C", "Valley")], LINE[::-1], status="closed"),
    ])
    domains = {"linked-x": Domain("linked-x", "A / B", 40, 6, ["A", "B"]), "C": Domain("C", "Valley", 35, 5, ["C"])}
    out = partition(domains, raw=tmp_path)
    assert sorted(f.id for f in out["linked-x"]) == ["l1", "r1", "r2"]
    assert [f.id for f in out["C"]] == ["r3"]  # same name as A, but only its own run; no closed lift
    run3 = out["C"][0]
    assert run3.kind == "run" and run3.grade == 1 and run3.grad > 0


def test_lift_with_seats_and_no_capacity_is_estimated(tmp_path):
    write(tmp_path / "runs.geojson", [])
    write(tmp_path / "lifts.geojson", [lift("l1", [area("A", "Valley")], LINE[::-1], capacity=None, occupancy=2),
                                       lift("l2", [area("A", "Valley")], LINE[::-1])])
    est, rec = partition({"A": Domain("A", "Valley", 40, 6, ["A"])}, raw=tmp_path)["A"]
    assert (est.cap, est.cap_src) == (P.CHAIR_CAP[(2, False)], "seats")
    assert est.speed_src == "seats" and est.dur is None
    assert (rec.cap, rec.cap_src) == (2400, "recorded")


def test_eligible_needs_km_and_lifts():
    domains = {"a": Domain("a", "big", 40, 6, ["a"]), "b": Domain("b", "short", 12, 9, ["b"]),
               "c": Domain("c", "few lifts", 50, 3, ["c"])}
    assert list(eligible(domains)) == ["a"]
