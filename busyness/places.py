"""Named places and building counts around each domain, for finding villages (docs/decisions/008).

A PlaceSource takes each domain's bounding box and returns its places (towns, villages, hamlets, neighbourhoods),
each with the number of buildings within PLACE_BUILDINGS_M of its point, or None for a domain it can't serve.
- OvertureSource: Overture Maps via DuckDB, at the pinned release (the production source).
- CachedSource: wraps another source and keeps its answers in a JSON file per release.
- OverpassSource: OpenStreetMap's Overpass service; slow and rate-limited, for local use only.
"""

import json
import math
import time
import urllib.parse
import urllib.request
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

from . import params as P

BBox = tuple[float, float, float, float]  # lon0, lat0, lon1, lat1
MARGIN = 0.02  # degrees added around a domain's runs and lifts


@dataclass
class Place:
    name: str
    kind: str  # town | village | hamlet | suburb
    lon: float
    lat: float
    buildings: int


class PlaceSource(Protocol):
    def places(self, boxes: dict[str, BBox]) -> dict[str, list[Place] | None]: ...


def bbox_of(points: Iterable[tuple[float, float]]) -> BBox:
    pts = list(points)
    return (round(min(p[0] for p in pts) - MARGIN, 4), round(min(p[1] for p in pts) - MARGIN, 4),
            round(max(p[0] for p in pts) + MARGIN, 4), round(max(p[1] for p in pts) + MARGIN, 4))


def _metres(lon1, lat1, lon2, lat2) -> float:
    kx = math.cos(math.radians((lat1 + lat2) / 2)) * 111_320
    return math.hypot((lon1 - lon2) * kx, (lat1 - lat2) * 111_320)


