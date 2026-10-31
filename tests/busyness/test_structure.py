"""busyness-pipeline: the structure file, and busyness-validation: impossible structures stop the run."""

import pytest

from busyness.partition import Domain
from busyness.sectors import find_sectors
from busyness.structure import StructureError, assemble, fingerprint, write
from busyness.villages import find_villages

from .test_sectors_villages import two_valleys

DOMAIN = Domain("d1", "Two Valleys", 40, 4, ["d1"])


def make():
    net = two_valleys()
    s = find_sectors(net)
    return net, s, find_villages(net, s, None)


def test_structure_holds_what_the_engine_needs(tmp_path):
    net, s, vs = make()
    doc = assemble(DOMAIN, net, s, vs, "abc", "none")
    assert len(doc["z"]) == len(net.z) and doc["z"] == sorted(doc["z"], reverse=True)  # highest first
    kinds = {link["k"] for link in doc["links"]}
    assert {"run", "lift"} <= kinds
    run = next(link for link in doc["links"] if link["k"] == "run")
    assert run["run"] in doc["runs"] and {"g", "grad", "len", "rt"} <= run.keys()
    lift = next(link for link in doc["links"] if link["k"] == "lift")
    assert str(lift["lift"]) in doc["lifts"] and doc["lifts"][str(lift["lift"])]["sector"] in (0, 1)
    assert [sec["share"] for sec in doc["sectors"]] == [0.3, 0.3]
    assert sum(v["skiers"] for v in doc["villages"]) == pytest.approx(8000 / 3.5, abs=1)
    path = write(doc, tmp_path)
    assert path.name == "d1.json" and path.stat().st_size > 0


def test_a_bad_commuting_share_stops_without_writing(tmp_path):
    net, s, vs = make()
    s.commute_share[0] = -0.2
    with pytest.raises(StructureError):
        write(assemble(DOMAIN, net, s, vs, "abc", "none"), tmp_path)
    assert not list(tmp_path.iterdir())


def test_fingerprint_changes_with_the_features():
    net, *_ = make()
    a = fingerprint(net.feats, None)
    net.feats[0].cap += 100
    assert fingerprint(net.feats, None) != a
