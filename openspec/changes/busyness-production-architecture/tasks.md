# Tasks

## 1. Tooling and shared parameters

- [x] 1.1 Add `numpy` and `duckdb` to the `busyness` dependency group and a `dev` group with `pytest` and `ruff`; configure `ruff` and `pytest` in `pyproject.toml`. Verify `uv sync --group busyness --group dev` succeeds and `uv run ruff check build_stats.py` runs.
- [x] 1.2 Create `busyness-engine/` with `package.json` (`"type": "module"`, `"test": "node --test"`, no dependencies) and `src/params.json` holding every behaviour constant from the prototype. Verify `node --test` runs (no tests yet) and the JSON parses.
- [x] 1.3 Create the `busyness/` package with `params.py` (structure constants, `OVERTURE_RELEASE`, `MIN_KM = 30`, `MIN_LIFTS = 5`, and a loader for the shared `params.json`). Verify `uv run python -c "import busyness.params"` prints no error and the loader returns `GRADE_PULL`.

## 2. Domain ids and stable feature ids in the site build

- [x] 2.1 Make `build_stats.py` write `data/domains.json` (top-level domain id â†’ member ski-area ids, piste km, lift count) and add OpenSkiMap's feature id as `i` to each run and lift in `data/runs/<id>.json`. Verify by running `build_stats.py` and checking that Les Trois VallÃ©es's entry lists its six member areas and that its runs file's entries carry `i`. (Done. Les Trois VallÃ©es lists its own id only: OpenSkiMap tags its sub-areas' runs with it, which is the site's membership. Linked domains list every member and sub-area, e.g. the Via Lattea's five.)
- [x] 2.2 Check the site still works with the extra field: open `index.html` on the local server, open Les Trois VallÃ©es and Serre Chevalier, and verify runs and lifts draw as before.

## 3. Python structure pipeline

