"""python -m busyness build: prepare structure files for the busyness engine.

    uv run --group busyness python -m busyness build --all
    uv run --group busyness python -m busyness build --name "Serre-Chevalier" --places cache

Reads data/domains.json and the raw OpenSkiMap files (run fetch.py and build_stats.py first). Writes
data/busy/<domain id>.json and data/busy/manifest.json (domain id -> fingerprint). Domains whose fingerprint is
unchanged are skipped unless --force. Places are cached in data/busy-cache/places-<release>.json.
"""

import argparse
import json
import sys
import time
from pathlib import Path

from . import params as P
from .network import build
from .partition import eligible, load_domains, partition
from .places import CachedSource, OverpassSource, OvertureSource, bbox_of
from .sectors import find_sectors
from .structure import assemble, fingerprint, write
from .villages import find_villages

OUT = P.ROOT / "data" / "busy"
CACHE = P.ROOT / "data" / "busy-cache"


def place_source(kind: str):
    path = CACHE / f"places-{P.OVERTURE_RELEASE}.json"
    if kind == "overture":
        return CachedSource(path, OvertureSource())
    if kind == "cache":
        return CachedSource(path, None)
    if kind == "overpass":
        return CachedSource(CACHE / "places-overpass.json", OverpassSource(), release="overpass")
    return None


def build_all(args) -> int:
    domains = load_domains()
    if args.domain or args.name:
        want = {k: d for k, d in domains.items() if k in (args.domain or []) or d.name in (args.name or [])}
    else:
        want = eligible(domains)
    if not want:
        print("no matching domains", file=sys.stderr)
        return 1
    out = Path(args.out)
    manifest_path = out / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    t = time.time()
    feats = partition(want)
    print(f"partitioned {len(want)} domains in {time.time() - t:.0f} s", flush=True)
    feats = {k: f for k, f in feats.items() if any(x.kind == "lift" for x in f) and any(x.kind == "run" for x in f)}
    source = place_source(args.places)
    boxes = {k: bbox_of((c[0], c[1]) for x in f for c in x.ll) for k, f in feats.items()}
    places = source.places(boxes) if source else {k: None for k in feats}
    built = skipped = small = 0
    for k, f in feats.items():
        fp = fingerprint(f, places[k])
        if not args.force and manifest.get(k) == fp and (out / f"{k}.json").exists():
            skipped += 1
            continue
        net = build(f)
        if len(net.lifts) < P.MIN_LIFTS:
            small += 1
            manifest.pop(k, None)
            (out / f"{k}.json").unlink(missing_ok=True)
            continue
        sectors = find_sectors(net)
        villages = find_villages(net, sectors, places[k])
        src = args.places if places[k] is not None else "lift layout"
        path = write(assemble(want[k], net, sectors, villages, fp, src), out)
        manifest[k] = fp
        built += 1
        print(f"  {want[k].name}: {len(net.z)} junctions, {len(net.links)} links, {len(sectors.lifts)} sectors, "
              f"{len(villages)} villages, {path.stat().st_size // 1024} KB", flush=True)
    pruned = 0
    if not (args.domain or args.name):
        # A full build is the whole published set: drop domains no longer eligible (or no longer existing).
        for k in [k for k in manifest if k not in feats]:
            manifest.pop(k)
            (out / f"{k}.json").unlink(missing_ok=True)
            pruned += 1
    out.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=0, sort_keys=True), encoding="utf-8")
    print(f"built {built}, unchanged {skipped}, too few lifts {small}, dropped {pruned}, in {time.time() - t:.0f} s")
    return 0


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="python -m busyness", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="build structure files")
    b.add_argument("--domain", action="append", help="domain id (repeatable)")
    b.add_argument("--name", action="append", help="domain name (repeatable)")
    b.add_argument("--all", action="store_true", help="every eligible domain (the default without --domain/--name)")
    b.add_argument("--places", choices=["overture", "cache", "overpass", "none"], default="overture")
    b.add_argument("--out", default=str(OUT))
    b.add_argument("--force", action="store_true", help="rebuild even if unchanged")
    args = ap.parse_args(argv)
    return build_all(args)
