"""Can we guess a lift's missing capacity (and speed) better than the median for its type?

    uv run --group busyness python prototypes/lift_capacity.py           # build the table once (a few minutes), then analyse
    uv run --group busyness python prototypes/lift_capacity.py --rebuild
    uv run --group busyness python prototypes/lift_capacity.py --evaluate  # models against today's fill-ins

Step 1 writes data/lift_capacity.csv: one row per operating lift with its recorded capacity, duration, seats, and
candidate predictors (length, vertical, runs starting near its top). Step 2 prints how capacity and speed vary with
them, and the cross-validated error of a few ways of filling a missing capacity, against today's type median
(busyness/params.py CAP_BY_TYPE).
"""

import csv
import math
import sys
import zlib
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import build_stats as bs  # noqa: E402
from busyness import params as P  # noqa: E402
from busyness.lifts import name_hints  # noqa: E402

OUT = ROOT / "data" / "lift_capacity.csv"
TOP_M = P.LIFT_TOP_M  # runs starting this close to a lift's top count as runs from it
CELL = 0.01  # degrees, grid for the run-start lookup
HOLDOUT = 5  # one ski area in this many is held out, with all its lifts
TYPES = ["chair_lift", "gondola", "t-bar", "platter", "drag_lift", "cable_car", "funicular", "rope_tow",
         "magic_carpet"]


def metres(a, b):
    """Equirectangular distance: fine at 150 m."""
    dx = (a[0] - b[0]) * 111320 * math.cos(math.radians(a[1]))
    return math.hypot(dx, (a[1] - b[1]) * 110540)


