"""Stream runs.geojson and write per-ski-area piste km by 100 m altitude band.

Output: data/ski_area_stats.json (small; the app loads it up front) and
data/runs/<area id>.json (simplified run and lift lines with elevation, loaded per domain for the map).
"""

import json
import shutil
from collections import Counter, defaultdict
from datetime import date
from itertools import combinations
from pathlib import Path

from pyproj import Geod

ROOT = Path(__file__).parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "ski_area_stats.json"
RUNS_OUT = ROOT / "data" / "runs"
SIMPLIFY_M = 30  # keep a vertex at least every 30 m along a run (or on a 15 m climb)

BIN = 100  # metres
MIN_ELE = -50  # below this an elevation is treated as bad data
SUB_AREA_SHARE = 0.8  # B is a sub-area of A if A shares >= 80% of B's runs
# Lift-pass networks of unlinked valleys: never a parent, hidden in the domain view.
PASS_NETWORKS = {"Dolomiti Superski", "Ski amadé"}

geod = Geod(ellps="WGS84")

# OpenSkiMap difficulty -> European grade index: 0 green, 1 blue, 2 red, 3 black, 4 ungraded.
GRADE = {"novice": 0, "easy": 1, "intermediate": 2, "advanced": 3, "expert": 3, "extreme": 3}


def features(path):
    """Yield features from OpenSkiMap's one-feature-per-line GeoJSON."""
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip().rstrip(",")
            if line.startswith('{"type":"Feature"') or line.startswith('{"properties"'):
                yield json.loads(line)


def keep_run(p):
    return (
        "downhill" in p["uses"]
        and p["status"] == "operating"
        and p["grooming"] != "backcountry"
        and p["difficulty"] != "freeride"
    )


def lines_of(geom):
    if geom["type"] == "LineString":
        return [geom["coordinates"]]
    if geom["type"] == "MultiLineString":
        return geom["coordinates"]
    return []  # Polygon piste areas have no meaningful length


def segments(coords):
    """Yield (horizontal_m, mid_altitude) per vertex-to-vertex segment, skipping bad elevations."""
    if len(coords) < 2 or len(coords[0]) < 3:
        return
    lons, lats, eles = zip(*((c[0], c[1], c[2]) for c in coords))
    _, _, dists = geod.inv(lons[:-1], lats[:-1], lons[1:], lats[1:])
    for d, z0, z1 in zip(dists, eles[:-1], eles[1:]):
        if z0 is None or z1 is None or min(z0, z1) < MIN_ELE:
            continue
        if abs(z1 - z0) > max(50, 2 * d):  # spike: steeper than ~63 degrees
            continue
        yield d, (z0 + z1) / 2


def simplified(coords):
    """A run line as [[lon, lat, ele], ...], thinned to SIMPLIFY_M spacing; bad elevations become null."""
    if len(coords) < 2:
        return None
    _, _, dists = geod.inv(*zip(*((c[0], c[1]) for c in coords[:-1])), *zip(*((c[0], c[1]) for c in coords[1:])))
    ele = lambda c: round(c[2]) if len(c) > 2 and c[2] is not None and c[2] >= MIN_ELE else None
    out, acc, last_z = [coords[0]], 0.0, ele(coords[0])
    for i, c in enumerate(coords[1:], 1):
        acc += dists[i - 1]
        z = ele(c)
        climb = z is not None and last_z is not None and abs(z - last_z) >= 15
        if acc >= SIMPLIFY_M or climb or i == len(coords) - 1:
            out.append(c)
            acc, last_z = 0.0, z
    return [[round(c[0], 5), round(c[1], 5), ele(c)] for c in out]


