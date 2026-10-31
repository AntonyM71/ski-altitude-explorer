# busyness: the structure half of the busyness model

Prepares each domain's **structure** for the busyness engine in [`busyness-engine/`](../busyness-engine/): the run and lift network, villages and sectors. The engine computes the **behaviour** from it (laps, commuting, the evening rush and the views), in the browser or in Node. Rationale is in [docs/decisions/](../docs/decisions/) 004–012. What the system must do is in [openspec/specs/](../openspec/specs/) (`busyness-*`).

## Stages

| Module | Does |
|---|---|
| `partition.py` | Reads the raw OpenSkiMap runs and lifts once and splits them into the site's domains, by id, using `data/domains.json` from `build_stats.py`. |
| `network.py` | Builds the network: runs downhill, lifts uphill, joins at ends and crossings, walks at lift stations, rides down, nursery areas, and each black's committed length. |
| `places.py` | Gets places and building counts: `OvertureSource` (production), `CachedSource` (per release) and `OverpassSource` (local only). |
| `sectors.py` | Finds groups of lifts that exchange skiers, from exact absorption probabilities, then Louvain. It can be replaced (known issue 11). |
| `villages.py` | Works out where skiers stay: real places with enough buildings and lifts, or the lift layout as a fallback. |
| `structure.py` | Assembles, fingerprints, checks and writes a domain's structure file. |
| `cli.py` | The command-line tool. |

Constants that shape the structure live in `params.py`. Behaviour constants live in `busyness-engine/src/params.json`, which both halves read.

## Commands

Run `fetch.py` and `build_stats.py` first. Then:

```sh
# Every eligible domain (at least 30 km of piste and 5 lifts), places from Overture (cached per release)
uv run --group busyness python -m busyness build --all

# Some domains, by name or id, using only cached places (no network)
uv run --group busyness python -m busyness build --name "Serre-Chevalier" --places cache

# Rebuild even if unchanged; or find villages from the lift layout only
uv run --group busyness python -m busyness build --name "Serre-Chevalier" --force --places none
```

- **Output:** `data/busy/<domain id>.json`, and `data/busy/manifest.json` (domain id → fingerprint).
- **Fingerprints:** a domain is rebuilt only when its fingerprint changes. The fingerprint covers its runs and lifts, its places, `MODEL_VERSION`, `OVERTURE_RELEASE` and the shared behaviour constants.
- **The places cache:** `data/busy-cache/places-<release>.json`.

## Tests

```sh
uv run --group busyness --group dev pytest
uv run --group dev ruff check busyness tests
```

The tests live in `tests/busyness/` and use small, hand-made networks (`tests/busyness/helpers.py`).
