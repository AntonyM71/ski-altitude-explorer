"""busyness-sectors-villages and the commuting share."""

import pytest

from busyness.network import build
from busyness.places import Place
from busyness.sectors import exchange, find_sectors
from busyness.villages import find_villages

from .helpers import KX, LAT0, LON0, lift, run


def fork():
    """L1's top forks into two equal runs, one to L2's bottom and one to L3's."""
    return build([lift("L1", (0, -1000, 1500), (0, 0, 2200)),
                  run("A", (0, 0, 2200), (-600, -1000, 1500)), run("B", (0, 0, 2200), (600, -1000, 1500)),
                  lift("L2", (-600, -1000, 1500), (-600, -2000, 2200)),
                  lift("L3", (600, -1000, 1500), (600, -2000, 2200))])


def two_valleys():
    """Two separate valleys, each with two lifts whose skiers ski to each other."""
    feats = []
    for v, x in (("1", 0), ("2", 10_000)):
        feats += [lift(f"L{v}a", (x, -1000, 1500), (x, 0, 2200)),
                  run(f"R{v}a", (x, 0, 2200), (x + 800, -1000, 1500)),
                  lift(f"L{v}b", (x + 800, -1000, 1500), (x + 800, 0, 2200)),
                  run(f"R{v}b", (x + 800, 0, 2200), (x, -1000, 1500))]
    return build(feats)


def ids(net, fis):
    return {net.feats[fi].id for fi in fis}


def test_exchange_splits_by_pull():
    net = fork()
    l1 = next(e.fi for e in net.lifts if net.feats[e.fi].id == "L1")
    shares = {net.feats[fj].id: s for fj, s in exchange(net)[l1].items()}
    assert shares == pytest.approx({"L2": 0.5, "L3": 0.5}, abs=1e-6)


def test_two_equal_valleys_are_two_sectors_with_30_percent_commuting():
    net = two_valleys()
    s = find_sectors(net)
    assert sorted(sorted(ids(net, c)) for c in s.lifts) == [["L1a", "L1b"], ["L2a", "L2b"]]
    assert s.commute_share == pytest.approx([0.3, 0.3])


def test_single_sector_resort_has_no_commuting():
    net = build([lift("La", (0, -1000, 1500), (0, 0, 2200)), run("Ra", (0, 0, 2200), (800, -1000, 1500)),
                 lift("Lb", (800, -1000, 1500), (800, 0, 2200)), run("Rb", (800, 0, 2200), (0, -1000, 1500))])
    assert find_sectors(net).commute_share == [0.0]


def place(name, x, y, buildings, kind="village"):
    return Place(name, kind, LON0 + x / KX, LAT0 + y / 111_320, buildings)


def test_thoroughfare_is_not_a_village():
    net = two_valleys()
    s = find_sectors(net)
    vs = find_villages(net, s, [place("Real", 0, -1100, 300), place("Pass", 10_000, -1100, 10)])
    names = {v.name for v in vs}
    assert "Real" in names and "Pass" not in names  # valley 2 falls back to its busiest station


def test_neighbourhood_with_lifts_can_be_a_village():
    net = two_valleys()
    vs = find_villages(net, find_sectors(net), [place("Quarter", 10_000, -1100, 120, kind="suburb")])
    assert "Quarter" in {v.name for v in vs}


def test_station_high_above_the_village_is_left_out():
    # A second lift starts 300 m above the village's lowest station, 600 m from the place's point.
    # Each lift's run leads to the other's bottom, so they form one sector.
    feats = [lift("low", (0, -1000, 1500), (0, 0, 2200)), run("r1", (0, 0, 2200), (500, -700, 1800)),
             lift("high", (500, -700, 1800), (500, 300, 2400)), run("r2", (500, 300, 2400), (0, -1000, 1500))]
    net = build(feats)
    (v,) = find_villages(net, find_sectors(net), [place("Town", 0, -1100, 400)])
    assert {net.feats[e.fi].id for e in net.lifts if e.a in {n for n, _ in v.nodes}} == {"low"}


def test_skiers_shared_by_lifts_out_without_places():
    net = two_valleys()
    vs = find_villages(net, find_sectors(net), None)
    total = sum(net.cap(e) for e in net.lifts) / 3.5
    assert sum(v.skiers for v in vs) == pytest.approx(total)
