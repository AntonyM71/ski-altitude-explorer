# Design

## Context

See proposal.md for why. The current state:

- **Site build** (`.github/workflows/deploy.yml`): `fetch.py` downloads about 930 MB of OpenSkiMap data, cached per ISO week. `build_stats.py` streams it once, groups 5,351 domains (138 linked) and writes `data/ski_area_stats.json` and `data/runs/<id>.json`, which holds runs and lifts with simplified lines. `index.html` is one page with one inline script and MapLibre from a CDN, with no build step. It loads a domain's runs file when the domain is opened. The build takes 1–2 minutes and has a 45-minute limit. The repository is public, so Actions minutes are free.
- **The prototype** (`prototypes/busyness.py`, 991 lines) is one `Model` class. It selects a domain by ski-area name, re-streams the raw files, calls Overpass, and writes `data/busyness/<slug>/busy.geojson`. Its stages already follow the specs: network, laps, sectors, villages, commuting, views.
- **Trials** (session scratchpad):
  - A JavaScript port of laps, demand and one routing pass matched Python. Laps agree to 0.02 skiers an hour; routing correlates at 0.99.
  - It ran in 1.4 s for Les Trois Vallées on the owner's PC, against 27 s in Python. The structure file is 213 KB, or 40 KB compressed.
  - Overture matched Overpass on 50 of 51 places. Building counts are within a few percent in the Alps, higher in Andorra, and the thresholds still hold. A query takes about 50 s per domain if done one by one.
- **Domains above 30 km of piste:** 443.

## Goals / Non-Goals

**Goals:**
- One behaviour engine, used by the site, the review map, the tests and the CI checks.
- A pipeline that's cheap in a normal week, fails safely, and never blocks the stats site.
- Small, separately tested stages in both halves, built from the spec scenarios.
- Today's validated behaviour carried over, except the deliberate fix and the change of places source.

**Non-Goals:**
- Scenario controls, such as bad weather or no snow low down. The architecture makes them possible; they come later.
- Redefining sectors as home areas and ski areas (known issue 11), or any other modelling refinement (snow conditions, buses).
- Precomputed views for phones. Revisit if phones prove too slow.
- Comparing domains with each other.

## Decisions

### 1. Two halves, split at "structure" versus "behaviour"

```
 busyness/ (Python)                          busyness-engine/ (JavaScript)
 partition -> network -> villages ->         laps -> demand -> routing ->
 sectors -> structure file                   evening ride-down -> views -> checks
       |                                            ^
       +--------- data/busy/<id>.json --------------+
                  (structure only)
```

**Structure** depends only on the map data and the place data. It covers the network, crossings, committed lengths, nursery flags, villages, sectors and commuting shares, and it changes at most weekly. **Behaviour** depends on assumptions (pull, ability groups, end-of-day factors, noise), and is what future scenarios will vary.

- *Alternative:* precompute everything in Python. Rejected: it gives no live scenarios, it costs hours of compute each week, and it means two places to keep results.
- *Alternative:* run Python in the browser (Pyodide). Rejected: a download of about 10 MB, slow start-up, and `networkx` in the browser.

### 2. One parameter file shared by both halves

`busyness-engine/src/params.json` holds the behaviour constants: `GRADE_PULL`, `LIFT_PULL`, `BLACK_SHORT_M`, `BLACK_LONG_M`, `ABILITIES` and the rest. The engine imports it. Python reads it too, because sector-finding needs the pull rules. Structure constants such as `SNAP_M` and `PLACE_M` stay in `busyness/params.py`.

- *Alternative:* copy the constants into Python. Rejected, because the copies drift; a shared file means one edit.

### 3. Sectors from exact absorption probabilities

Build the junction-to-junction matrix `Q` and the junction-to-lift matrix `R` from the pull weights. Each lift's riders' next-lift shares are then the rows of `B = (I − Q)⁻¹ R`, at the lift tops. These replace the 30-sweep simulation, then go through the same Louvain grouping and the 4% merge. Solved with `numpy` (a dense solve; about 1,000 junctions for Les Trois Vallées, so milliseconds).

- A fixture test checks `B` against the engine's laps run from single lifts. That one test confirms the shared pull rules are applied the same way in both halves.
- The step sits behind a `find_sectors(network, params) -> SectorResult` function, so known issue 11 can replace it.
- *Alternative:* call the JavaScript engine from Python, through Node, for the exchanges. Rejected: it adds a language hop in the pipeline.

### 4. Partition by the site's domain ids, reading the raw data once

