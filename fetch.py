"""Download OpenSkiMap GeoJSON once into data/raw/. Pass --force to refresh."""

import http.client
import shutil
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://tiles.openskimap.org/geojson"
FILES = ["runs.geojson", "ski_areas.geojson", "lifts.geojson"]
RAW = Path(__file__).parent / "data" / "raw"
ATTEMPTS = 5  # the server sometimes drops a long download part-way; each retry starts the file again
TIMEOUT = 120  # seconds without data before giving up on an attempt


def download(name, dest):
    tmp = dest.with_suffix(".part")
    for attempt in range(1, ATTEMPTS + 1):
        try:
            req = urllib.request.Request(f"{BASE}/{name}", headers={"User-Agent": "ski-altitude-explorer"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp, open(tmp, "wb") as out:
                shutil.copyfileobj(resp, out, length=1 << 20)
            tmp.replace(dest)
            return
        except (http.client.IncompleteRead, urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if attempt == ATTEMPTS:
                raise
            wait = 15 * attempt
            print(f"  attempt {attempt} failed ({type(e).__name__}); retrying in {wait}s", flush=True)
            time.sleep(wait)


def main():
    force = "--force" in sys.argv
    RAW.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        dest = RAW / name
        if dest.exists() and not force:
            print(f"cached: {dest}")
            continue
        print(f"downloading {name} ...", flush=True)
        download(name, dest)
        print(f"  {dest.stat().st_size / 1e6:.0f} MB", flush=True)


if __name__ == "__main__":
    main()
