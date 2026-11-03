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


def test_green_from_a_lift_station_to_a_nursery_area_is_a_way_through():
    # The green starts at the chair's bottom and ends by the carpet: skiers pass along it to the next lift.
    net = build([lift("carpet", (0, -160, 1500), (0, -60, 1510), type="magic_carpet"),
                 lift("chair", (0, 0, 1520), (0, 1000, 2000)), run("through", (10, 0, 1520), (10, -150, 1500), grade=0),
                 lift("chair2", (30, -170, 1500), (30, -1200, 2000))])
    assert {f.id for f in net.feats if f.nursery} == {"carpet"}


def test_run_stopping_short_walks_to_the_nearest_lift():
    # The run ends 300 m from the chair's bottom, with nothing mapped leading on.
    net = build([lift("chair", (0, 0, 1500), (0, 1000, 2000)), run("short", (0, 1000, 2000), (300, 0, 1500))])
    (end,) = [e.b for e in links_of(net, "short")]
    (walk,) = [e for e in net.out_links[end] if e.kind == "walk"]
    assert walk.b == links_of(net, "chair", "lift")[0].a and round(walk.t) == 300


def test_lift_top_with_no_run_walks_to_the_nearest_run_start():
    # The gondola's top is 400 m from where the run starts.
    net = build([lift("gondola", (0, 0, 1500), (0, 1000, 2500)), run("run", (400, 1000, 2480), (40, 0, 1500))])
    (top,) = [e.b for e in links_of(net, "gondola", "lift")]
    (walk,) = [e for e in net.out_links[top] if e.kind == "walk"]
    assert walk.b == links_of(net, "run")[0].a and round(walk.t) == 400


def test_no_backup_walk_where_a_way_on_exists():
    net = build([lift("chair", (0, 0, 1500), (0, 1000, 2000)), run("upper", (0, 1000, 2000), (300, 500, 1700)),
                 run("lower", (300, 500, 1700), (40, 0, 1500))])
    (mid,) = [e.b for e in links_of(net, "upper")]
    assert not [e for e in net.out_links[mid] if e.kind == "walk"]


def test_run_far_from_any_lift_is_dropped():
    net = build([lift("chair", (0, 0, 1500), (0, 1000, 2000)), run("home", (0, 1000, 2000), (40, 0, 1500)),
                 run("far", (0, 1000, 2000), (1500, -1500, 1400))])
    assert links_of(net, "far") == []
    assert links_of(net, "home")


def test_committed_length_of_a_black():
    # A 1,200 m black with no way out, and a black crossed by a blue 250 m from its top.
    net = build([run("long", (0, 0, 2400), (0, -1200, 1900), grade=3),
                 run("short", (1000, 0, 2400), (1000, -1200, 1900), grade=3),
                 run("escape", (700, -250, 2350), (1300, -250, 2250), grade=1)])
    (long,) = links_of(net, "long")
    assert abs(long.committed - 1200) < 5
    first = max(links_of(net, "short"), key=lambda e: net.z[e.a])
    assert abs(first.committed - 250) < 5


def station_walks_of(net):
    return [(e.a, e.b) for e in net.links if e.kind == "walk" and e.len > 0]


def bottom(net, lid):
    (e,) = links_of(net, lid, "lift")
    return e.a


def top(net, lid):
    (e,) = links_of(net, lid, "lift")
    return e.b


def test_two_lift_bottoms_a_short_walk_apart():
    net = build([lift("gondola", (0, 0, 1795), (0, 1500, 2300)), lift("funicular", (184, 0, 1810), (184, 1500, 2600))])
    a, b = bottom(net, "gondola"), bottom(net, "funicular")
    assert sorted(station_walks_of(net)) == sorted([(a, b), (b, a)])
    walk = next(e for e in net.links if e.kind == "walk" and e.a == a)
    assert 180 <= walk.t <= 190  # about 3 minutes at 1 m/s


def test_a_lift_top_near_another_lift_bottom_walks_one_way():
    net = build([lift("town", (0, -800, 1800), (0, 0, 1856)), lift("next", (161, 0, 1850), (161, 1200, 2300))])
    assert station_walks_of(net) == [(top(net, "town"), bottom(net, "next"))]


def test_no_walk_where_a_run_already_joins_them():
    net = build([lift("one", (0, -1000, 1800), (0, 0, 2315)), lift("two", (200, 0, 2295), (200, 1200, 2700)),
                 run("r", (0, 0, 2315), (200, 0, 2295))])
    assert station_walks_of(net) == []


def test_lift_bottoms_too_far_apart_are_not_joined():
    net = build([lift("a", (0, 0, 1800), (0, 1200, 2300)), lift("b", (300, 0, 1800), (300, 1200, 2300))])
    assert station_walks_of(net) == []


def test_a_walk_to_a_nearby_lift_pulls_like_that_lift():
    from busyness import params as P
    from busyness.sectors import pull

    net = build([lift("gondola", (0, 0, 1795), (0, 1500, 2300), cap=2500),
                 lift("funicular", (184, 0, 1810), (184, 1500, 2600), cap=1500)])
    a = bottom(net, "gondola")
    (walk,) = [e for e in net.out_links[a] if e.kind == "walk"]
    (up,) = [e for e in net.out_links[a] if e.kind == "lift"]
    beh = P.behaviour()
    assert pull(net, up, beh) == 3.125 and pull(net, walk, beh) == 1.875


def test_a_short_lift_does_not_walk_back_to_its_own_bottom():
    net = build([lift("carpet", (0, 0, 1500), (0, 200, 1520), type="t-bar")])
    assert station_walks_of(net) == []