`build_stats.py` writes `data/domains.json`, mapping each top-level domain id to its member ski-area ids, its piste km and lift count. It also adds a stable id to each run and lift in `data/runs/<id>.json`: OpenSkiMap's feature id, as `i`. The busyness `partition` stage streams the raw runs and lifts once, and buckets features into every eligible domain by their ski-area ids.

- *Alternative:* select by ski-area name, as the prototype does. Rejected, because names aren't unique and linked domains have no name in OpenSkiMap.

### 5. Python package layout

```
busyness/
  __init__.py
  params.py        structure constants; loads the shared params.json
  partition.py     raw files -> per-domain runs and lifts
  network.py       links, junctions, crossings, walks, rides down, nursery, committed length
  places.py        PlaceSource protocol: OvertureSource (DuckDB batch), CachedSource, OverpassSource (local)
  villages.py      places -> villages (and the lift-layout fallback)
  sectors.py       absorption probabilities -> Louvain -> merge small sectors -> commuting shares
  structure.py     assemble, fingerprint, validate (commuting shares), write
  cli.py           python -m busyness build [--domain ID ...] [--all] [--places overture|cache|overpass]
tests/busyness/    pytest, one file per module; fixtures in tests/fixtures/busyness/
```

- Plain functions over small dataclasses, not one large class. Each stage takes the previous stage's output.
- `ruff` for linting and formatting.
- `pytest`, `ruff` and `duckdb` live in dependency groups; site builds don't need them.

### 6. Engine layout: plain ES modules, no build step, no dependencies

```
busyness-engine/
  package.json     {"type": "module", "scripts": {"test": "node --test"}}
  src/params.json  behaviour constants (shared with Python)
  src/random.js    seeded generator (mulberry32 + Box-Muller)
  src/graph.js     adjacency, binary heap, shortest paths, path walk
  src/laps.js      pull, laps flow (sources summed per top station: the fix)
  src/demand.js    gravity model
  src/routing.js   route times by ability; commuters out and home; locals home
  src/evening.js   ride-down passes, capped at capacity
  src/views.js     day / morning / evening, lift loads, bands
  src/checks.js    negative traffic and share checks
  src/index.js     run(structure, params) -> results
  src/worker.js    browser Web Worker wrapper
  bin/run.mjs      command-line runner: busiest runs and lifts per view
  test/*.test.js   node:test; scenario tests on fixture networks; observation checks on test-domain fixtures
```

- JSDoc types on exported functions, so editors can check them without TypeScript.
- The site and the review map load `src/worker.js` as a module worker. The deploy copies `busyness-engine/src/` to `_site/busyness-engine/src/`, the same relative path as when the repository is served locally.
- *Alternative:* TypeScript with a bundler. Rejected for now: it would be the site's first build step. JSDoc gives most of the checking.

### 7. Shared fixtures and observation checks

- **Small handmade networks** (`tests/fixtures/busyness/*.json`) in the structure format, with expected results. Examples: two lifts sharing a top station, a junction split by pull, a black crossed by an easier run, a gondola that can be ridden down. Both test suites use them.
- **Structure files for the four test domains** are committed under `tests/fixtures/busyness/domains/`, about 1 MB in all, and regenerated with the CLI when structure code changes.
- `busyness-engine/test/observations.test.js` encodes every row decision 011 marks as matched as an assertion on these fixtures, named after the observation. CI runs it on every push.

### 8. Workflows: the release asset is both cache and published set

- **`busyness.yml`** runs weekly on Mondays after the stats build, and on demand:
  1. Fetch the raw data (same weekly cache key as the deploy) and run `build_stats.py` for `domains.json`.
  2. Download the latest published set from the `busyness-latest` release (`busyness.tar.gz` and `manifest.json` of domain id → fingerprint).
  3. Harvest Overture places for domains without cached places at the pinned release. The cache is another release asset, `places-<release>.json`.
  4. Rebuild only the domains whose fingerprints changed; reuse the rest.
  5. Run pytest and the engine checks.
  6. Upload the new set, overwriting the release assets, then trigger `deploy.yml`.
- **`deploy.yml`** gains one step: download `busyness.tar.gz` from `busyness-latest` if it exists, and unpack it to `_site/data/busy/`. It also copies `busyness-engine/src/` to `_site/busyness-engine/src/`. If the download fails, the step continues and the site deploys without the overlay.
- **`test.yml`** runs on every push and pull request: `ruff`, `pytest` and `node --test`.
- *Alternatives:* a data branch (rejected: hundreds of files rewritten in git history every week) and the Actions cache alone (rejected: it's evicted after 7 days unused or under size pressure, so it can't be the only copy of the published set).

