"""Stream runs.geojson and write per-ski-area piste km by 100 m altitude band.

Output: data/ski_area_stats.json (small; the app loads it up front) and
data/runs/<area id>.json (simplified run and lift lines with elevation, loaded per domain for the map).
"""

import hashlib
import json
import math
import shutil
import sys
from collections import Counter, defaultdict
from datetime import date
from itertools import combinations
from pathlib import Path

import shapely
from pyproj import Geod
from shapely.geometry import LineString, shape

ROOT = Path(__file__).parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "ski_area_stats.json"
RUNS_OUT = ROOT / "data" / "runs"
DOMAINS_OUT = ROOT / "data" / "domains.json"
SIMPLIFY_M = 30  # keep a vertex at least every 30 m along a run (or on a 15 m climb)

BIN = 100  # metres
MIN_ELE = -50  # below this an elevation is treated as bad data
SUB_AREA_SHARE = 0.8  # B is a sub-area of A if A shares >= 80% of B's runs
# Lift-pass networks of unlinked valleys: never a parent, hidden in the domain view.
PASS_NETWORKS = {"Dolomiti Superski", "Ski amadé"}

# Linked domains OpenSkiMap doesn't group: top-level areas whose runs or lifts touch are joined.
# Pistes mapped only as an area (an outline, no run line) are counted with an estimated length.
AREA_EDGE_M = 15  # a run line this close to an area's outline counts as running along it
AREA_LINE_M = 40  # an area with more than this much run line along it is already counted
SNAP_M = 30  # a line end this close to another area's run or lift joins the two areas
SNAP_CELL = 0.0005  # grid cell for the snap search, in degrees (about 40-55 m)
LINK_MIN = 1  # touching points (plus runs tagged to both) needed to join two areas
LINKED_ALONE = 0.85  # a linked set keeps its largest member's name if that member has this share of the km
# Names for linked sets, keyed by any member's name.
LINKED_NAMES = {
    "Sestriere": "Via Lattea",
    "La Thuile ski": "Espace San Bernardo",
    "Masella": "Alp 2500",
    "Artesina": "Mondolè Ski",
    "Valle Nevado": "Tres Valles",
    "Grindelwald - Wengen (Kleine Scheidegg - Männlichen)": "Jungfrau Ski Region",
    "Snowbird": "Alta and Snowbird",
    "Palisades Tahoe Olympic Valley": "Palisades Tahoe",
    "Andermatt+Disentis+Sedrun": "Andermatt-Sedrun-Disentis",
    "Ylläs": "Ylläs",
    "Kolašin 1600": "Kolašin",
    "志賀高原 焼額山スキー場, Shiga Kogen Yakebitaiyama Ski Area, 焼額山スキー場": "Shiga Kogen",
    "志賀高原 横手山スキー場, Shiga Kogen Yokoteyama Ski Area": "Shiga Kogen Yokoteyama and Shibutoge",
}

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
    return []  # piste areas: see area_pistes()


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
    run_info = []  # (areas, grade, bins, lo, hi, json) per run, to rebuild linked sets without double counting
    counted_lines = []  # 2D run lines, to tell which piste areas a run already runs along
    piste_areas = []  # (feature, areas) for piste areas, sorted out after the runs
    ends = defaultdict(list)  # snap grid cell -> [((lon, lat), areas)] for every run and lift end

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
        if f["geometry"]["type"] in ("Polygon", "MultiPolygon"):
            piste_areas.append((f, areas))
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
        run_json = json.dumps({"i": short_id(p["id"]), "n": p["name"], "d": p["difficulty"], "c": lines},
                              ensure_ascii=False, separators=(",", ":"))
        grade = GRADE.get(p["difficulty"], 4)
        run_info.append((areas, grade, run_bins, lo, hi, run_json))
        index_ends(ends, f["geometry"], areas)
        counted_lines.extend(LineString([(c[0], c[1]) for c in ln]) for ln in lines if len(ln) >= 2)
        for a in areas:
            run_lines[a].append(run_json)
            run_count[a] += 1
        for pair in combinations(areas, 2):
            shared[pair] += 1

    # Piste areas with no run line along them are counted too, with an estimated length.
    area_lines = defaultdict(list)  # area id -> JSON strings of its area-only pistes
    area_only = set()  # their feature ids, so their outlines can link resorts
    for f, areas, run_bins, grade, lo, hi, area_json in area_pistes(piste_areas, counted_lines, skipped):
        area_only.add(f["properties"]["id"])
        run_info.append((areas, grade, run_bins, lo, hi, None))
        index_outline(ends, f["geometry"], areas)
        for a in areas:
            area_lines[a].append(area_json)
            run_count[a] += 1
        for pair in combinations(areas, 2):
            shared[pair] += 1

    for areas, grade, run_bins, lo, hi, _ in run_info:
        for a in areas:
            bins[a].update(run_bins)
            grade_bins[a][grade].update(run_bins)
            r = alt_range.setdefault(a, [lo, hi])
            r[0], r[1] = min(r[0], lo), max(r[1], hi)

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
    lift_info = []  # (areas, top, json) per lift, for linked sets
    for f in features(RAW / "lifts.geojson"):
        p = f["properties"]
        areas = {a["properties"]["id"] for a in p["skiAreas"]}
        if p["status"] != "operating" or not areas:
            continue
        lines = [ln for ln in map(simplified, lines_of(f["geometry"])) if ln]
        if not lines:
            continue
        top = max((c[2] for ln in lines for c in ln if c[2] is not None), default=None)
        lift_json = json.dumps({"i": short_id(p["id"]), "n": p["name"], "t": p["liftType"], "c": lines},
                               ensure_ascii=False, separators=(",", ":"))
        lift_info.append((areas, top, lift_json))
        index_ends(ends, f["geometry"], areas)
        for a in areas:
            lift_lines[a].append(lift_json)
            if top is not None:
                lift_top[a] = max(lift_top.get(a, top), top)

    linked_sets = find_linked_sets(ends, parent, pass_ids, shared, run_count, area_only)

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

    # Linked sets become synthetic domains; their members become its sub-areas.
    by_id = {a["id"]: a for a in out}
    linked_members = {}  # linked domain id -> member area ids
    for members in linked_sets:
        members = [m for m in members if m in by_id]
        if len(members) < 2:
            continue
        dom = linked_domain(members, by_id, parent, run_info, lift_info)
        linked_members[dom["id"]] = members
        area_lines[dom["id"]] = [j for m in members for j in area_lines_of(m, parent, area_lines)]
        for m in members:
            by_id[m]["parent"] = dom["id"]
        run_lines[dom["id"]], lift_lines[dom["id"]] = dom.pop("_runs"), dom.pop("_lifts")
        out.append(dom)
    linked = sorted((a for a in out if a.get("linked")), key=lambda a: -a["km"])
    print(f"{len(linked)} linked domains joined from touching areas:")
    for a in linked:
        print(f"  {a['km']:6.0f} km  {a['name']}: {', '.join(a['linked'])}")

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
        path.write_text('{"runs":[' + ",".join(run_lines[a["id"]]) + '],"lifts":[' + ",".join(lift_lines[a["id"]])
                        + '],"areas":[' + ",".join(dict.fromkeys(area_lines[a["id"]])) + "]}", encoding="utf-8")
        size += path.stat().st_size
    print(f"wrote {len(out)} run files to {RUNS_OUT} ({size / 1e6:.0f} MB)")

    # The domains the site lists (linked domains on), with the ski areas whose runs and lifts belong to each, so the
    # busyness pipeline uses exactly the site's membership. A feature belongs if any of its ski areas is listed.
    domains = {}
    for a in out:
        if a["parent"] or a["pass_network"]:
            continue
        members = linked_members.get(a["id"])
        areas = sorted({x for m in members for x in [m, *descendants(m, parent)]}) if members else [a["id"]]
        domains[a["id"]] = {"name": a["name"], "km": a["km"], "lifts": len(lift_lines[a["id"]]), "areas": areas}
    DOMAINS_OUT.write_text(json.dumps(domains, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {len(domains)} domains to {DOMAINS_OUT}")
    for region, n in Counter(a["region"] for a in out if not a["parent"]).most_common():
        print(f"  {n:5} top-level areas: {region}")
    for reason, n in skipped.most_common():
        print(f"  skipped {n} runs: {reason}")


def snap_cell(lon, lat):
    return math.floor(lon / SNAP_CELL), math.floor(lat / SNAP_CELL)


def index_ends(ends, geom, areas):
    """Add each line's two end points, with the line's areas, to the snap grid."""
    for ln in lines_of(geom):
        if len(ln) >= 2:
            for pt in (ln[0], ln[-1]):
                ends[snap_cell(pt[0], pt[1])].append(((pt[0], pt[1]), areas))


def outline_of(geom):
    """The outer rings of a piste area, as lines."""
    polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    return [poly[0] for poly in polys]


def index_outline(ends, geom, areas):
    """Add every vertex of an area's outline to the snap grid, so the area can link like a run end."""
    for ring in outline_of(geom):
        for pt in ring:
            ends[snap_cell(pt[0], pt[1])].append(((pt[0], pt[1]), areas))


def in_metres(g):
    """g projected to metres around its own centre: plenty accurate at the scale of one piste."""
    c = g.centroid
    kx = math.cos(math.radians(c.y)) * 111_320
    return shapely.transform(g, lambda xy: (xy - (c.x, c.y)) * (kx, 111_320))


def area_pistes(piste_areas, counted_lines, skipped):
    """Yield (feature, areas, bins, grade, lo, hi, json) for each piste area no counted run runs along.

    Its length is the long side of the strip with the same area and perimeter, which on areas that do have a
    run along them comes out at 1.03x the run's length (95% within 25%). The length is spread evenly over the
    altitude between the outline's lowest and highest vertex.
    """
    tree = shapely.STRtree(counted_lines)
    pad = AREA_EDGE_M / 111_320 * 2  # generous in degrees; the exact test is in metres
    for f, areas in piste_areas:
        g = shape(f["geometry"]).buffer(0)
        if g.is_empty:
            continue
        near = [counted_lines[i] for i in tree.query(g.buffer(pad))]
        if near:
            c = g.centroid
            kx = math.cos(math.radians(c.y)) * 111_320
            to_m = lambda h: shapely.transform(h, lambda xy: (xy - (c.x, c.y)) * (kx, 111_320))
            zone = to_m(g).buffer(AREA_EDGE_M)
            if sum(to_m(ln).intersection(zone).length for ln in near) > AREA_LINE_M:
                continue
        m = in_metres(g)
        half = m.length / 2
        disc = half * half - 4 * m.area
        length = (half + math.sqrt(disc)) / 2 if disc > 0 else math.sqrt(m.area)
        zs = [c[2] for ring in outline_of(f["geometry"]) for c in ring if len(c) > 2 and c[2] is not None and c[2] >= MIN_ELE]
        if not zs or length < 1:
            skipped["piste area with no usable altitude"] += 1
            continue
        lo, hi = min(zs), max(zs)
        run_bins = Counter()
        if hi - lo < 1:
            run_bins[int(lo // BIN) * BIN] = length
        else:
            for b in range(int(lo // BIN) * BIN, int(hi // BIN) * BIN + BIN, BIN):
                run_bins[b] += length * (min(hi, b + BIN) - max(lo, b)) / (hi - lo)
        p = f["properties"]
        rings = [[[round(c[0], 5), round(c[1], 5)] for c in ring] for ring in outline_of(f["geometry"])]
        area_json = json.dumps({"n": p["name"], "d": p["difficulty"], "a": rings, "lo": round(lo), "hi": round(hi), "km": round(length / 1000, 2)},
                               ensure_ascii=False, separators=(",", ":"))
        yield f, areas, run_bins, GRADE.get(p["difficulty"], 4), lo, hi, area_json


def area_lines_of(a, parent, area_lines):
    """Area-only pistes of area a and of every area below it."""
    yield from area_lines[a]
    for child, par in parent.items():
        if par == a:
            yield from area_lines_of(child, parent, area_lines)


def descendants(a, parent):
    """Every area below area a."""
    for child, par in parent.items():
        if par == a:
            yield child
            yield from descendants(child, parent)


def short_id(feature_id):
    """A run's or lift's id in the site's files: the start of OpenSkiMap's, unique enough within a domain."""
    return feature_id[:12]


def top_of(parent, a):
    while a in parent:
        a = parent[a]
    return a


def find_linked_sets(ends, parent, pass_ids, shared, run_count, area_only):
    """Top-level areas joined by touching runs or lifts, as lists of area ids, largest first.

    Every run and lift vertex is checked against other areas' line ends within SNAP_M, so a run that
    finishes at another resort's lift, or joins its piste, links the two. Runs tagged to two top-level
    areas link them too. Links chain: A-B and B-C make one set.
    """
    def tops(areas):
        return {top_of(parent, a) for a in areas if a not in pass_ids}

    touches = defaultdict(set)  # (a, b) -> touching end points
    sources = ((RAW / "runs.geojson", keep_run), (RAW / "lifts.geojson", lambda p: p["status"] == "operating"))
    for path, wanted in sources:
        for f in features(path):
            p = f["properties"]
            if not wanted(p) or not p["skiAreas"]:
                continue
            mine = tops(a["properties"]["id"] for a in p["skiAreas"])
            outline = outline_of(f["geometry"]) if p["id"] in area_only else []
            for ln in lines_of(f["geometry"]) + outline:
                for pt in ln:
                    cx, cy = snap_cell(pt[0], pt[1])
                    kx = math.cos(math.radians(pt[1])) * 111_320
                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            for q, qareas in ends.get((cx + dx, cy + dy), ()):
                                theirs = tops(qareas)
                                if theirs & mine or math.hypot((q[0] - pt[0]) * kx, (q[1] - pt[1]) * 111_320) > SNAP_M:
                                    continue
                                for a in mine:
                                    for b in theirs:
                                        touches[tuple(sorted((a, b)))].add(q)
    score = Counter({pair: len(pts) for pair, pts in touches.items()})
    for (a, b), n in shared.items():
        ta, tb = top_of(parent, a), top_of(parent, b)
        if ta != tb and a not in pass_ids and b not in pass_ids:
            score[tuple(sorted((ta, tb)))] += n

    root = {}

    def find(x):
        while root.get(x, x) != x:
            x = root[x]
        return x

    linked_pairs = [pair for pair, n in score.items() if n >= LINK_MIN]
    for a, b in linked_pairs:
        root[find(a)] = find(b)
    sets = defaultdict(list)
    for a in {x for pair in linked_pairs for x in pair}:
        sets[find(a)].append(a)
    return [sorted(m, key=lambda a: -run_count[a]) for m in sets.values()]


def linked_domain(members, by_id, parent, run_info, lift_info):
    """A synthetic domain for a linked set: every run and lift of its members and their sub-areas, counted once."""
    ms = sorted((by_id[m] for m in members), key=lambda a: -a["km"])
    member_ids = set(members)
    bins, grade_bins, runs, lifts = Counter(), defaultdict(Counter), [], []
    lo, hi, lift_top = math.inf, -math.inf, None
    for areas, grade, run_bins, rlo, rhi, run_json in run_info:
        if any(top_of(parent, a) in member_ids for a in areas):
            bins.update(run_bins)
            grade_bins[grade].update(run_bins)
            lo, hi = min(lo, rlo), max(hi, rhi)
            if run_json:
                runs.append(run_json)
    for areas, ltop, lift_json in lift_info:
        if any(top_of(parent, a) in member_ids for a in areas):
            lifts.append(lift_json)
            if ltop is not None:
                lift_top = ltop if lift_top is None else max(lift_top, ltop)
    hist = {z: m / 1000 for z, m in sorted(bins.items())}
    total = sum(hist.values())
    names = list(dict.fromkeys(a["name"] for a in ms if a["name"]))
    name = next((LINKED_NAMES[nm] for nm in names if nm in LINKED_NAMES), None)
    if not name:
        alone = ms[0]["km"] >= LINKED_ALONE * sum(a["km"] for a in ms)
        name = names[0] if alone or len(names) == 1 else " / ".join(names[:3]) + (f" +{len(names) - 3}" if len(names) > 3 else "")
    placed = [a for a in ms if a["lon"] is not None]
    w = [a["km"] or 0.01 for a in placed]
    return {
        # From the member with the most runs, so the id (and shared links to it) survive members joining or leaving.
        "id": "linked-" + hashlib.sha1(members[0].encode()).hexdigest()[:16],
        "name": name,
        "countries": list(dict.fromkeys(c for a in ms for c in a["countries"])),
        "lon": sum(a["lon"] * k for a, k in zip(placed, w)) / sum(w) if placed else None,
        "lat": sum(a["lat"] * k for a, k in zip(placed, w)) / sum(w) if placed else None,
        "region": ms[0]["region"],
        "parent": None,
        "pass_network": False,
        "linked": [a["name"] or "(unnamed)" for a in ms],
        "runs": sum(1 for areas, *_ in run_info if any(top_of(parent, a) in member_ids for a in areas)),
        "km": round(total, 2),
        "osm_km": round(sum(a["osm_km"] for a in ms), 2),
        "min_alt": round(lo),
        "max_alt": round(hi),
        "lift_top": round(lift_top) if lift_top is not None else None,
        "median_alt": round(weighted_median(hist, total)),
        "hist": {str(z): round(km, 3) for z, km in hist.items()},
        "gh": {str(g): {str(z): round(m / 1000, 2) for z, m in sorted(c.items()) if m >= 5} for g, c in sorted(grade_bins.items())},
        "_runs": runs,
        "_lifts": lifts,
    }


def weighted_median(hist, total):
    """Length-weighted median altitude, interpolated within the 100 m band."""
    acc = 0
    for z, km in hist.items():
        if acc + km >= total / 2:
            return z + BIN * (total / 2 - acc) / km
        acc += km
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # area names in the log, on any console
    main()
