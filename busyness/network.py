"""The run and lift network a domain's skiers move through (busyness-network; docs/decisions/005).

Runs point downhill and lifts uphill; runs are cut where other lines end on them or cross them; lift stations join
runs passing nearby; short walks link lift tops and bottoms to nearby runs; enclosed lifts can be ridden down in the
evening; nursery lifts and slopes are marked, kept as links only. Each black piece gets its committed length.
"""

import math
import statistics
from collections import defaultdict
from dataclasses import dataclass, field

import build_stats as bs

from . import params as P
from .partition import Feature

Node = tuple[int, int]  # a junction: the (feature, point) that represents it


@dataclass
class Link:
    a: Node
    b: Node
    kind: str  # "run" | "lift" | "walk" | "download"
    fi: int | None  # the feature it comes from (None for walks)
    len: float  # metres
    t: float  # seconds, as skied or ridden
    route_t: float  # seconds, as it feels before ability: flat or very steep runs feel slower
    committed: float | None = None  # blacks: metres of black from its top before the next way out


@dataclass
class Network:
    feats: list[Feature]
    links: list[Link] = field(default_factory=list)
    z: dict[Node, float] = field(default_factory=dict)
    xy: dict[Node, tuple[float, float]] = field(default_factory=dict)
    out_links: dict[Node, list[Link]] = field(default_factory=lambda: defaultdict(list))
    in_links: dict[Node, list[Link]] = field(default_factory=lambda: defaultdict(list))
    order: list[Node] = field(default_factory=list)  # junctions, highest first
    crossings: int = 0
    origin: tuple[float, float] = (0.0, 0.0)  # lon, lat of the local metric frame

    @property
    def all_lifts(self) -> list[Link]:
        return [e for e in self.links if e.kind == "lift"]

    @property
    def lifts(self) -> list[Link]:
        """Lifts that carry skiing: not nursery lifts."""
        return [e for e in self.links if e.kind == "lift" and not self.feats[e.fi].nursery]

    def dist(self, n: Node, m: Node) -> float:
        return math.hypot(self.xy[n][0] - self.xy[m][0], self.xy[n][1] - self.xy[m][1])

    def cap(self, e: Link) -> float:
        return self.feats[e.fi].cap


def _length(ll) -> float:
    lons, lats = [c[0] for c in ll], [c[1] for c in ll]
    return sum(bs.geod.inv(lons[:-1], lats[:-1], lons[1:], lats[1:])[2])


def mark_nursery(feats: list[Feature]) -> None:
    """Nursery lifts (magic carpets, rope tows, short drags) and the short greens ending at them are for ski school:
    kept in the network as links people pass through, but with no pull for laps and not counted as village lifts."""
    def lowest(ll):
        return min((ll[0], ll[-1]), key=lambda c: c[2])

    nursery = [f for f in feats if f.kind == "lift" and
               (f.type in P.NURSERY_LIFTS or (f.type in P.DRAG_LIFTS and _length(f.ll) < P.NURSERY_DRAG_M))]
    bottoms = [lowest(f.ll) for f in nursery]
    kx = math.cos(math.radians(statistics.mean(c[1] for f in feats for c in f.ll))) * 111_320

    def near_nursery(c):
        return any(math.hypot((c[0] - b[0]) * kx, (c[1] - b[1]) * 111_320) <= P.NURSERY_SLOPE_END_M for b in bottoms)

    for f in nursery:
        f.nursery = True
    for f in feats:
        if f.kind == "run" and f.grade == 0 and _length(f.ll) < P.NURSERY_SLOPE_M and near_nursery(lowest(f.ll)):
            f.nursery = True


def project(feats: list[Feature]) -> tuple[float, float]:
    """Put every feature in metres from the domain's centre (good enough at a resort's scale)."""
    lon0 = statistics.mean(c[0] for f in feats for c in f.ll)
    lat0 = statistics.mean(c[1] for f in feats for c in f.ll)
    kx = math.cos(math.radians(lat0)) * 111_320
    for f in feats:
        f.xy = [((c[0] - lon0) * kx, (c[1] - lat0) * 111_320, c[2]) for c in f.ll]
    return lon0, lat0


