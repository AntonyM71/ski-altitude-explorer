"""Villages: where a domain's skiers stay (docs/decisions/008).

Lift stations near a real place (a town, village or hamlet, or failing those a neighbourhood, with enough buildings)
form that place's village, up to VILLAGE_RISE_M above its lowest station. A village needs PLACE_VILLAGE_CAP of lifts
leaving it. Without places, villages come from the lift layout. Every sector houses skiers somewhere (its busiest
station if it has no village: known issue 5). The domain's skiers live in its villages, in proportion to each
village's own lifts out.
"""

import math
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass

from . import params as P
from .network import Network, Node
from .places import Place
from .sectors import Sectors


@dataclass
class Village:
    name: str
    sector: int
    nodes: list[tuple[Node, float]]  # stations: junction and lift capacity leaving it
    z: float
    cap: float = 0.0
    skiers: float = 0.0


def find_villages(net: Network, sectors: Sectors, places: list[Place] | None) -> list[Village]:
    bottoms = defaultdict(list)  # junction -> lifts starting there
    for lift in net.lifts:
        bottoms[lift.a].append(lift.fi)
    parent = {n: n for n in bottoms}

    def find(n):
        while parent[n] != n:
            parent[n] = parent[parent[n]]
            n = parent[n]
        return n

    nodes = list(bottoms)
    for i, n in enumerate(nodes):
        for m in nodes[i + 1:]:
            if net.dist(n, m) <= P.STATION_M and abs(net.z[n] - net.z[m]) < P.STATION_RISE_M:
                parent[find(n)] = find(m)
    groups = defaultdict(list)
    for n in nodes:
        groups[find(n)].append(n)
    stations = []
    for ns in groups.values():
        fis = [fi for n in ns for fi in bottoms[n]]
        stations.append({"nodes": ns, "fis": fis, "z": statistics.mean(net.z[n] for n in ns),
                         "cap": sum(net.feats[fi].cap for fi in fis),
                         "xy": (statistics.mean(net.xy[n][0] for n in ns), statistics.mean(net.xy[n][1] for n in ns))})

    def apart(s, t):
        return math.hypot(s["xy"][0] - t["xy"][0], s["xy"][1] - t["xy"][1])

    if places:
        lon0, lat0 = net.origin
        kx = math.cos(math.radians(lat0)) * 111_320
        pxy = [((p.lon - lon0) * kx, (p.lat - lat0) * 111_320) for p in places]
        by_place = defaultdict(list)
        # A town, village or hamlet first; a neighbourhood only where there's none within reach. Towns are mapped
        # as many neighbourhoods (Val d'Isère's quarters), but some resorts are only a neighbourhood (Val Claret).
        for s in stations:
            for suburb in (False, True):
                near = [(math.hypot(x - s["xy"][0], y - s["xy"][1]), i) for i, (x, y) in enumerate(pxy)
                        if (places[i].kind == "suburb") == suburb]
                d, i = min(near, default=(math.inf, None))
                if d <= P.PLACE_M:
                    by_place[i].append(s)
                    break
        # Too few buildings: a thoroughfare skiers pass through, not a village.
        by_place = {i: ss for i, ss in by_place.items() if places[i].buildings >= P.PLACE_MIN_BUILDINGS}
        # A village is its streets, not the slope above it.
        for i, ss in by_place.items():
            low = min(s["z"] for s in ss)
            by_place[i] = [s for s in ss if s["z"] - low <= P.VILLAGE_RISE_M]
        merged = []
        for i, ss in by_place.items():
            low = min(ss, key=lambda s: s["z"])
            merged.append({"nodes": [n for s in ss for n in s["nodes"]], "fis": [fi for s in ss for fi in s["fis"]],
                           "z": low["z"], "cap": sum(s["cap"] for s in ss), "xy": low["xy"],
                           "place": places[i].name, "village": sum(s["cap"] for s in ss) >= P.PLACE_VILLAGE_CAP})
        placed = {id(s) for ss in by_place.values() for s in ss}
        unplaced = [dict(s, village=False) for s in stations if id(s) not in placed]  # mid-mountain
        stations = merged + unplaced
    else:
        # Without places: a village has real lift capacity and no other such station below it nearby.
        for s in stations:
            s["village"] = s["cap"] >= P.VILLAGE_CAP and not any(
                t is not s and t["cap"] >= P.VILLAGE_CAP and t["z"] < s["z"] - 50 and apart(s, t) <= P.VILLAGE_RADIUS_M
                for t in stations)
        # A village spreads up its slope.
        for s in stations:
            if s["village"]:
                for t in stations:
                    if t is not s and not t["village"] and not t.get("taken") \
                            and 0 <= t["z"] - s["z"] <= P.VILLAGE_RISE_M and apart(s, t) <= P.VILLAGE_SPREAD_M:
                        s["nodes"] = s["nodes"] + t["nodes"]
                        s["fis"] = s["fis"] + t["fis"]
                        t["taken"] = True

    def node_cap(n):
        return sum(net.feats[fi].cap for fi in bottoms[n])

    villages: list[Village] = []
    for si in range(len(sectors.lifts)):
        mine = [Village(s.get("place") or max((net.feats[fi] for fi in s["fis"]), key=lambda f: f.cap).name, si,
                        [(n, node_cap(n)) for n in s["nodes"]], s["z"])
                for s in stations
                if s["village"] and Counter(sectors.sector_of[fi] for fi in s["fis"]).most_common(1)[0][0] == si]
        if not mine:  # every sector lives somewhere: its station with the most lift capacity leaving it
            lift_bottoms = {e.a for e in net.lifts if e.fi in sectors.lifts[si]}
            n = max(lift_bottoms, key=node_cap)
            mine = [Village(net.feats[bottoms[n][0]].name, si, [(n, node_cap(n))], net.z[n])]
        for v in mine:
            v.cap = sum(c for _, c in v.nodes)
        villages += mine
    # A village is sized by its own lifts out, not by the terrain above it.
    skiers = sum(net.cap(lift) for lift in net.lifts) / P.LIFTS_PER_HOUR
    access = sum(v.cap for v in villages)
    for v in villages:
        v.skiers = skiers * v.cap / access
    return villages