- [x] 3.1 `partition.py`: stream the raw runs and lifts once and bucket them by eligible domain id. Verify with a pytest on a tiny hand-written GeoJSON (two domains, one shared name) and by checking that the run and lift counts for Les Trois VallÃ©es and Serre Chevalier match what the prototype loads for the same ski areas.
- [x] 3.2 `network.py`: port links, end joins, crossings, short-piece joins, walks, ride-down links, nursery flags and committed lengths from the prototype as functions. Verify with pytest cases for each busyness-network scenario (a run drawn uphill, a run under a lift, an X crossing, two cuts at one place, a walk to a run below a lift top, the gondola ride down, a magic carpet link) and that Serre Chevalier's junction and link counts match the prototype's.
- [x] 3.3 `places.py`: a `PlaceSource` protocol with `OvertureSource` (DuckDB batch queries for division points and building counts within 500 m, done inside DuckDB), `CachedSource` (a per-release JSON file) and `OverpassSource` (the prototype's, for local use). Verify with a pytest on `CachedSource` and a manual Overture run over the four test domains that reproduces the trial: 50 of 51 places matched, Grau Roig under 50 buildings. (Done: 50 of 51 matched, about 15 s per domain with the metadata cache. Les Brames, Serre Ratier and Puy Richard now reach 50 buildings, so they become villages: recheck in 5.3.)
- [x] 3.4 `villages.py`: port village finding (places, the 1 km and 200 m rules, the building and capacity thresholds, the lift-layout fallback, residents by lifts out); microhoods excluded, neighbourhoods allowed. Verify with pytest cases for each villages scenario and that the four test domains' village lists match the trial's expectations (Val Claret appears; Grau Roig doesn't). (Done. Found: stations attach to a town, village or hamlet first and to a neighbourhood only if there is none, or towns split into quarters; spec and design updated. Val-Claret, Tignes, Val-d'IsÃ¨re, Encamp and Canillo are villages; Grau Roig isn't.)
- [x] 3.5 `sectors.py`: exact absorption probabilities `B = (I âˆ’ Q)â»Â¹ R` from the shared pull rules, then Louvain, the `SECTOR_MIN` merge, nursery lifts' sectors and commuting shares, behind `find_sectors(network, params)`. Verify with a pytest on a fixture network with a known answer and that the four test domains' sectors match the prototype's groupings. (Done. Serre Chevalier identical; Les Trois VallÃ©es one sector differs by 2 lifts; Tignesâ€“Val d'IsÃ¨re merges the Cascade (Le Fornet) and LeissiÃ¨res sectors: recheck in 5.3.)
- [x] 3.6 `structure.py` and `cli.py`: assemble the structure file (per busyness-pipeline), compute the fingerprint, check commuting shares are within 0â€“100% (stop otherwise), and write `data/busy/<id>.json`; `python -m busyness build --domain ID` and `--all`. Verify the four test domains build, a forced bad share stops the run without writing, and Les Trois VallÃ©es's file is about 200 KB. (Done: the four test domains build; Les Trois VallÃ©es is 306 KB because it also carries run and lift names for the overlay. An unchanged domain is skipped.)
- [x] 3.7 Document the package in a short `busyness/README.md` (stages, commands, place sources) and verify the documented commands run as written.

## 4. JavaScript engine

- [x] 4.1 `random.js` and `graph.js`: the seeded generator, binary heap, shortest paths (forward and reverse) and path walk. Verify with `node:test` cases: a fixed seed's first values, and shortest paths on a small fixture with a known answer.
- [x] 4.2 `laps.js`: pull (grade, gradient, short blacks, walks, nursery, rides down), the laps flow, and sources summed per top station (the fix for known issue 11). Verify with `node:test` cases for every busyness-laps scenario, including two lifts sharing a top station, and that laps match Python's exact exchange shares on the shared fixtures to within 0.1%.
- [x] 4.3 `demand.js` and `routing.js`: gravity demand, route times by ability (including end-of-day conditions, skied-out runs, easy pace), commuters out and home, and locals home. Verify with `node:test` cases for the busyness-commuting scenarios and a determinism test (two runs, identical results).
- [x] 4.4 `evening.js`: the ride-down passes capped at capacity (`DOWNLOAD_MAX_LOAD`, `DOWNLOAD_PASSES`). Verify with a fixture where demand to ride down exceeds capacity and the excess skis home.
- [x] 4.5 `views.js`, `checks.js` and `index.js`: day, morning and evening, lift loads, riding down, per-run aggregation by run id, bands at `BANDS`, and the negative-traffic check. Verify with `node:test` cases for the busyness-views scenarios, the band scenarios, and a forced negative value that makes `run` throw.
- [x] 4.6 `bin/run.mjs`: print the busiest runs and lifts per view for a structure file. Verify it runs on Les Trois VallÃ©es's structure in under 3 s on a laptop.

## 5. Agreement, the bug fix and observations

- [x] 5.1 Commit the four test domains' structure files as fixtures and add `observations.test.js`, asserting each row decision 011 marks as matched. Verify `node --test` passes, or lists each failing observation by name.
- [x] 5.2 Compare the new pipeline and engine with the prototype on the four test domains, apart from the bug fix and the Overture places, and record the differences. Verify that laps match the prototype with the fix disabled, and that routing correlates at 0.99 or better. (Done. With the bug put back, the prototype's places and the same commuting shares, every link's laps match within 1%. Day traffic correlates at 0.99, morning and evening at 0.96–0.99: different random draws, and the exact sectors. Found and fixed: the structure file rounded gradients, which flipped a run at 5.9997% over the 6% pull step. Found in the prototype: zero-weight exchanges put nursery lifts into sectors, inflating Serre Chevalier's Combes sector (35% commuting instead of 45%); the new code follows the spec.)
- [x] 5.3 Recheck every observation with the fix and Overture places on. Update decision 011's table and the known issues (11 resolved; 5's place names; any regressions), and bring any regression to the project owner before continuing. Verify the docs' numbers match `bin/run.mjs` output. (Done. Accepted by the project owner: Pelvoux 4th (was 1st), Combe 24th and Lac 36th (were 11th and 21st), all still busy. The Laisinant traverse (4th) and Santons (63rd and 70th) got worse in the evening, noted under known issues 1 and 2. The shared-top bug was removed from the known issues and recorded in decision 006.)

## 6. Overlay on the site

- [x] 6.1 `worker.js` and the overlay in `index.html`: a "Busyness (experimental)" toggle and day/morning/evening switch shown only for domains marked `busy` in the stats; the worker computes on the first toggle; a progress state; colours by band set on the existing run and lift features by id; a legend and hover text with bands only; attribution for Overture Maps and OpenStreetMap; a message where workers aren't available. Verify on the local server: Les Trois VallÃ©es shows bands in all three views, switching views doesn't recompute, the map stays usable while it computes, and a small domain shows no control.
- [ ] 6.2 Check the overlay on a phone-width viewport and on a phone: it computes, the controls are reachable, and the legend doesn't cover the chart. Verify by screenshot at 390 px wide and on the owner's phone.
- [x] 6.3 Point `prototypes/busyness_review.html` at a structure file and the engine (`?d=<domain id>`). Verify it shows the same busiest runs as `bin/run.mjs` for Serre Chevalier.

## 7. Workflows

- [x] 7.1 `test.yml`: on every push and pull request, run `ruff`, `pytest` and `node --test`. Verify a run on a branch passes. (Passed on the busyness-production branch, run 41192380800.)
- [ ] 7.2 `busyness.yml`: weekly and on demand. It fetches and partitions, downloads the last published set and places cache, harvests Overture for new domains, rebuilds changed domains only, runs the tests, uploads `busyness.tar.gz`, `manifest.json` and the places cache to the `busyness-latest` release, and triggers the deploy. Verify that a first manual run publishes a set for every eligible domain, and that a second run rebuilds none (all fingerprints unchanged).
- [ ] 7.3 `deploy.yml`: download and unpack the latest set to `_site/data/busy/` if present, copy `busyness-engine/src/` to `_site/busyness-engine/src/`, and continue without them if the download fails. Verify a deploy with the release present shows the overlay, and a deploy run with the download forced to fail still succeeds.

## 8. Retire the prototype and update the docs

- [ ] 8.1 Delete `prototypes/busyness.py` and the `data/busyness/` outputs once 5.3 is accepted. Verify nothing in the repository still imports or links to them (`grep`).
- [x] 8.2 Write decision record 012 (the production architecture: the two halves, the shared parameters, exact sectors, Overture, the release-asset pipeline, banding within the domain), and update decisions 007, 008 and 009's "Code:" lines, the README's busyness section and known issue 9. Verify all links in the changed docs resolve.

## Workflow follow-up

- Review the results and the overlay with the project owner before archiving.
- Archive the change with `/opsx:archive`, which merges the deltas into `openspec/specs/`.
