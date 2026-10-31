"""busyness-network scenarios."""

from busyness.network import build

from .helpers import lift, run


def links_of(net, fid, kind="run"):
    return [e for e in net.links if e.kind == kind and e.fi is not None and net.feats[e.fi].id == fid]


def test_run_drawn_uphill_points_downhill():
    net = build([run("r", (0, 0, 1800), (0, 500, 2000)), lift("l", (0, -50, 1790), (0, 600, 2010))])
    (e,) = links_of(net, "r")
    assert net.z[e.a] > net.z[e.b]


def test_run_under_a_lift_is_not_connected():
    # The lift passes over the middle of the run; its ends are far from it.
    net = build([run("r", (-400, 0, 2000), (400, 0, 1800)), lift("l", (0, -600, 1700), (0, 600, 2300))])
    (e,) = links_of(net, "r")  # not cut
    lift_nodes = {x for le in links_of(net, "l", "lift") for x in (le.a, le.b)}
    assert not {e.a, e.b} & lift_nodes


def test_run_ending_beside_another_cuts_it():
    # Ends join the nearest vertex within reach; mapped runs have vertices every few tens of metres.
    main = run("main", *[(0, -y, 2000 - 0.3 * y) for y in range(0, 1001, 25)])
    net = build([main, run("side", (300, -400, 2000), (30, -500, 1850))])
    assert len(links_of(net, "main")) == 2
    (side,) = links_of(net, "side")
    assert side.b in {e.a for e in links_of(net, "main")}


def test_two_runs_crossing_in_an_x_are_joined():
    net = build([run("a", (-500, 0, 2000), (500, -1000, 1700)), run("b", (500, 0, 2000), (-500, -1000, 1700))])
    assert net.crossings == 1
    a, b = links_of(net, "a"), links_of(net, "b")
    assert len(a) == 2 and len(b) == 2
    assert {e.b for e in a if e.b in {x.a for x in a}} & {e.b for e in b if e.b in {x.a for x in b}}


def test_two_cuts_at_one_place_leave_no_dead_end():
    # Three runs crossing at one point: the crossing runs' cuts meet there.
    net = build([run("a", (-500, 0, 2000), (500, -1000, 1700)), run("b", (500, 0, 2000), (-500, -1000, 1700)),
                 run("c", (0, 0, 2000), (0, -1000, 1700))])
    for rid in "abc":
        pieces = links_of(net, rid)
        tops, bottoms = {e.a for e in pieces}, {e.b for e in pieces}
        assert len(bottoms - tops) == 1, f"run {rid} is broken into separate parts"


def test_walk_from_lift_top_to_a_run_below():
    net = build([lift("l", (0, -1000, 1500), (0, 0, 2040)), run("r", (120, 0, 2000), (120, -900, 1600))])
    (top,) = [e.b for e in links_of(net, "l", "lift")]
    walks = [e for e in net.out_links[top] if e.kind == "walk"]
    assert walks and walks[0].t == 30


def test_gondola_can_be_ridden_down_but_chair_cannot():
    net = build([lift("g", (0, -1000, 1500), (0, 0, 2000), type="gondola"),
                 lift("c", (500, -1000, 1500), (500, 0, 2000)),
                 run("r", (0, 0, 2000), (0, -1000, 1500)), run("r2", (500, 0, 2000), (500, -1000, 1500))])
    downs = [e for e in net.links if e.kind == "download"]
    assert [net.feats[e.fi].id for e in downs] == ["g"]
    (up,) = links_of(net, "g", "lift")
    assert (downs[0].a, downs[0].b) == (up.b, up.a)


def test_magic_carpet_and_its_slope_are_nursery():
    net = build([lift("carpet", (0, 0, 1500), (0, 100, 1520), type="magic_carpet"),
                 run("bunny", (0, 110, 1520), (20, 10, 1500), grade=0),
                 lift("chair", (500, 0, 1500), (500, 1000, 2000)), run("big", (500, 1000, 2000), (520, 0, 1500))])
    nursery = {f.id for f in net.feats if f.nursery}
    assert nursery == {"carpet", "bunny"}
    assert [net.feats[e.fi].id for e in net.lifts] == ["chair"]


def test_committed_length_of_a_black():
    # A 1,200 m black with no way out, and a black crossed by a blue 250 m from its top.
    net = build([run("long", (0, 0, 2400), (0, -1200, 1900), grade=3),
                 run("short", (1000, 0, 2400), (1000, -1200, 1900), grade=3),
                 run("escape", (700, -250, 2350), (1300, -250, 2250), grade=1)])
    (long,) = links_of(net, "long")
    assert abs(long.committed - 1200) < 5
    first = max(links_of(net, "short"), key=lambda e: net.z[e.a])
    assert abs(first.committed - 250) < 5