def run_tops():
    """Grid of the higher end of every operating downhill run line."""
    grid = defaultdict(list)
    for f in bs.features(bs.RAW / "runs.geojson"):
        if not bs.keep_run(f["properties"]):
            continue
        for ln in bs.lines_of(f["geometry"]):
            if len(ln) < 2 or len(ln[0]) < 3 or ln[0][2] is None or ln[-1][2] is None:
                continue
            top = ln[0] if ln[0][2] >= ln[-1][2] else ln[-1]
            grid[(int(top[0] // CELL), int(top[1] // CELL))].append(top)
    return grid


def runs_near(grid, p):
    cx, cy = int(p[0] // CELL), int(p[1] // CELL)
    return sum(metres(p, q) <= TOP_M for i in (-1, 0, 1) for j in (-1, 0, 1) for q in grid.get((cx + i, cy + j), ()))


def build():
    print("indexing run tops...", flush=True)
    grid = run_tops()
    print("reading lifts...", flush=True)
    rows = []
    for f in bs.features(bs.RAW / "lifts.geojson"):
        p = f["properties"]
        if p["status"] != "operating" or f["geometry"]["type"] != "LineString":
            continue
        ln = f["geometry"]["coordinates"]
        if len(ln) < 2 or len(ln[0]) < 3 or ln[0][2] is None or ln[-1][2] is None:
            continue
        lons, lats = [c[0] for c in ln], [c[1] for c in ln]
        length = sum(bs.geod.inv(lons[:-1], lats[:-1], lons[1:], lats[1:])[2])
        top, bottom = (ln[-1], ln[0]) if ln[-1][2] >= ln[0][2] else (ln[0], ln[-1])
        place = p["places"][0] if p["places"] else {}
        rows.append(dict(
            id=bs.short_id(p["id"]), name=p["name"], type=p["liftType"],
            area=p["skiAreas"][0]["properties"]["name"] if p["skiAreas"] else None,
            country=place.get("iso3166_1Alpha2"), alps=bs.in_alps(place.get("iso3166_1Alpha2"), *bottom[:2]),
            length=round(length), vertical=round(top[2] - bottom[2]), top_ele=round(top[2]),
            runs_from_top=runs_near(grid, top),
            capacity=p.get("capacity"), duration=p.get("duration"), occupancy=p.get("occupancy"),
            detachable=p.get("detachable"), bubble=p.get("bubble"), heating=p.get("heating")))
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} lifts to {OUT}")


def num(v):
    return float(v) if v not in ("", None) else math.nan


def load():
    with open(OUT, encoding="utf-8") as fh:
        # Only lifts in a ski area: the busyness model fills no others, and urban, tourist and industrial lifts
        # (London Cable Car, cliff railways, dam service cableways) would skew the tables.
        rows = [r for r in csv.DictReader(fh) if r["area"]]
    for r in rows:
        for k in ("length", "vertical", "top_ele", "runs_from_top", "capacity", "duration", "occupancy"):
            r[k] = num(r[k])
        if not P.CAP_RANGE[0] <= r["capacity"] <= P.CAP_RANGE[1]:
            r["capacity"] = math.nan  # same plausibility filter as the pipeline
        if not P.DURATION_RANGE[0] <= r["duration"] <= P.DURATION_RANGE[1]:
            r["duration"] = math.nan
        if not 1 <= r["occupancy"] <= P.SEATS_MAX.get(r["type"], 2):
            r["occupancy"] = math.nan
        r["speed"] = r["length"] / r["duration"] if r["duration"] == r["duration"] else math.nan
        if not 0.2 <= r["speed"] <= 12:
            r["speed"] = math.nan
        r["test"] = zlib.crc32((r["area"] or r["id"]).encode()) % HOLDOUT == 0
    return rows


def quartile_table(rs, x, y, label):
    """Median y by quartile of x: the quickest look at whether x tells us anything."""
    pts = sorted((r[x], r[y]) for r in rs if r[x] == r[x] and r[y] == r[y])
    if len(pts) < 40:
        return
    q = np.array_split(np.array(pts), 4)
    cells = "  ".join(f"{b[0, 0]:>6.0f}-{b[-1, 0]:<6.0f} {np.median(b[:, 1]):>6.0f}" for b in q)
    print(f"  {label:<22} {cells}   (n={len(pts)})")


def log_or_missing(vals):
    """log(v), and a 0/1 column marking where v is missing (its log column is 0 there)."""
    v = np.array(vals, dtype=float)
    return [np.log(np.where(np.isnan(v), 1, v)), np.isnan(v).astype(float)]


def design(rs, cols):
    """Predictors: log length, vertical, runs from top (log1p), and seats and recorded capacity where known."""
    X = [np.ones(len(rs))]
    if "length" in cols:
        X.append(np.log([max(r["length"], 20) for r in rs]))
    if "vertical" in cols:
        X.append(np.array([max(r["vertical"], 0) for r in rs]) / 1000)
    if "runs" in cols:
        X.append(np.log1p([r["runs_from_top"] for r in rs]))
    if "seats" in cols:
        X += log_or_missing([r["occupancy"] for r in rs])
    if "cap" in cols:
        X += log_or_missing([r["capacity"] for r in rs])
    return np.column_stack(X)


def cv_error(rs, cols, k=5):
    """Median absolute % error of a log-linear fit, k-fold. cols=None means the plain type median."""
    y = np.log([r["capacity"] for r in rs])
    fold = np.arange(len(rs)) % k
    np.random.default_rng(0).shuffle(fold)
    pred = np.empty(len(rs))
    X = design(rs, cols or [])
    for i in range(k):
        tr, te = fold != i, fold == i
        if cols is None:
            pred[te] = np.median(y[tr])
        else:
            beta, *_ = np.linalg.lstsq(X[tr], y[tr], rcond=None)
            pred[te] = X[te] @ beta
    return np.median(np.abs(np.exp(pred - y) - 1)) * 100


def analyse():
    rows = load()
    by_type = defaultdict(list)
    for r in rows:
        by_type[r["type"]].append(r)

    print("\nCoverage (operating lifts)")
    print(f"  {'type':<14}{'n':>7}{'cap':>7}{'dur':>7}{'seats':>7}  median cap  median speed m/s")
    for t in TYPES:
        rs = by_type[t]
        cap = [r["capacity"] for r in rs if r["capacity"] == r["capacity"]]
        spd = [r["speed"] for r in rs if r["speed"] == r["speed"]]
        pct = lambda k: 100 * sum(r[k] == r[k] for r in rs) / len(rs)  # noqa: E731
        print(f"  {t:<14}{len(rs):>7}{pct('capacity'):>6.0f}%{pct('duration'):>6.0f}%{pct('occupancy'):>6.0f}%"
              f"  {np.median(cap) if cap else math.nan:>10.0f}  {np.median(spd) if spd else math.nan:>8.1f}")

    print("\nMedian capacity by quartile of each predictor (lifts with a recorded capacity)")
    for t in ["chair_lift", "gondola", "t-bar", "platter", "drag_lift", "cable_car"]:
        print(f" {t}")
        rs = by_type[t]
        quartile_table(rs, "length", "capacity", "length m")
        quartile_table(rs, "vertical", "capacity", "vertical m")
        quartile_table(rs, "runs_from_top", "capacity", "runs from top")
        quartile_table(rs, "occupancy", "capacity", "seats")
        quartile_table(rs, "length", "speed", "length m -> speed")

    print("\nMedian abs % error filling capacity, 5-fold CV, lifts with a recorded capacity")
    models = {"type median (today)": None, "+length": ["length"], "+length+vertical": ["length", "vertical"],
              "+length+runs": ["length", "runs"], "+length+vertical+runs": ["length", "vertical", "runs"],
              "+all incl. seats": ["length", "vertical", "runs", "seats"]}
    print(f"  {'type':<14}{'n':>6}  " + "".join(f"{m:>24}" for m in models))
    for t in ["chair_lift", "gondola", "t-bar", "platter", "drag_lift", "cable_car"]:
        rs = [r for r in by_type[t] if r["capacity"] == r["capacity"]]
        print(f"  {t:<14}{len(rs):>6}  " + "".join(f"{cv_error(rs, c):>23.0f}%" for c in models.values()))


MODELS = {"capacity": ["length", "vertical", "runs", "seats"], "speed": ["length", "vertical", "seats", "cap"]}
MIN_TRAIN = 30  # fewer training lifts than this and a type keeps today's value


def today(target, t):
    """The pipeline's current fill-in (busyness/params.py)."""
    return P.CAP_BY_TYPE.get(t, 1000) if target == "capacity" else P.LIFT_SPEED.get(t, P.DEFAULT_LIFT_SPEED)


def fit(rs, target):
    """Per type, least squares on log target. Returns {type: coefficients}; types too thin to fit are left out."""
    out = {}
    for t in {r["type"] for r in rs}:
        tr = [r for r in rs if r["type"] == t and r[target] == r[target]]
        if len(tr) >= MIN_TRAIN:
            out[t] = np.linalg.lstsq(design(tr, MODELS[target]), np.log([r[target] for r in tr]), rcond=None)[0]
    return out


def predict(beta, rs, target):
    return np.array([math.exp(design([r], MODELS[target])[0] @ beta[r["type"]]) if r["type"] in beta
                     else today(target, r["type"]) for r in rs])


def errors(pred, actual, target="capacity"):
    """Absolute % errors, relative to the actual value. For speed, the error in the ride time it gives
    (length / speed), which is what's used: |actual speed / predicted speed - 1|."""
    return np.abs((actual / pred if target == "speed" else pred / actual) - 1) * 100


def evaluate():
    rows = load()
    train = [r for r in rows if not r["test"]]
    test = [r for r in rows if r["test"]]
    print(f"\nHold-out: {sum(r['test'] for r in rows)} of {len(rows)} lifts, from 1 in {HOLDOUT} ski areas")
    for target, what in (("capacity", "capacity"), ("speed", "ride time from speed")):
        beta = fit(train, target)
        print(f"\n{target.capitalize()}: abs % error in {what} on held-out lifts (median / 90th percentile), "
              f"and bias (median predicted / actual - 1)")
        print(f"  {'type':<14}{'train':>6}{'test':>6}  {'today':>14}{'train median':>16}{'model':>14}"
              f"{'bias today':>12}{'bias model':>12}   model, seats known / missing")
        groups = [(t, [r for r in test if r["type"] == t]) for t in TYPES] + [("all", [r for r in test if r["type"] in TYPES])]
        for t, ts in groups:
            ts = [r for r in ts if r[target] == r[target]]
            if len(ts) < 10:
                continue
            ntr = sum(r[target] == r[target] for r in train if t == "all" or r["type"] == t)
            actual = np.array([r[target] for r in ts])
            med = {u: np.median([r[target] for r in train if r["type"] == u and r[target] == r[target]] or
                                [today(target, u)]) for u in {r["type"] for r in ts}}
            preds = {"today": np.array([today(target, r["type"]) for r in ts]),
                     "median": np.array([med[r["type"]] for r in ts]), "model": predict(beta, ts, target)}
            cells = "".join(f"{np.median(e):>8.0f}/{np.percentile(e, 90):<5.0f}"
                            for e in (errors(p, actual, target) for p in preds.values()))
            bias = "".join(f"{np.median(p / actual - 1) * 100:>+11.0f}%" for p in (preds["today"], preds["model"]))
            seats = np.array([r["occupancy"] == r["occupancy"] for r in ts])
            em = errors(preds["model"], actual, target)
            split = " / ".join(f"{np.median(em[m]):.0f}% (n={m.sum()})" if m.sum() >= 10 else "-" for m in (seats, ~seats))
            print(f"  {t:<14}{ntr:>6}{len(ts):>6}  {cells:>44}{bias}   {split}")
    multiseat(rows, train, test)
    cable_cars(train, test)
    print("\nFitted on all lifts with the target (what a pipeline would use): log target = coefficients x")
    for target in MODELS:
        print(f"  {target}: [1, " + ", ".join(MODELS[target]) + "]  (seats and cap are log value + missing flag)")
        for t, b in sorted(fit(rows, target).items()):
            print(f"    {t:<14}" + " ".join(f"{v:>7.3f}" for v in b))


def names():
    """How far a chairlift's name tells us its speed class and seats, checked against the recorded values."""
    rs = [r for r in load() if r["type"] == "chair_lift"]
    for r in rs:
        r["hint"], r["name_seats"] = name_hints(r["name"])
    print(f"\nChairlifts: {len(rs)}; hint from name: "
          + ", ".join(f"{h} {sum(r['hint'] == h for r in rs)}" for h in ("fast", "fixed")))
    print("\nMedian speed and capacity by name hint and recorded seats (n in brackets)")
    print(f"  {'seats':<7}" + "".join(f"{h or 'no hint':>30}" for h in ("fast", "fixed", None)))
    for s in (2, 3, 4, 6, 8, None):
        cells = []
        for h in ("fast", "fixed", None):
            g = [r for r in rs if r["hint"] == h and (r["occupancy"] == s if s else r["occupancy"] != r["occupancy"])]
            sp = [r["speed"] for r in g if r["speed"] == r["speed"]]
            cap = [r["capacity"] for r in g if r["capacity"] == r["capacity"]]
            cells.append(f"{np.median(sp) if sp else math.nan:.1f} m/s ({len(sp)}) {np.median(cap) if cap else math.nan:.0f}/h ({len(cap)})")
        print(f"  {str(s or 'none'):<7}" + "".join(f"{c:>30}" for c in cells))
    both = [r for r in rs if r["name_seats"] and r["occupancy"] == r["occupancy"]]
    agree = sum(r["name_seats"] == r["occupancy"] for r in both)
    print(f"\nSeats from name vs recorded: agree {agree} of {len(both)}")
    for r in [r for r in both if r["name_seats"] != r["occupancy"]][:10]:
        print(f"    {r['name']!r}: name {r['name_seats']}, recorded {r['occupancy']:.0f}")
    gap = [r for r in rs if r["occupancy"] != r["occupancy"]]
    print(f"Chairlifts with no recorded seats: {len(gap)}; seats from name: {sum(bool(r['name_seats']) for r in gap)}, "
          f"speed hint from name: {sum(bool(r['hint']) for r in gap)}")
    print("  e.g. " + "; ".join(f"{r['name']} -> {r['name_seats']}" for r in gap if r["name_seats"])[:400])
    fast = [r for r in rs if r["hint"] == "fast"]
    print("\nSample 'fast' names: " + "; ".join(r["name"] for r in fast[::max(len(fast) // 25, 1)]))


MULTISEAT = ["chair_lift", "gondola", "cable_car"]
LONG_M = 1000  # "long" lift, for the seats x length lookup
MIN_GROUP = 5  # a lookup cell with fewer training lifts falls back to the type median


def seat_bin(r):
    """Seats as a lookup key: exact for chairs and gondolas, cabin-size bands for cable cars."""
    s = r["occupancy"]
    if s != s:
        return None
    if r["type"] != "cable_car":
        return int(s)
    return next(b for b in (10, 40, 80, 250) if s <= b)


LOOKUPS = {"seats": lambda r: (r["type"], seat_bin(r)),
           "seats x long": lambda r: (r["type"], seat_bin(r), r["length"] >= LONG_M)}


def lookup(train, target, key):
    """Median target per key over training lifts; cells under MIN_GROUP and missing seats fall back to the type."""
    cells, types = defaultdict(list), defaultdict(list)
    for r in train:
        if r[target] == r[target]:
            cells[key(r)].append(r[target])
            types[r["type"]].append(r[target])
    table = {k: float(np.median(v)) for k, v in cells.items() if len(v) >= MIN_GROUP and None not in k}
    return table, {t: float(np.median(v)) for t, v in types.items()}


CABLE_MIN_SEATS = 11  # "cable cars" with smaller cabins behave like gondolas


def is_cable_car(r):
    return r["type"] == "cable_car" and r["occupancy"] >= CABLE_MIN_SEATS


def cable_formula(r, speed, load_s):
    """A two-cabin cable car: each way, one cabin of seats per trip of length / speed plus loading time."""
    return r["occupancy"] * 3600 / (r["length"] / speed + load_s)


def fit_cable(train):
    """Speed and loading time minimising median % error. Recorded ride times aren't used: some may include
    loading and some not."""
    rs = [r for r in train if is_cable_car(r) and r["capacity"] == r["capacity"]]
    actual = np.array([r["capacity"] for r in rs])
    return min(((v, t) for v in np.arange(3, 12.5, 0.5) for t in range(0, 400, 10)),
               key=lambda p: np.median(errors(np.array([cable_formula(r, *p) for r in rs]), actual)))


def cable_cars(train, test):
    speed, load_s = fit_cable(train)
    ts = [r for r in test if is_cable_car(r) and r["capacity"] == r["capacity"]]
    actual = np.array([r["capacity"] for r in ts])
    print(f"\nCable cars ({CABLE_MIN_SEATS}+ seats): capacity = seats x 3600 / (length / {speed:.1f} m/s + {load_s} s),"
          f" fitted on {sum(is_cable_car(r) and r['capacity'] == r['capacity'] for r in train)} training lifts")
    for label, p in (("today (flat)", [today("capacity", "cable_car")] * len(ts)),
                     ("formula", [cable_formula(r, speed, load_s) for r in ts])):
        e = errors(np.array(p), actual)
        print(f"  {label:<14} median {np.median(e):>3.0f}%  90th percentile {np.percentile(e, 90):>3.0f}%  (n={len(ts)})")


def is_gondola(r):
    return r["type"] == "gondola" or (r["type"] == "cable_car" and r["occupancy"] <= 10)


def cabin_group(r):
    s = r["occupancy"]
    return "no seats" if s != s else "2-6" if s <= 6 else "8-10" if s <= 10 else "12+"


GONDOLA_KEYS = {
    "seats": lambda r: (seat_bin(r),),
    "seats x long": lambda r: (seat_bin(r), r["length"] >= LONG_M),
    "seats x 3 bands": lambda r: (seat_bin(r), sum(r["length"] >= b for b in (700, 1500))),
}


def gondolas(repeats=10, k=5):
    """Gondolas split at random by lift, not by ski area: an old resort's gondolas no longer land in the test
    together. Repeated random k-fold; prints the median of each repeat's median error, with its range."""
    g = [dict(r, type="gondola") for r in load() if is_gondola(r)]
    flat = {"capacity": P.CAP_BY_TYPE["gondola"], "speed": P.LIFT_SPEED["gondola"]}
    for target in ("capacity", "speed"):
        rs = [r for r in g if r[target] == r[target]]
        groups = {grp: [i for i, r in enumerate(rs) if cabin_group(r) == grp] for grp in ("2-6", "8-10", "12+", "no seats")}
        res = defaultdict(list)  # (method, group) -> median error of each repeat
        for rep in range(repeats + 1):  # repeat 0 is the split by ski area, for comparison
            fold = (np.array([zlib.crc32((r["area"] or r["id"]).encode()) % k for r in rs]) if rep == 0
                    else np.random.default_rng(rep).permutation(len(rs)) % k)
            pred = {m: np.empty(len(rs)) for m in ["flat", *GONDOLA_KEYS]}
            for f in range(k):
                tr = [r for r, x in zip(rs, fold) if x != f]
                te = np.flatnonzero(fold == f)
                pred["flat"][te] = flat[target]
                for m, key in GONDOLA_KEYS.items():
                    tab, by_type = lookup(tr, target, lambda r: ("gondola", *key(r)))
                    pred[m][te] = [tab.get(("gondola", *key(rs[i])), by_type["gondola"]) for i in te]
            actual = np.array([r[target] for r in rs])
            for m, p in pred.items():
                e = errors(p, actual, target)
                for grp, idx in groups.items():
                    res[(m, grp, rep == 0)].append(np.median(e[idx]) if len(idx) else math.nan)
        print(f"\nGondolas, {target if target == 'capacity' else 'ride time'}: median abs % error, random {k}-fold by "
              f"lift x {repeats} (range across repeats); [by ski area]")
        print(f"  {'cabin':<10}{'n':>5}" + "".join(f"{m:>24}" for m in pred))
        for grp, idx in groups.items():
            cells = "".join(f"{np.median(res[(m, grp, False)]):>6.0f}% ({min(res[(m, grp, False)]):.0f}-"
                            f"{max(res[(m, grp, False)]):.0f}) [{res[(m, grp, True)][0]:.0f}]".rjust(24) for m in pred)
            print(f"  {grp:<10}{len(idx):>5}{cells}")


def multiseat(rows, train, test):
    print("\nMulti-seat lifts: lookup tables vs regression vs today, median abs % error on held-out lifts")
    print(f"  {'':<22}{'test':>6}{'today':>8}{'model':>8}" + "".join(f"{k:>14}" for k in LOOKUPS)
          + "   lookup 'seats x long', seats known / missing")
    for target in ("capacity", "speed"):
        beta = fit(train, target)
        tabs = {k: lookup(train, target, f) for k, f in LOOKUPS.items()}
        for t in MULTISEAT:
            ts = [r for r in test if r["type"] == t and r[target] == r[target]]
            actual = np.array([r[target] for r in ts])
            cols = [np.array([today(target, t)] * len(ts)), predict(beta, ts, target)]
            for k, (tab, by_type) in tabs.items():
                cols.append(np.array([tab.get(LOOKUPS[k](r), by_type[t]) for r in ts]))
            errs = [errors(p, actual, target) for p in cols]
            seats = np.array([r["occupancy"] == r["occupancy"] for r in ts])
            split = " / ".join(f"{np.median(errs[-1][m]):.0f}% (n={m.sum()})" if m.sum() >= 5 else "-"
                               for m in (seats, ~seats))
            print(f"  {target + ' ' + t:<22}{len(ts):>6}" + "".join(f"{np.median(e):>7.0f}%" for e in errs[:2])
                  + "".join(f"{np.median(e):>13.0f}%" for e in errs[2:]) + f"   {split}")
    print(f"\n  The 'seats x long' lookup, fitted on all lifts (long = {LONG_M} m or more; n in brackets)")
    for target in ("capacity", "speed"):
        tab, by_type = lookup(rows, target, LOOKUPS["seats x long"])
        n = defaultdict(int)
        for r in rows:
            if r[target] == r[target]:
                n[LOOKUPS["seats x long"](r)] += 1
        print(f"  {target}")
        for t in MULTISEAT:
            cells = "  ".join(f"{s}{'L' if lg else 'S'} {v:.{0 if target == 'capacity' else 1}f} ({n[(t, s, lg)]})"
                              for (tt, s, lg), v in sorted(tab.items()) if tt == t)
            print(f"    {t:<12} no seats {by_type[t]:.1f} | {cells}")


CHARTS = ROOT / "data" / "lift_capacity.html"
CSS = """
.viz-root{color-scheme:light;--surface-1:#fcfcfb;--text-primary:#0b0b0b;--text-secondary:#52514e;--grid:#e4e3df;
 --s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--s4:#eda100;background:var(--surface-1);color:var(--text-primary);
 font:14px system-ui,sans-serif;padding:16px 24px;max-width:1400px}
@media (prefers-color-scheme:dark){.viz-root{color-scheme:dark;--surface-1:#1a1a19;--text-primary:#f0efec;
 --text-secondary:#c3c2b7;--grid:#33332f;--s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#c98500}}
body{margin:0;background:var(--surface-1)} h2{font-size:17px;margin:28px 0 4px} p{color:var(--text-secondary);margin:0 0 8px}
.row{display:flex;flex-wrap:wrap;gap:16px} svg text{fill:var(--text-secondary);font-size:11px}
svg .t{fill:var(--text-primary);font-size:13px;font-weight:600} .key{display:inline-flex;align-items:center;gap:6px;margin-right:14px}
.key i{width:12px;height:12px;border-radius:3px;display:inline-block}
"""


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def key(items):
    return "<div>" + "".join(f'<span class="key"><i style="background:var({c})"></i>{t}</span>' for t, c in items) + "</div>"


def coverage_chart(rows):
    """Per type: share with capacity and seats, capacity only, seats only, neither."""
    cats = [("both", "--s1"), ("capacity only", "--s2"), ("seats only", "--s3"), ("neither", "--s4")]
    W, L, bh, gap = 760, 110, 22, 8
    out = []
    for i, t in enumerate(TYPES):
        rs = [r for r in rows if r["type"] == t]
        c = [sum((r["capacity"] == r["capacity"], r["occupancy"] == r["occupancy"]) == k for r in rs)
             for k in ((True, True), (True, False), (False, True), (False, False))]
        y, x = 10 + i * (bh + gap), L
        out.append(f'<text x="{L - 8}" y="{y + 15}" text-anchor="end">{t} ({len(rs)})</text>')
        for (name, col), v in zip(cats, c):
            w = (W - L - 20) * v / len(rs)
            if w > 0:
                out.append(f'<rect x="{x:.1f}" y="{y}" width="{max(w - 2, 0.5):.1f}" height="{bh}" rx="3" '
                           f'fill="var({col})"><title>{t}: {name} {v} ({100 * v / len(rs):.0f}%)</title></rect>')
                if w > 34:
                    out.append(f'<text x="{x + 5:.1f}" y="{y + 15}" style="fill:#fff">{100 * v / len(rs):.0f}%</text>')
            x += w
    h = 10 + len(TYPES) * (bh + gap)
    return key([(n, c) for n, c in cats]) + f'<svg width="{W}" height="{h}">{"".join(out)}</svg>'


def scatter(rs, x, y, title, xlab, ylab, logx=False, ymax=None, xcat=False, xmax=None, hl=None, diag=False):
    """Points (series 1, or series 3 where hl(r)) with the median of y across ten x-bins (series 2).
    diag: a predicted (x) vs actual (y) plot instead: square axes from 0 and a y = x line, no medians."""
    W, H, ml, mr, mt, mb = 440, 300, 52, 12, 26, 40
    pts = [r for r in rs if r[x] == r[x] and r[y] == r[y] and (not logx or r[x] > 0)]
    if ymax:
        pts = [r for r in pts if r[y] <= ymax]
    if xmax:
        pts = [r for r in pts if r[x] <= xmax]
    if len(pts) < 20:
        return ""
    if hl:
        pts.sort(key=hl)  # highlighted points drawn last, on top
    fx =(lambda v: math.log10(v)) if logx else (lambda v: v)
    xs = [fx(r[x]) for r in pts]
    x0, x1 = (min(xs), max(xs)) if not xcat else (min(xs) - 0.5, max(xs) + 0.5)
    y1 = ymax or max(r[y] for r in pts)
    if diag:
        x0, x1 = 0, math.ceil(max(y1, x1) / 500) * 500
        y1 = x1
    sx = lambda v: ml + (fx(v) - x0) / (x1 - x0 or 1) * (W - ml - mr)  # noqa: E731
    sy = lambda v: H - mb - v / y1 * (H - mt - mb)  # noqa: E731
    rng = np.random.default_rng(1)
    g = [f'<text class="t" x="{ml}" y="16">{esc(title)} (n={len(pts)})</text>']
    for v in np.linspace(0, y1, 5):
        g.append(f'<line x1="{ml}" x2="{W - mr}" y1="{sy(v):.1f}" y2="{sy(v):.1f}" stroke="var(--grid)"/>'
                 f'<text x="{ml - 6}" y="{sy(v) + 4:.1f}" text-anchor="end">{v:.0f}</text>')
    ticks = sorted({r[x] for r in pts}) if xcat else (
        [v for v in (30, 100, 300, 1000, 3000, 10000) if x0 <= math.log10(v) <= x1] if logx
        else np.linspace(x0, x1, 5) if diag else np.linspace(min(r[x] for r in pts), max(r[x] for r in pts), 5))
    for v in ticks:
        g.append(f'<text x="{sx(v):.1f}" y="{H - mb + 16}" text-anchor="middle">{v:.0f}</text>')
    g.append(f'<text x="{(W + ml) / 2}" y="{H - 6}" text-anchor="middle">{esc(xlab)}</text>'
             f'<text transform="translate(12 {(H + mt - mb) / 2}) rotate(-90)" text-anchor="middle">{esc(ylab)}</text>')
    for r in pts:
        jx = rng.uniform(-0.25, 0.25) * (W - ml - mr) / (x1 - x0) if xcat else 0
        g.append(f'<circle cx="{sx(r[x]) + jx:.1f}" cy="{sy(r[y]):.1f}" r="2.5" fill="var({'--s3' if hl and hl(r) else '--s1'})" fill-opacity=".45">'
                 f'<title>{esc(r["name"] or "(unnamed)")}, {esc(r["area"] or "")}\n{xlab}: {r[x]:.0f}, '
                 f'{ylab}: {r[y]:.0f}</title></circle>')
    if diag:
        g.append(f'<line x1="{sx(0):.1f}" y1="{sy(0):.1f}" x2="{sx(x1):.1f}" y2="{sy(x1):.1f}" stroke="var(--s2)" '
                 f'stroke-width="2"/>')
        return f'<svg width="{W}" height="{H}">{"".join(g)}</svg>'
    if xcat:
        groups = defaultdict(list)
        for r in pts:
            groups[r[x]].append(r[y])
        med = [(k, float(np.median(v)), len(v)) for k, v in sorted(groups.items()) if len(v) >= 5]
    else:
        srt = sorted(pts, key=lambda r: r[x])
        med = [(float(np.median([r[x] for r in b])), float(np.median([r[y] for r in b])), len(b))
               for b in np.array_split(np.array(srt, dtype=object), 10)]
    path = " ".join(f"{'M' if i == 0 else 'L'}{sx(a):.1f},{sy(b):.1f}" for i, (a, b, _) in enumerate(med))
    g.append(f'<path d="{path}" fill="none" stroke="var(--surface-1)" stroke-width="5"/>'
             f'<path d="{path}" fill="none" stroke="var(--s2)" stroke-width="2"/>')
    for a, b, n in med:
        g.append(f'<circle cx="{sx(a):.1f}" cy="{sy(b):.1f}" r="4" fill="var(--s2)" stroke="var(--surface-1)" '
                 f'stroke-width="2"><title>median {ylab} {b:.0f} at {xlab} {a:.0f} (n={n})</title></circle>')
    return f'<svg width="{W}" height="{H}">{"".join(g)}</svg>'


def page(body):
    return (f'<!DOCTYPE html><html><head><meta charset="utf-8"><title>Lift capacity</title><style>{CSS}</style>'
            f'</head><body><div class="viz-root">{body}</div></body></html>')


def figures():
    """One page per figure for the decision record (docs/decisions/013), to screenshot into PNGs."""
    rows = load()
    chairs = [r for r in rows if r["type"] == "chair_lift"]
    fast = lambda r: name_hints(r["name"])[0] == "fast"  # noqa: E731
    figs = {
        "coverage": coverage_chart(rows),
        "chair-capacity-by-seats": key([("one chairlift", "--s1"), ("median", "--s2")])
        + scatter(chairs, "occupancy", "capacity", "Chairlift capacity by seats", "seats", "capacity /h", ymax=6000, xcat=True),
        "chair-speed-by-length": key([("one chairlift", "--s1"), ("name says fast (express, TSD, 高速...)", "--s3"),
                                      ("median", "--s2")])
        + scatter(chairs, "length", "speed", "Chairlift speed by length", "length m", "speed m/s", logx=True, ymax=8, hl=fast),
    }
    speed, load_s = fit_cable([r for r in rows if not r["test"]])
    cable = [r for r in rows if is_cable_car(r)]
    for r in cable:
        r["formula"] = cable_formula(r, speed, load_s)
    figs["cable-car-formula"] = key([("training lift", "--s1"), ("held-out lift", "--s3"), ("formula = actual", "--s2")]) \
        + scatter(cable, "formula", "capacity", f"Cable cars: seats x 3600 / (length / {speed:.1f} m/s + {load_s} s)",
                  "formula capacity /h", "recorded capacity /h", hl=lambda r: r["test"], diag=True)
    for name, body in figs.items():
        (ROOT / "data" / f"fig-{name}.html").write_text(page(body), encoding="utf-8")
    print("figures: data/fig-*.html")


def charts():
    rows = load()
    by_type = defaultdict(list)
    for r in rows:
        by_type[r["type"]].append(r)
    pk = key([("one lift (hover for name)", "--s1"), ("median", "--s2")])
    secs = [("Which lifts record capacity and seats", "Share of operating lifts per type. Seats without capacity is "
             "the gap a seats-based fill would cover.", coverage_chart(rows))]
    secs.append(("Capacity by seats", "Median per seat count with at least 5 lifts.", pk + '<div class="row">' + "".join(
        scatter(by_type[t], "occupancy", "capacity", t, "seats", "capacity /h", ymax=6000, xcat=True, xmax=16)
        for t in ("chair_lift", "gondola")) + "</div>"))
    secs.append(("Capacity by length", "Median across ten equal-count length bins.", pk + '<div class="row">' + "".join(
        scatter(by_type[t], "length", "capacity", t, "length m", "capacity /h", logx=True, ymax=6000)
        for t in ("chair_lift", "gondola", "t-bar", "platter", "drag_lift", "cable_car")) + "</div>"))
    secs.append(("Capacity by runs starting near the top", f"Runs whose top is within {TOP_M} m of the lift's top.",
                 pk + '<div class="row">' + "".join(
                     scatter(by_type[t], "runs_from_top", "capacity", t, "runs from top", "capacity /h", ymax=6000,
                             xcat=True) for t in ("chair_lift", "gondola", "platter")) + "</div>"))
    secs.append(("Speed by length", "Length ÷ recorded ride time. Missing ride times use a flat speed per type today.",
                 pk + '<div class="row">' + "".join(
                     scatter(by_type[t], "length", "speed", t, "length m", "speed m/s", logx=True, ymax=12)
                     for t in ("chair_lift", "gondola", "t-bar", "platter")) + "</div>"))
    body = "".join(f"<h2>{h}</h2><p>{p}</p>{c}" for h, p, c in secs)
    CHARTS.write_text(f'<!DOCTYPE html><html><head><meta charset="utf-8"><title>Lift capacity</title>'
                      f'<style>{CSS}</style></head><body><div class="viz-root"><h1>Lift capacity, seats, length and '
                      f'speed</h1>{body}</div></body></html>', encoding="utf-8")
    print(f"\ncharts: {CHARTS}")


def params():
    """The lift-estimate tables for busyness/params.py, fitted on every lift in a ski area, as the pipeline reads
    them: seats recorded or from the name, fast from the name. Cells with fewer than MIN_GROUP lifts are left out."""
    rows = load()
    for r in rows:
        r["fast"] = name_hints(r["name"])[0] == "fast"
        if r["occupancy"] != r["occupancy"]:
            n = name_hints(r["name"])[1]
            if n and n <= P.SEATS_MAX.get(r["type"], 2):
                r["occupancy"] = float(n)
    chairs = [r for r in rows if r["type"] == "chair_lift" and r["occupancy"] == r["occupancy"]]
    gondolas = [r for r in rows if is_gondola(r) and r["occupancy"] == r["occupancy"]]

    def table(rs, target, key, fmt):
        cells = defaultdict(list)
        for r in rs:
            if r[target] == r[target]:
                cells[key(r)].append(r[target])
        return "{" + ", ".join(f"{k!r}: {fmt(np.median(v))}" for k, v in sorted(cells.items()) if len(v) >= MIN_GROUP) + "}"

    speed, load_s = fit_cable(rows)
    print(f"CHAIR_CAP = {table(chairs, 'capacity', lambda r: (int(r['occupancy']), r['fast']), lambda v: int(round(v, -1)))}"
          "  # (seats, fast name): an hour")
    print(f"CHAIR_SPEED = {table(chairs, 'speed', lambda r: (int(r['occupancy']), r['length'] >= LONG_M), lambda v: round(v, 1))}"
          "  # (seats, LONG_M or longer): m/s")
    print(f"GONDOLA_CAP = {table(gondolas, 'capacity', lambda r: int(r['occupancy']), lambda v: int(round(v, -1)))}"
          "  # seats: an hour")
    print(f"CABLE_SPEED = {speed:.1f}  # m/s, for capacity\nCABLE_LOAD_S = {load_s}  # loading at each end")


if __name__ == "__main__":
    if "--rebuild" in sys.argv or not OUT.exists():
        build()
    if "--params" in sys.argv:
        params()
    elif "--gondolas" in sys.argv:
        gondolas()
    elif "--figures" in sys.argv:
        figures()
    elif "--names" in sys.argv:
        names()
    elif "--evaluate" in sys.argv:
        evaluate()
    else:
        analyse()
        charts()