# Region -> group, in dropdown order.
REGIONS = {
    "Alps": "Europe",
    "Pyrenees": "Europe",
    "Nordics": "Europe",
    "Central European Uplands": "Europe",
    "Carpathians & Tatras": "Europe",
    "Apennines": "Europe",
    "Balkans & Greece": "Europe",
    "Iberia": "Europe",
    "British Isles": "Europe",
    "Caucasus & Turkey": "Europe",
    "Eastern Europe & Russia": "Europe",
    "North America West": "North America",
    "North America East": "North America",
    "Japan": "Asia",
    "Asia (other)": "Asia",
    "Southern Hemisphere": "Southern Hemisphere",
    "Other": "Other",
}
# Countries that sit in a single European region once the Alps and Pyrenees are taken out.
EUROPE_BY_COUNTRY = {
    **dict.fromkeys(["NO", "SE", "FI", "IS", "DK"], "Nordics"),
    **dict.fromkeys(["DE", "CZ", "BE", "NL", "LU", "FR", "AT", "CH", "LI"], "Central European Uplands"),
    **dict.fromkeys(["PL", "SK", "RO", "HU", "MD"], "Carpathians & Tatras"),
    **dict.fromkeys(["IT", "SM", "MT"], "Apennines"),
    **dict.fromkeys(["SI", "HR", "BA", "RS", "ME", "MK", "AL", "XK", "BG", "GR", "CY"], "Balkans & Greece"),
    **dict.fromkeys(["ES", "PT", "AD"], "Iberia"),
    **dict.fromkeys(["GB", "IE"], "British Isles"),
    **dict.fromkeys(["TR", "GE", "AM", "AZ"], "Caucasus & Turkey"),
    **dict.fromkeys(["BY", "EE", "LV", "LT"], "Eastern Europe & Russia"),
}


def in_alps(country, lon, lat):
    if country not in {"FR", "CH", "AT", "IT", "DE", "SI", "LI"}:
        return False
    if not (5 <= lon <= 16.5 and 43.7 <= lat <= 47.85):
        return False
    return lat >= 45.3 or lon < 8.2  # keeps the Maritime Alps, drops the Apennines


def region_of(country, lon, lat):
    """Skiing region (a key of REGIONS); checked in order, first match wins."""
    if lon is None or not country:
        return "Other"
    if lat < 0:
        return "Southern Hemisphere"
    if in_alps(country, lon, lat):
        return "Alps"
    if country in {"ES", "FR", "AD"} and 42.0 <= lat <= 43.2 and -2.0 <= lon <= 3.3:
        return "Pyrenees"
    if country == "UA":
        return "Carpathians & Tatras" if lon < 27 else "Eastern Europe & Russia"
    if country == "RU" and lon < 60:
        return "Caucasus & Turkey" if lat < 45 and lon > 37 else "Eastern Europe & Russia"
    if country in EUROPE_BY_COUNTRY:
        return EUROPE_BY_COUNTRY[country]
    if country in {"US", "CA"}:
        return "North America West" if lon < -100 else "North America East"
    if country == "JP":
        return "Japan"
    return "Asia (other)"


