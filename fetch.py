"""Download OpenSkiMap GeoJSON once into data/raw/. Pass --force to refresh."""

import shutil
import sys
import urllib.request
from pathlib import Path

BASE = "https://tiles.openskimap.org/geojson"
FILES = ["runs.geojson", "ski_areas.geojson", "lifts.geojson"]
RAW = Path(__file__).parent / "data" / "raw"


def main():
    force = "--force" in sys.argv
    RAW.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        dest = RAW / name
        if dest.exists() and not force:
            print(f"cached: {dest}")
            continue
        tmp = dest.with_suffix(".part")
        print(f"downloading {name} ...")
        req = urllib.request.Request(f"{BASE}/{name}", headers={"User-Agent": "ski-altitude-explorer"})
        with urllib.request.urlopen(req) as resp, open(tmp, "wb") as out:
            shutil.copyfileobj(resp, out, length=1 << 20)
        tmp.replace(dest)
        print(f"  {dest.stat().st_size / 1e6:.0f} MB")


if __name__ == "__main__":
    main()
