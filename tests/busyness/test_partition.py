"""busyness-pipeline: domains are those the site shows, by id, never by name."""

import json

from busyness.partition import Domain, eligible, partition


def area(aid, name):
    return {"properties": {"id": aid, "name": name}}


def run(fid, areas, coords, difficulty="easy", geom="LineString"):
    return {"type": "Feature", "properties": {
        "id": fid, "name": fid, "uses": ["downhill"], "status": "operating", "grooming": "classic",
        "difficulty": difficulty, "skiAreas": areas}, "geometry": {"type": geom, "coordinates": coords}}


def lift(fid, areas, coords, status="operating"):
    return {"type": "Feature", "properties": {
        "id": fid, "name": fid, "status": status, "liftType": "chair_lift", "capacity": 2400, "duration": None,
        "places": [], "skiAreas": areas}, "geometry": {"type": "LineString", "coordinates": coords}}


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


def test_eligible_needs_km_and_lifts():
    domains = {"a": Domain("a", "big", 40, 6, ["a"]), "b": Domain("b", "short", 12, 9, ["b"]),
               "c": Domain("c", "few lifts", 50, 3, ["c"])}
    assert list(eligible(domains)) == ["a"]
