"""Split OpenSkiMap's runs and lifts into the site's domains, reading the raw files once (busyness-pipeline).

Membership comes from data/domains.json, written by build_stats.py: a feature belongs to a domain if any of its ski
areas is one the domain lists. Domains are chosen by id, never by name.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

import build_stats as bs

from . import params as P


@dataclass
class Domain:
    id: str
    name: str | None
    km: float
    lifts: int
    areas: list[str]


@dataclass
class Feature:
    """A run or lift line, with coordinates (lon, lat, altitude) and the properties the model uses."""
    kind: str  # "run" | "lift"
    id: str  # the site's id for it (build_stats.short_id)
    name: str | None
    ll: list[tuple[float, float, float]]
    grade: int = 4  # runs: 0 green .. 3 black, 4 ungraded
    grad: float = 0.0  # runs: average gradient, end to end
    type: str = ""  # lifts: OpenSkiMap liftType
    cap: float = 0.0  # lifts: capacity per hour (recorded or typical)
    cap_known: bool = False
    dur: float | None = None  # lifts: recorded ride time, seconds
    place: str | None = None  # lifts: locality or region, for naming sectors
    nursery: bool = False
    xy: list[tuple[float, float, float]] = field(default_factory=list)  # metres from the domain's centre, altitude


def load_domains(path: Path = P.ROOT / "data" / "domains.json") -> dict[str, Domain]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {k: Domain(k, v["name"], v["km"], v["lifts"], v["areas"]) for k, v in raw.items()}


def eligible(domains: dict[str, Domain]) -> dict[str, Domain]:
    """Domains big enough to model. Lifts are counted again without nursery lifts once the network is built."""
    return {k: d for k, d in domains.items() if d.km >= P.MIN_KM and d.lifts >= P.MIN_LIFTS}


def _complete(ln) -> bool:
    return len(ln) >= 2 and all(len(c) > 2 and c[2] is not None for c in ln)


def _run(p: dict, ln) -> Feature:
    lons, lats = [c[0] for c in ln], [c[1] for c in ln]
    length = sum(bs.geod.inv(lons[:-1], lats[:-1], lons[1:], lats[1:])[2])
    return Feature("run", bs.short_id(p["id"]), p["name"], [tuple(c[:3]) for c in ln],
                   grade=bs.GRADE.get(p["difficulty"], 4),
                   grad=abs(ln[0][2] - ln[-1][2]) / length if length > 0 else 0.0)


def _lift(p: dict, ln) -> Feature:
    cap = p.get("capacity")
    known = bool(cap and P.CAP_RANGE[0] <= cap <= P.CAP_RANGE[1])
    dur = p.get("duration")
    place = next((pl["localized"]["en"]["locality"] or pl["localized"]["en"]["region"] for pl in p["places"]
                  if pl["localized"]["en"]["locality"] or pl["localized"]["en"]["region"]), None)
    return Feature("lift", bs.short_id(p["id"]), p["name"] or "(unnamed lift)", [tuple(c[:3]) for c in ln],
                   type=p["liftType"], cap=cap if known else P.CAP_BY_TYPE.get(p["liftType"], 1000), cap_known=known,
                   dur=dur if dur and P.DURATION_RANGE[0] <= dur <= P.DURATION_RANGE[1] else None, place=place)


def partition(domains: dict[str, Domain], raw: Path = bs.RAW) -> dict[str, list[Feature]]:
    """Every wanted domain's runs (lines only, not piste areas) and operating lifts, in one pass over the raw files."""
    owner = {a: d.id for d in domains.values() for a in d.areas}
    out: dict[str, list[Feature]] = {d: [] for d in domains}

    def domains_of(p):
        return {owner[a["properties"]["id"]] for a in p["skiAreas"] if a["properties"]["id"] in owner}

    for f in bs.features(raw / "runs.geojson"):
        p = f["properties"]
        if not bs.keep_run(p) or f["geometry"]["type"] in ("Polygon", "MultiPolygon"):
            continue
        for d in domains_of(p):
            out[d] += [_run(p, ln) for ln in bs.lines_of(f["geometry"]) if _complete(ln)]
    for f in bs.features(raw / "lifts.geojson"):
        p = f["properties"]
        if p["status"] != "operating":
            continue
        for d in domains_of(p):
            out[d] += [_lift(p, ln) for ln in bs.lines_of(f["geometry"]) if _complete(ln)]
    return out
