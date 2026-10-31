"""Shared fixtures: small hand-made networks as structure files, with the pipeline's exact exchange shares, used by
both test suites (busyness-validation: the two halves agree). Regenerate with:

    uv run --group busyness python -m tests.busyness.fixtures

Add --domains to also copy the four test domains' structure files from data/busy/ (build them first with
python -m busyness build --name ...); the engine checks decision 011's observations on them.
"""

import json
import sys

from busyness.network import build
from busyness.params import ROOT
from busyness.partition import Domain
from busyness.sectors import exchange, find_sectors
from busyness.structure import assemble, fingerprint
from busyness.villages import find_villages

from .helpers import lift, run

FIXTURES = ROOT / "tests" / "fixtures" / "busyness"


def shared_top():
    """Two lifts arriving at the same top station, one run down to both bottoms."""
    return [lift("La", (0, -1000, 1500), (0, 0, 2200)), lift("Lb", (300, -1000, 1500), (20, 0, 2200)),
            run("R1", (0, 0, 2200), (0, -1000, 1500)), run("R2", (20, 0, 2200), (300, -1000, 1500))]


def fork_and_loop():
    """A lift whose top forks into a red and a black crossed by a blue; a walk; a gondola that can be ridden down."""
    return [lift("G", (0, -1500, 1400), (0, 0, 2400), type="gondola", cap=2400),
            run("Red", (0, 0, 2400), (-700, -1500, 1400), grade=2),
            run("Black", (0, 0, 2400), (700, -1500, 1400), grade=3),
            run("Cross", (-300, -600, 2050), (900, -700, 1950), grade=1),
            lift("C", (700, -1500, 1400), (40, 80, 2380), cap=1800),
            run("Home", (-700, -1500, 1400), (-50, -1520, 1395), grade=0)]


def two_valleys():
    feats = []
    for v, x in (("1", 0), ("2", 10_000)):
        feats += [lift(f"L{v}a", (x, -1000, 1500), (x, 0, 2200)), run(f"R{v}a", (x, 0, 2200), (x + 800, -1000, 1500)),
                  lift(f"L{v}b", (x + 800, -1000, 1500), (x + 800, 0, 2200)),
                  run(f"R{v}b", (x + 800, 0, 2200), (x, -1000, 1500))]
    return feats


def linked_valleys():
    """Two equal valleys joined by link runs from each one's top to the other's bottom, so people commute."""
    return two_valleys() + [run("Link12", (800, 0, 2200), (5_000, -500, 1850), (10_000, -1000, 1500), grade=1),
                            run("Link21", (10_800, 0, 2200), (5_800, -500, 1850), (0, -1000, 1500), grade=1)]


CASES = {"shared_top": shared_top, "fork_and_loop": fork_and_loop, "two_valleys": two_valleys,
         "linked_valleys": linked_valleys}


def make(name: str) -> dict:
    feats = CASES[name]()
    fp = fingerprint(feats, None)
    net = build(feats)
    sectors = find_sectors(net)
    doc = assemble(Domain(name, name, 40, 5, [name]), net, sectors, find_villages(net, sectors, None), fp, "none")
    doc["built"] = "fixture"
    doc["expected"] = {"exchange": {str(fi): {str(fj): round(s, 6) for fj, s in got.items()}
                                    for fi, got in exchange(net).items()}}
    return doc


TEST_DOMAINS = {"Les Trois Vallées": "les-trois-vallees", "Tignes - Val d'Isère": "tignes-val-d-isere",
                "Serre-Chevalier": "serre-chevalier", "GrandValira / Canaro": "grandvalira"}


def copy_test_domains() -> None:
    """Copy the four test domains' structure files (built with python -m busyness build) into the fixtures, for the
    engine's observation checks (decision 011)."""
    out = FIXTURES / "domains"
    out.mkdir(parents=True, exist_ok=True)
    for path in sorted((ROOT / "data" / "busy").glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        slug = TEST_DOMAINS.get(doc.get("domain", {}).get("name"))
        if slug:
            (out / f"{slug}.json").write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")),
                                              encoding="utf-8")
            print(f"copied {doc['domain']['name']} to domains/{slug}.json")


def main() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    for name in CASES:
        (FIXTURES / f"{name}.json").write_text(json.dumps(make(name), indent=1), encoding="utf-8")
        print(f"wrote {name}.json")
    if "--domains" in sys.argv:
        copy_test_domains()


if __name__ == "__main__":
    sys.exit(main())