def cross_runs(feats: list[Feature]) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    """Where two runs cross mid-way, put a point on both there, so skiers can switch runs. Returns the pairs of
    (feature, point index) to join. Crossings within SNAP_M of a line's end are left to the end joins."""
    runs = [fi for fi, f in enumerate(feats) if f.kind == "run"]
    box = {fi: (min(p[0] for p in feats[fi].xy), min(p[1] for p in feats[fi].xy),
                max(p[0] for p in feats[fi].xy), max(p[1] for p in feats[fi].xy)) for fi in runs}

    def along(f):  # distance along the line at each point
        d = [0.0]
        for a, b in zip(f.xy, f.xy[1:], strict=False):
            d.append(d[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        return d

    dists = {fi: along(feats[fi]) for fi in runs}
    adds = defaultdict(list)  # feature -> (segment, fraction, crossing id)
    n = 0
    for i, fi in enumerate(runs):
        for fj in runs[i + 1:]:
            A, B = box[fi], box[fj]
            if A[0] > B[2] or B[0] > A[2] or A[1] > B[3] or B[1] > A[3]:
                continue
            Pi, Qj = feats[fi].xy, feats[fj].xy
            for si in range(len(Pi) - 1):
                (x1, y1, _), (x2, y2, _) = Pi[si], Pi[si + 1]
                for sj in range(len(Qj) - 1):
                    (x3, y3, _), (x4, y4, _) = Qj[sj], Qj[sj + 1]
                    den = (x2 - x1) * (y4 - y3) - (y2 - y1) * (x4 - x3)
                    if den == 0:
                        continue
                    s = ((x3 - x1) * (y4 - y3) - (y3 - y1) * (x4 - x3)) / den
                    t = ((x3 - x1) * (y2 - y1) - (y3 - y1) * (x2 - x1)) / den
                    if not (0 <= s < 1 and 0 <= t < 1):  # a crossing at a shared point counts once
                        continue
                    at_i = dists[fi][si] + s * (dists[fi][si + 1] - dists[fi][si])
                    at_j = dists[fj][sj] + t * (dists[fj][sj + 1] - dists[fj][sj])
                    if min(at_i, dists[fi][-1] - at_i, at_j, dists[fj][-1] - at_j) < P.SNAP_M:
                        continue
                    adds[fi].append((si, s, n))
                    adds[fj].append((sj, t, n))
                    n += 1
    where = defaultdict(list)  # crossing id -> [(feature, new point index)]
    for fi, xs in adds.items():
        f = feats[fi]
        xs.sort()
        for key in ("xy", "ll"):
            old, new, k = getattr(f, key), [], 0
            for seg in range(len(old)):
                new.append(old[seg])
                while k < len(xs) and xs[k][0] == seg:
                    frac = xs[k][1]
                    new.append(tuple(p + frac * (q - p) for p, q in zip(old[seg], old[seg + 1], strict=True)))
                    k += 1
            setattr(f, key, new)
        for k, (seg, _frac, cid) in enumerate(xs):
            where[cid].append((fi, seg + 1 + k))
    return [tuple(v) for v in where.values()]


def _piece_len(pts) -> float:
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:], strict=False))