### 9. Overture harvest

- One DuckDB session per run, with the `spatial` and `httpfs` extensions.
- **Places:** one query for division points (`subtype` = locality or neighborhood, excluding microhoods) inside the union of the pending domains' bounding boxes. Classes town, village and hamlet become Overpass's kinds; neighborhood maps to suburb.
- **Buildings:** one query that counts buildings within 500 m of each candidate place, done inside DuckDB by joining building bounding-box centres to place points in a small grid. Only counts come back. This replaces 443 per-domain scans (about 50 s each) with one pass.
- **The pin:** `OVERTURE_RELEASE = "2026-10-21.0"`, kept in `busyness/params.py`.
- **Neighbourhoods come second** (found during implementation). Overture maps many towns as several neighbourhoods (Val d'Isère as La Balme, le Rosset and others; Grandvalira's housing estates), which split villages apart when stations took the nearest point of any kind. A station belongs to the nearest town, village or hamlet within `PLACE_M`, and to a neighbourhood only if there's none, which keeps Val Claret (only a neighbourhood, about 2 km from Tignes) as a village.
- **Buildings:** one query per domain's box, with DuckDB's metadata cache on (`enable_object_cache`): about 15 s per domain after the first, so the batch-join plan above wasn't needed.

### 10. Overlay on the site

- A "Busyness (experimental)" toggle and a day/morning/evening switch in the map legend. They appear only for domains listed in the published `data/busy/manifest.json` (fetched once). This replaced a `busy` flag in the stats file during implementation: the stats are built before the busyness set is downloaded, so they can't know which domains have one.
- On the toggle, the page fetches the structure file and starts the module worker. It shows "Computing…", and the engine returns per-run and per-lift values for all three views.
- **Values to the map:** each run's length-weighted traffic is set by its run id (`i`) as a property on the run features already on the map. Bands are 50th, 80th and 95th percentiles of length-weighted traffic within the domain (`BANDS`). Lifts are banded by demand ÷ capacity. The page caches results per domain for the visit, so switching views doesn't recompute.
- The legend and hover text use bands only. The attribution adds Overture Maps and OpenStreetMap.

### 11. Fix the shared-top bug in the new code, then recheck everything

Laps sum their sources per top station. Because the fix and the switch to Overture places both change numbers, decision 011 is rerun in full on the new pipeline and engine. Its table and the known issues are then updated, and any regression is discussed before the old prototype is removed.

## Risks / Trade-offs

- [Floating-point differences between browsers' `Math.exp` and `Math.log`] → The specs promise identical results within one engine and agreement to 0.1% between browsers, not bit-identical output.
- [Phones are slower: perhaps 3–6 s for the largest domains] → Compute only when the overlay is turned on, in a worker, with a progress state. If that proves too slow, precomputed default views are a later option.
- [The dense solve for very large domains (Dolomiti Superski, about 2× Les Trois Vallées)] → `numpy` handles a few thousand junctions in seconds. If not, switch to a sparse solve (`scipy`).
- [Overture's place types differ from OpenStreetMap's] → Map them as decided; the trial showed 50 of 51 places matching. Known differences (Courchevel's point, renamed communes) are noted in decision 008.
- [Overture releases expire] → The cache is keyed by release. Moving the pin is a deliberate change that triggers a full rebuild.
- [Two languages share the pull rules] → One shared `params.json`, plus the exchange-versus-laps fixture test.
- [Numbers change: the bug fix and Overture places] → A full recheck against decision 011 before the prototype is retired, with regressions brought to the owner.
- [A GitHub release used as storage] → Simple and public. If it's lost, the next weekly run rebuilds everything, slowly but safely.

## Migration Plan

1. Build the package and engine alongside the prototype, then check that they match it on the four test domains, apart from the fix.
2. Fix the bug, switch places to Overture, recheck decision 011, and update the docs.
3. Add the workflows. Run the busyness workflow by hand once, for the slow first harvest, and publish the first set.
4. Ship the overlay.
5. Delete `prototypes/busyness.py`, and point the review map at the engine.

**Rollback:** delete the `busyness-latest` release, or revert the deploy step. The site falls back to no overlay.

## Open Questions

- Default size threshold: is `MIN_KM = 30` and `MIN_LIFTS = 5` right? It's easy to tune later without changing the design.