def count_buildings(places: list[tuple[str, str, float, float]], centres: list[tuple[float, float]]) -> list[Place]:
    """Each place with the number of building centres within PLACE_BUILDINGS_M of its point (grid-bucketed)."""
    cell = P.PLACE_BUILDINGS_M / 111_320  # degrees of latitude; longitude cells are narrower in metres, so safe
    grid: dict[tuple[int, int], list[tuple[float, float]]] = {}
    for x, y in centres:
        grid.setdefault((int(x // cell), int(y // cell)), []).append((x, y))
    out = []
    for name, kind, lon, lat in places:
        cx, cy = int(lon // cell), int(lat // cell)
        span = math.ceil(1 / math.cos(math.radians(lat)))  # longitude cells spanning PLACE_BUILDINGS_M
        n = sum(1 for dx in range(-span - 1, span + 2) for dy in (-1, 0, 1) for x, y in grid.get((cx + dx, cy + dy), ())
                if _metres(x, y, lon, lat) <= P.PLACE_BUILDINGS_M)
        out.append(Place(name, kind, lon, lat, n))
    return out


class OvertureSource:
    """Overture Maps divisions (place points) and buildings, read from its public S3 bucket with DuckDB."""
    KINDS = {"city": "town", "town": "town", "village": "village", "hamlet": "hamlet"}

    def __init__(self, release: str = P.OVERTURE_RELEASE):
        import duckdb  # only the pipeline needs it

        self.base = f"s3://overturemaps-us-west-2/release/{release}"
        self.con = duckdb.connect()
        for sql in ("INSTALL spatial", "LOAD spatial", "INSTALL httpfs", "LOAD httpfs", "SET s3_region='us-west-2'",
                    "SET enable_object_cache=true"):  # keep parquet metadata between queries
            self.con.execute(sql)

    def _one(self, box: BBox) -> list[Place]:
        x0, y0, x1, y1 = box
        rows = self.con.execute(f"""
            SELECT names.primary, subtype, class, bbox.xmin, bbox.ymin
            FROM read_parquet('{self.base}/theme=divisions/type=division/*', hive_partitioning=1)
            WHERE bbox.xmin BETWEEN {x0} AND {x1} AND bbox.ymin BETWEEN {y0} AND {y1}
              AND subtype IN ('locality', 'neighborhood') AND names.primary IS NOT NULL""").fetchall()
        named = [(name, "suburb" if sub == "neighborhood" else self.KINDS.get(cls, "hamlet"), lon, lat)
                 for name, sub, cls, lon, lat in rows]
        centres = self.con.execute(f"""
            SELECT (bbox.xmin + bbox.xmax) / 2, (bbox.ymin + bbox.ymax) / 2
            FROM read_parquet('{self.base}/theme=buildings/type=building/*', hive_partitioning=1)
            WHERE bbox.xmin < {x1} AND bbox.xmax > {x0} AND bbox.ymin < {y1} AND bbox.ymax > {y0}""").fetchall()
        return count_buildings(named, centres)

    def places(self, boxes: dict[str, BBox]) -> dict[str, list[Place] | None]:
        out: dict[str, list[Place] | None] = {}
        for k, box in boxes.items():
            try:
                out[k] = self._one(box)
            except Exception as e:  # noqa: BLE001 - any failure means "no places for this domain"
                print(f"  Overture: no places for {k}: {e}", flush=True)
                out[k] = None
        return out


class CachedSource:
    """Keeps another source's answers in a JSON file, keyed by release and each domain's box. Domains whose box is
    unchanged are answered from the file; the rest are fetched from the inner source in one batch."""

    def __init__(self, path: Path, inner: PlaceSource | None, release: str = P.OVERTURE_RELEASE):
        self.path, self.inner, self.release = path, inner, release
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        self.domains = data.get("domains", {}) if data.get("release") == release else {}

    def places(self, boxes: dict[str, BBox]) -> dict[str, list[Place] | None]:
        out: dict[str, list[Place] | None] = {}
        todo = {}
        for k, box in boxes.items():
            hit = self.domains.get(k)
            if hit and tuple(hit["bbox"]) == tuple(box):
                out[k] = [Place(**p) for p in hit["places"]]
            else:
                todo[k] = box
        if todo and self.inner:
            for k, got in self.inner.places(todo).items():
                out[k] = got
                if got is not None:
                    self.domains[k] = {"bbox": list(todo[k]), "places": [asdict(p) for p in got]}
            self.save()
        return {k: out.get(k) for k in boxes}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"release": self.release, "domains": self.domains}, ensure_ascii=False,
                                        separators=(",", ":")), encoding="utf-8")


class OverpassSource:
    """OpenStreetMap places and building counts from the public Overpass servers. Slow and rate-limited: for local
    experiments, not the weekly pipeline."""
    SERVERS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
    KINDS = "town|village|hamlet|suburb"

    def _query(self, query: str):
        for attempt in range(6):
            req = urllib.request.Request(self.SERVERS[attempt % len(self.SERVERS)],
                                         data=urllib.parse.urlencode({"data": query}).encode(),
                                         headers={"User-Agent": "ski-altitude-explorer busyness"})
            try:
                with urllib.request.urlopen(req, timeout=180) as r:
                    return json.load(r)["elements"]
            except (OSError, ValueError) as e:
                print(f"  Overpass: {e}, retrying", flush=True)
                time.sleep(5 * (attempt + 1))
        return None

    def places(self, boxes: dict[str, BBox]) -> dict[str, list[Place] | None]:
        out: dict[str, list[Place] | None] = {}
        for k, (x0, y0, x1, y1) in boxes.items():
            box = f"{y0},{x0},{y1},{x1}"
            els = self._query(f'[out:json][timeout:60];node["place"~"^({self.KINDS})$"]["name"]({box});out;')
            if els is None:
                out[k] = None
                continue
            found = []
            for start in range(0, len(els), 15):
                chunk = els[start:start + 15]
                around = P.PLACE_BUILDINGS_M
                counts = self._query("[out:json][timeout:170];" + "".join(
                    f'way["building"](around:{around},{el["lat"]},{el["lon"]});out count;' for el in chunk))
                if counts is None:
                    break
                found += [Place(el["tags"]["name"], el["tags"]["place"], el["lon"], el["lat"], int(c["tags"]["total"]))
                          for el, c in zip(chunk, counts, strict=True)]
            else:
                out[k] = found
                continue
            out[k] = None
        return out
