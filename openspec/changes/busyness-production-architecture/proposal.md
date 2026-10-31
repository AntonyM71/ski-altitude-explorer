# Proposal

## Why

The busyness model (issue #3) exists only as a one-file prototype, run by hand on four domains. It looks domains up by name, re-reads about 930 MB of raw data for every domain, queries a volunteer-run service (Overpass) live, and takes 25–35 s per large domain. None of that can run for the site's hundreds of domains each week. Trials have shown a way through:
- **Places:** Overture Maps, queried with DuckDB, matched Overpass on 50 of 51 places.
- **Engine:** a JavaScript port of laps and routing reproduced the prototype exactly, and ran in 1.4 s for the largest test domain in a browser.

The owner wants this production architecture settled before any further modelling refinements.

## What Changes

- **A per-domain busyness overlay on the site's map.** Runs and lifts are coloured by their modelled traffic, banded relative to the rest of the same domain, for the day, morning rush and evening rush. It's labelled as an experimental relative index, with no comparison between domains.
- **The model splits into two halves:**
  - **Structure, prepared in Python:** the run and lift network, villages and sectors for each domain, written as a compact structure file.
  - **Behaviour, computed in the browser:** laps, commuter demand, routing, the evening rides down and the views, by one JavaScript engine running in a background worker. The same engine runs in Node for tests and checks.
- **A separate busyness workflow** prepares structure files for every domain above a size threshold, and recomputes only domains whose inputs changed. The site deploy uses the last good set, so a busyness failure never blocks the stats site.
- **Places and buildings come from Overture Maps** (via DuckDB, from a pinned release), harvested in one batch and cached. Overpass stays only as a local fallback.
- **Domains are identified by the site's domain ids,** including linked domains, not by ski-area name.
- **Sectors are computed exactly** from the network, using the probability that a skier from one lift next rides another, rather than a step-by-step simulation. Grouping still uses Louvain, behind a replaceable step, so a better definition (known issue 11) can be swapped in later.
- **Fix:** lapping skiers are counted from every lift, including where several lifts share a top station (a bug in the prototype, since fixed).
- **Code:** a Python package with a module per stage and tests; a JavaScript engine of plain ES modules with no build step, tested with Node's built-in test runner; shared fixture networks so both halves are tested against the same cases; decision 011's observations checked automatically in CI.
- **BREAKING (prototype only):** `prototypes/busyness.py` and `data/busyness/<slug>/busy.geojson` are replaced. The review map moves to the new structure files and engine.

## Capabilities

### New Capabilities

- `busyness-pipeline`: preparing, caching and publishing busyness structure files for every eligible domain, separately from the site build.
- `busyness-overlay`: the busyness overlay on the site's domain map, computed in the browser, banded within the domain.

### Modified Capabilities

- `busyness-laps`: lapping skiers are counted from every lift that shares a top station.
- `busyness-sectors-villages`: sectors are computed from exact lift-to-lift exchange probabilities; villages come from Overture Maps places and buildings at a pinned release.
- `busyness-commuting`: random route draws are seeded, so every run of the engine gives the same result.
- `busyness-views`: results come from the engine run on a structure file, not from per-domain GeoJSON; the review map uses the same engine.
- `busyness-validation`: the observation checks run automatically on the test domains in CI.

## Impact

- **New code:**
  - a `busyness/` Python package, replacing `prototypes/busyness.py`;
  - a `busyness-engine/` directory of JavaScript modules, with tests and a minimal `package.json` (no dependencies);
  - tests and shared fixtures.
- **Changed:** `build_stats.py` exposes each domain's member ski areas and gives every run a stable id; `index.html` gains the overlay; `.github/workflows/deploy.yml` adds the last good busyness files to the site; a new `.github/workflows/busyness.yml`.
- **Dependencies:** `duckdb` and `numpy` in the `busyness` dependency group (`networkx` is already there); `pytest` and `ruff` as dev tools; Node in CI for the engine's tests. No new runtime dependency for the site.
- **External services:** Overture's public S3 bucket replaces live Overpass queries. The site credits Overture Maps and OpenStreetMap.
- **Docs:** a new decision record for the architecture; updates to decision 008 (Overture places), decision 007 (exact sectors) and the README; known issues 5 and 9 resolved or updated, and the shared-top bug removed from them.
- **Results:** fixing the shared-top bug and switching places to Overture both change the model's numbers, so every observation in decision 011 is rechecked.
