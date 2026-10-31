"""Assemble, check and write a domain's structure file: everything the engine needs, nothing it computes
(busyness-pipeline). Junctions are numbered highest first; links refer to them by number."""

import hashlib
import json
from dataclasses import asdict
from datetime import date
from pathlib import Path

from . import params as P
from .network import Network
from .partition import Domain, Feature
from .places import Place
from .sectors import Sectors
from .villages import Village


class StructureError(ValueError):
    """The structure is impossible (a bug, not a result): nothing is written."""


def fingerprint(feats: list[Feature], places: list[Place] | None) -> str:
    """Changes whenever anything that shapes the structure does: the features, the places, the structure code's
    version, the places release, or the shared behaviour constants (sectors use the pull rules)."""
    h = hashlib.sha256()
    h.update(f"{P.MODEL_VERSION}|{P.OVERTURE_RELEASE}|".encode())
    h.update(P.ENGINE_PARAMS.read_bytes())
    for f in feats:
        h.update(json.dumps([f.kind, f.id, f.name, f.grade, f.type, f.cap, f.cap_known, f.dur,
                             [[round(c, 6) for c in pt] for pt in f.ll]], ensure_ascii=False).encode())
    h.update(json.dumps([asdict(p) for p in places] if places is not None else None, ensure_ascii=False).encode())
    return h.hexdigest()[:16]


def assemble(domain: Domain, net: Network, sectors: Sectors, villages: list[Village], fp: str,
             places_source: str) -> dict:
    for s in sectors.commute_share:
        if not 0 <= s <= 1:
            raise StructureError(f"{domain.id}: commuting share {s:.2f} outside 0-100%")
    idx = {n: i for i, n in enumerate(net.order)}
    links = []
    for e in net.links:
        f = net.feats[e.fi] if e.fi is not None else None
        link = {"a": idx[e.a], "b": idx[e.b], "k": e.kind, "len": round(e.len, 1), "rt": round(e.route_t, 2)}
        if e.kind == "run":
            # Gradient unrounded: pull steps at 6% and 10% (a run at 5.9997% rounded up would pull twice as hard).
            link |= {"g": f.grade, "grad": f.grad, "run": f.id}
            if e.committed is not None:
                link["cm"] = round(e.committed, 1)
        if e.kind in ("lift", "download"):
            link |= {"cap": f.cap, "lift": e.fi}
        if f is not None and f.nursery:
            link["nur"] = 1
        links.append(link)
    lift_fis = sorted({e.fi for e in net.all_lifts})
    return {
        "format": 1,
        "domain": {"id": domain.id, "name": domain.name},
        "model_version": P.MODEL_VERSION,
        "fingerprint": fp,
        "places": {"source": places_source, "release": P.OVERTURE_RELEASE if places_source == "overture" else None},
        "built": date.today().isoformat(),
        "z": [round(net.z[n], 3) for n in net.order],  # to the millimetre: whether a link climbs depends on it
        "links": links,
        "lifts": {str(fi): {"id": net.feats[fi].id, "name": net.feats[fi].name, "type": net.feats[fi].type,
                            "cap": net.feats[fi].cap, "cap_known": net.feats[fi].cap_known,
                            "nursery": net.feats[fi].nursery, "sector": sectors.sector_of[fi],
                            **({"day_sectors": {str(k): round(v, 4) for k, v in sectors.day_sectors[fi].items()}}
                               if fi in sectors.day_sectors else {})}
                  for fi in lift_fis},
        "runs": {f.id: [f.name, f.grade] for f in net.feats if f.kind == "run"},
        "sectors": [{"name": n, "cap": c, "share": round(s, 4)}
                    for n, c, s in zip(sectors.name, sectors.cap, sectors.commute_share, strict=True)],
        "villages": [{"name": v.name, "sector": v.sector, "nodes": [[idx[n], c] for n, c in v.nodes], "cap": v.cap,
                      "skiers": round(v.skiers, 1)} for v in villages],
    }


def write(doc: dict, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{doc['domain']['id']}.json"
    path.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return path
