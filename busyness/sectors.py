"""Sectors: groups of lifts that mostly exchange skiers among themselves (docs/decisions/007).

How lifts exchange skiers is computed exactly: lapping skiers form a Markov chain over junctions, each way on weighted
by its pull, and a lift ends the lap. From each lift's top, the share of its riders who next ride each lift is an
absorption probability, B = (I - Q)^-1 R. Lifts are then grouped by Louvain, and small groups merge into the neighbour
they exchange most with. This step is replaceable (known issue 11): find_sectors(net, params) -> Sectors.
"""

from collections import Counter
from dataclasses import dataclass

import networkx as nx
import numpy as np

from . import params as P
from .network import Link, Network

LEAK = 1e-9  # per step: makes I - Q invertible where a loop of links never reaches a lift, without changing results


@dataclass
class Sectors:
    sector_of: dict[int, int]  # lift feature -> sector
    lifts: list[set[int]]  # sector -> lift features
    cap: list[float]  # sector -> lift capacity
    name: list[str]
    commute_share: list[float]
    passes_to: dict[int, dict[int, float]]  # lift -> {next lift: riders per hour}
    day_sectors: dict[int, dict[int, float]]  # lift -> {sector: share of its riders' next lifts}


def gradient_pull(g: float, rule: dict) -> float:
    for below, factor in rule["flat"]:
        if g < below:
            return factor
    above, factor = rule["steep"]
    return factor if g > above else 1.0


def by_grade(net: Network, e: Link, table: list[float], beh: dict) -> float:
    """A run's value from a by-grade table; a black counts more like a red the shorter its committed stretch."""
    grade = net.feats[e.fi].grade
    if grade != 3:
        return table[grade]
    span = beh["BLACK_LONG_M"] - beh["BLACK_SHORT_M"]
    mix = min(1.0, max(0.0, (e.committed - beh["BLACK_SHORT_M"]) / span))
    return table[2] + mix * (table[3] - table[2])


def pull(net: Network, e: Link, beh: dict) -> float:
    """How strongly a way on draws lapping skiers at a junction (the same rules as the engine's laps)."""
    if e.kind == "download" or (e.fi is not None and net.feats[e.fi].nursery):
        return 0.0
    if e.kind == "lift":
        return net.cap(e) / beh["LIFT_PULL"]
    if e.kind == "walk":  # as strong as the best run it leads to
        return max((pull(net, x, beh) for x in net.out_links[e.b] if x.kind == "run"), default=1.0)
    return by_grade(net, e, beh["GRADE_PULL"], beh) * gradient_pull(net.feats[e.fi].grad, beh["GRADIENT_PULL"])


def exchange(net: Network, beh: dict | None = None) -> dict[int, dict[int, float]]:
    """For each lift (by feature), the share of riders leaving its top who next ride each lift."""
    beh = beh or P.behaviour()
    nodes = net.order
    idx = {n: i for i, n in enumerate(nodes)}
    lift_fis = sorted({e.fi for e in net.all_lifts})
    col = {fi: j for j, fi in enumerate(lift_fis)}
    Q = np.zeros((len(nodes), len(nodes)))
    R = np.zeros((len(nodes), len(lift_fis)))
    for n in nodes:
        outs = net.out_links[n]
        weights = [pull(net, e, beh) for e in outs]
        total = sum(weights)
        if total <= 0:
            continue  # nowhere to go (or only nursery ways): skiers stop here, as in the engine
        for e, w in zip(outs, weights, strict=True):
            if w <= 0:
                continue
            if e.kind == "lift":
                R[idx[n], col[e.fi]] += w / total
            else:
                Q[idx[n], idx[e.b]] += w / total
    B = np.linalg.solve(np.eye(len(nodes)) - Q * (1 - LEAK), R)
    return {e.fi: {fj: float(B[idx[e.b], j]) for fj, j in col.items() if B[idx[e.b], j] > 1e-9} for e in net.lifts}


def find_sectors(net: Network, beh: dict | None = None) -> Sectors:
    lifts = net.lifts
    cap_of_lift = {e.fi: net.cap(e) for e in lifts}
    shares = exchange(net, beh)
    passes_to = {fi: {fj: cap_of_lift[fi] * s for fj, s in got.items()} for fi, got in shares.items()}
    passed = Counter()
    for fi, got in passes_to.items():
        for fj, q in got.items():
            if fj != fi:
                passed[tuple(sorted((fi, fj)))] += q
    g = nx.Graph()
    g.add_nodes_from(cap_of_lift)
    for (a, b), q in passed.items():
        g.add_edge(a, b, weight=q)
    comms = [set(c) for c in nx.community.louvain_communities(g, weight="weight", seed=1)]

    def cap_of(c):
        return sum(cap_of_lift[fi] for fi in c)

    total = sum(cap_of_lift.values())
    while len(comms) > 1:
        small = [c for c in comms if cap_of(c) < P.SECTOR_MIN * total]
        if not small:
            break
        c = min(small, key=cap_of)
        target = max((d for d in comms if d is not c),
                     key=lambda d: sum(g[a][b]["weight"] for a in c for b in d if g.has_edge(a, b)))
        target |= c
        comms.remove(c)
    sector_of = {fi: i for i, c in enumerate(comms) for fi in c}
    # Nursery lifts belong to the sector of the nearest proper lift.
    for e in net.all_lifts:
        if e.fi not in sector_of:
            nearest = min(lifts, key=lambda lf: net.dist(lf.a, e.a))
            sector_of[e.fi] = sector_of[nearest.fi]
    # Where each lift's riders spend their time: the sectors of the lifts they take next.
    day_sectors = {}
    for fi, got in passes_to.items():
        spent = Counter()
        for fj, q in got.items():
            spent[sector_of[fj]] += q
        tot = sum(spent.values())
        day_sectors[fi] = {sj: q / tot for sj, q in spent.items()} if tot > 0 else {sector_of[fi]: 1.0}
    names = []
    for c in comms:
        places = Counter(net.feats[fi].place for fi in c if net.feats[fi].place)
        biggest = max(c, key=lambda fi: cap_of_lift[fi])
        names.append(f"{places.most_common(1)[0][0] if places else 'sector'} ({net.feats[biggest].name})")
    caps = [cap_of(c) for c in comms]
    domain_cap = sum(caps)
    share = [P.COMMUTE_TOP * (1 - c / domain_cap) for c in caps]
    return Sectors(sector_of, comms, caps, names, share, passes_to, day_sectors)