def build(feats: list[Feature]) -> Network:
    """The network for a domain's features: marks nursery areas, projects to metres, joins and cuts lines, adds walks
    and rides down, and works out each black's committed length."""
    mark_nursery(feats)
    net = Network(feats, origin=project(feats))
    crossings = cross_runs(feats)
    net.crossings = len(crossings)

    # Runs offer every vertex as a join point; lifts only their ends.
    grid = defaultdict(list)
    for fi, f in enumerate(feats):
        for vi in (range(len(f.xy)) if f.kind == "run" else (0, len(f.xy) - 1)):
            x, y, _ = f.xy[vi]
            grid[(int(x // P.SNAP_M), int(y // P.SNAP_M))].append((fi, vi))
    parent: dict[Node, Node] = {}

    def find(a):
        while parent.get(a, a) != a:
            parent[a] = parent.get(parent[a], parent[a])
            a = parent[a]
        return a

    # Each line end joins the nearest point of every other line within reach; that point cuts the other line.
    splits = defaultdict(set)
    for fi, f in enumerate(feats):
        for vi in (0, len(f.xy) - 1):
            splits[fi].add(vi)
            x, y, _ = f.xy[vi]
            r = P.LIFT_STATION_M if f.kind == "lift" else P.SNAP_M
            cells = math.ceil(r / P.SNAP_M)
            best = {}
            for dx in range(-cells, cells + 1):
                for dy in range(-cells, cells + 1):
                    for fj, vj in grid.get((int(x // P.SNAP_M) + dx, int(y // P.SNAP_M) + dy), ()):
                        if fj == fi:
                            continue
                        qx, qy, _ = feats[fj].xy[vj]
                        d = math.hypot(qx - x, qy - y)
                        if d <= (r if feats[fj].kind == "run" else P.SNAP_M) and d < best.get(fj, (math.inf,))[0]:
                            best[fj] = (d, vj)
            for fj, (_, vj) in best.items():
                parent[find((fi, vi))] = find((fj, vj))
                splits[fj].add(vj)
    for (fi, vi), (fj, vj) in crossings:
        parent[find((fi, vi))] = find((fj, vj))
        splits[fi].add(vi)
        splits[fj].add(vj)

    # A piece under 1 m (two cuts at one place) is dropped, so its ends must be one junction.
    for fi, f in enumerate(feats):
        cut = sorted(splits[fi])
        for i0, i1 in zip(cut, cut[1:], strict=False):
            if _piece_len(f.xy[i0:i1 + 1]) < 1:
                parent[find((fi, i0))] = find((fi, i1))

    node_pts = defaultdict(list)

    def node(fi, vi):
        n = find((fi, vi))
        node_pts[n].append(feats[fi].xy[vi])
        return n

    for fi, f in enumerate(feats):
        cut = sorted(splits[fi])
        for i0, i1 in zip(cut, cut[1:], strict=False):
            pts = f.xy[i0:i1 + 1]
            length = _piece_len(pts)
            if length < 1:
                continue
            a, b = node(fi, i0), node(fi, i1)
            if f.kind == "run":
                if pts[0][2] < pts[-1][2]:
                    a, b = b, a  # downhill
                t = length / (P.RUN_SPEED[f.grade] * P.flat_speed(f.grad))
                net.links.append(Link(a, b, "run", fi, length, t, t * P.route_effort(f.grad)))
            else:
                if pts[0][2] > pts[-1][2]:
                    a, b = b, a  # uphill
                t = (f.dur or length / P.LIFT_SPEED.get(f.type, P.DEFAULT_LIFT_SPEED)) + P.WAIT_S
                net.links.append(Link(a, b, "lift", fi, length, t, t))
    net.z = {n: statistics.mean(p[2] for p in v) for n, v in node_pts.items()}
    net.xy = {n: (statistics.mean(p[0] for p in v), statistics.mean(p[1] for p in v)) for n, v in node_pts.items()}

    # Walking links: lift tops to nearby run starts, nearby run ends to lift bottoms.
    starts = {e.a for e in net.links if e.kind == "run"}
    finishes = {e.b for e in net.links if e.kind == "run"}
    walks = []
    for lift in net.all_lifts:
        for s in starts:
            if s != lift.b and net.dist(lift.b, s) <= P.LIFT_TOP_M and -150 <= net.z[s] - net.z[lift.b] <= 30:
                walks.append(Link(lift.b, s, "walk", None, 0, P.WALK_S, P.WALK_S))
        for s in finishes:
            if s != lift.a and net.dist(lift.a, s) <= P.LIFT_BOTTOM_M and -30 <= net.z[s] - net.z[lift.a] <= 60:
                walks.append(Link(s, lift.a, "walk", None, 0, P.WALK_S, P.WALK_S))
    # Enclosed lifts can be ridden down on the way home in the evening (never for laps or in the morning).
    downs = [Link(lift.b, lift.a, "download", lift.fi, lift.len, lift.t, lift.route_t)
             for lift in net.all_lifts if feats[lift.fi].type in P.DOWNLOAD_LIFTS]
    net.links += walks + downs
    for e in net.links:
        net.out_links[e.a].append(e)
        net.in_links[e.b].append(e)
    net.order = sorted(net.z, key=lambda n: -net.z[n])
    commit_blacks(net)
    return net


def commit_blacks(net: Network) -> None:
    """For each black piece, the black skied from its top before the next way out: an easier run, a lift or a walk
    (a skier picks the shortest)."""
    def black(e):
        return e.kind == "run" and net.feats[e.fi].grade == 3

    to_out: dict[Node, float] = {}  # junction -> black still to ski from there before a way out
    for n in reversed(net.order):  # lowest first, so what's below is known
        outs = [e for e in net.out_links[n] if e.kind != "download"]
        if not outs or any(not black(e) for e in outs):
            to_out[n] = 0.0
        else:
            to_out[n] = min(e.len + to_out.get(e.b, 0.0) for e in outs)
    for e in net.links:
        if black(e):
            e.committed = e.len + to_out.get(e.b, 0.0)