def main():
    bins = defaultdict(Counter)  # area id -> {bin start: metres}
    grade_bins = defaultdict(lambda: defaultdict(Counter))  # area id -> grade -> {bin start: metres}
    alt_range = {}  # area id -> [min, max]
    run_count = Counter()
    shared = Counter()  # (a, b) -> runs in both
    skipped = Counter()
    pass_ids = set()
    run_lines = defaultdict(list)  # area id -> JSON strings of its runs (shared between areas)

    for f in features(RAW / "runs.geojson"):
        p = f["properties"]
        if not keep_run(p):
            continue
        areas = sorted({a["properties"]["id"] for a in p["skiAreas"]})
        for a in p["skiAreas"]:
            if a["properties"]["name"] in PASS_NETWORKS:
                pass_ids.add(a["properties"]["id"])
        if not areas:
            skipped["no ski area"] += 1
            continue
        segs = [s for line in lines_of(f["geometry"]) for s in segments(line)]
        if not segs:
            skipped[f"no usable segments ({f['geometry']['type']})"] += 1
            continue
        run_bins = Counter()
        for d, z in segs:
            run_bins[int(z // BIN) * BIN] += d
        lo, hi = min(z for _, z in segs), max(z for _, z in segs)
        lines = [ln for ln in map(simplified, lines_of(f["geometry"])) if ln]
        run_json = json.dumps({"n": p["name"], "d": p["difficulty"], "c": lines}, ensure_ascii=False, separators=(",", ":"))
        grade = GRADE.get(p["difficulty"], 4)
        for a in areas:
            run_lines[a].append(run_json)
            bins[a].update(run_bins)
            grade_bins[a][grade].update(run_bins)
            r = alt_range.setdefault(a, [lo, hi])
            r[0], r[1] = min(r[0], lo), max(r[1], hi)
            run_count[a] += 1
        for pair in combinations(areas, 2):
            shared[pair] += 1

    # Sub-area detection: B's parent is the largest A that holds most of B's runs.
    parent = {}
    for (a, b), n in shared.items():
        for big, small in ((a, b), (b, a)):
            if big in pass_ids:
                continue
            if run_count[big] > run_count[small] and n >= SUB_AREA_SHARE * run_count[small]:
                if small not in parent or run_count[big] > run_count[parent[small]]:
                    parent[small] = big

    # Operating lifts, kept per area for the map, plus each area's highest lift station.
    lift_lines = defaultdict(list)
    lift_top = {}
    for f in features(RAW / "lifts.geojson"):
        p = f["properties"]
        areas = {a["properties"]["id"] for a in p["skiAreas"]}
        if p["status"] != "operating" or not areas:
            continue
        lines = [ln for ln in map(simplified, lines_of(f["geometry"])) if ln]
        if not lines:
            continue
        top = max((c[2] for ln in lines for c in ln if c[2] is not None), default=None)
        lift_json = json.dumps({"n": p["name"], "t": p["liftType"], "c": lines}, ensure_ascii=False, separators=(",", ":"))
        for a in areas:
            lift_lines[a].append(lift_json)
            if top is not None:
                lift_top[a] = max(lift_top.get(a, top), top)

    out = []
    country_names = {}
    for f in features(RAW / "ski_areas.geojson"):
        p = f["properties"]
        aid = p["id"]
        if aid not in bins:
            continue
        hist = {z: m / 1000 for z, m in sorted(bins[aid].items())}
        total = sum(hist.values())
        lon, lat = p["viewportHint"]["center"] if p.get("viewportHint") else (None, None)
        countries = list(dict.fromkeys(pl["iso3166_1Alpha2"] for pl in p["places"]))
        for pl in p["places"]:
            country_names.setdefault(pl["iso3166_1Alpha2"], pl["localized"]["en"]["country"])
        dh = p["statistics"]["runs"]["byActivity"].get("downhill", {}).get("byDifficulty", {})
        out.append({
            "id": aid,
            "name": p["name"],
            "countries": countries,
            "lon": lon,
            "lat": lat,
            "region": region_of(countries[0] if countries else None, lon, lat),
            "parent": parent.get(aid),
            "pass_network": aid in pass_ids,
            "runs": run_count[aid],
            "km": round(total, 2),
            "osm_km": round(sum(d["lengthInKm"] for d in dh.values()), 2),
            "min_alt": round(alt_range[aid][0]),
            "max_alt": round(alt_range[aid][1]),
            "lift_top": round(lift_top[aid]) if aid in lift_top else None,
            "median_alt": round(weighted_median(hist, total)),
            "hist": {str(z): round(km, 3) for z, km in hist.items()},
            # Per-grade km by band (grade index -> band -> km), for the grade filters.
            "gh": {str(g): {str(z): round(m / 1000, 2) for z, m in sorted(c.items()) if m >= 5}
                   for g, c in sorted(grade_bins[aid].items())},
        })

    # Refuse to publish if the download was truncated or the schema changed.
    if len(out) < 3000 or not any(a["name"] == "Les Trois Vallées" for a in out):
        raise SystemExit(f"sanity check failed: only {len(out)} ski areas, or Les Trois Vallées missing")

    doc = {"bin": BIN, "built": date.today().isoformat(), "regions": REGIONS, "countries": dict(sorted(country_names.items())), "areas": out}
    OUT.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {len(out)} ski areas to {OUT} ({OUT.stat().st_size / 1e6:.1f} MB)")

    shutil.rmtree(RUNS_OUT, ignore_errors=True)
    RUNS_OUT.mkdir(parents=True)
    size = 0
    for a in out:
        path = RUNS_OUT / f"{a['id']}.json"
        path.write_text('{"runs":[' + ",".join(run_lines[a["id"]]) + '],"lifts":[' + ",".join(lift_lines[a["id"]]) + "]}", encoding="utf-8")
        size += path.stat().st_size
    print(f"wrote {len(out)} run files to {RUNS_OUT} ({size / 1e6:.0f} MB)")
    for region, n in Counter(a["region"] for a in out if not a["parent"]).most_common():
        print(f"  {n:5} top-level areas: {region}")
    for reason, n in skipped.most_common():
        print(f"  skipped {n} runs: {reason}")


def weighted_median(hist, total):
    """Length-weighted median altitude, interpolated within the 100 m band."""
    acc = 0
    for z, km in hist.items():
        if acc + km >= total / 2:
            return z + BIN * (total / 2 - acc) / km
        acc += km
    return 0


if __name__ == "__main__":
    main()
