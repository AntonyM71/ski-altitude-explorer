# 012. Run busyness as Python structure plus a JavaScript engine in the browser

**Status:** Proposed (issue #3; OpenSpec change `busyness-production-architecture`): accepted once the overlay is deployed

**Code:** [busyness/](../../busyness/) (structure), [busyness-engine/](../../busyness-engine/) (behaviour), [.github/workflows/busyness.yml](../../.github/workflows/busyness.yml)

## Context

The busyness model (004–011) was a one-file prototype, run by hand on four domains. It couldn't run for the site's hundreds of domains each week:
- It found domains by ski-area name, which isn't unique.
- It re-read about 930 MB of raw data for every domain.
- It queried Overpass, a volunteer-run service, live.
- It took 25–35 s per large domain.

The project owner also wanted room for live scenarios later, such as bad weather up high or no snow low down.

## Decision

- **Show it as an overlay on each domain's map, relative within the domain.** Runs and lifts are coloured in four bands: quiet, moderate, busy and busiest, split at the domain's 50th, 80th and 95th percentiles (`BANDS`). There's no comparison between resorts. Lift capacity differs too much between regions (US resorts often have long lift lines with quiet runs below), so the model can only say which routes are relatively busy within one resort.
- **Split the model into structure and behaviour.**
  - **Structure,** prepared in Python (`busyness/`): the network, villages and sectors, one structure file per domain (about 60 KB compressed for Les Trois Vallées).
  - **Behaviour,** computed by one JavaScript engine (`busyness-engine/`): laps, commuting, the evening rides down and the views. It runs in a browser worker when the visitor turns the overlay on, and in Node for tests.
  - Both halves read one parameter file, `busyness-engine/src/params.json`.
- **Compute sectors exactly.** A lift's riders' next lifts are absorption probabilities of the laps' Markov chain (007), so Python needs only the pull rules, not a second copy of the laps simulation. A fixture test checks the engine's laps against them.
- **Take places and buildings from Overture Maps,** via DuckDB at a pinned release, cached per release (008).
- **Use the site's domain ids,** from `data/domains.json`, which `build_stats.py` writes.
- **Prepare busyness in its own workflow.** It runs weekly. It starts from the last published set, rebuilds only domains whose fingerprint changed, and publishes the set as release assets. The site's deploy takes the last good set, or deploys without the overlay. Only domains with at least 30 km of piste and 5 lifts are modelled (`MIN_KM`, `MIN_LIFTS`).
- **Check the observations in CI.** The four test domains' structure files are test fixtures, and the engine's tests check every observation that 011 marks as matched.

## Alternatives considered

- **Precompute everything in Python.** This would mean hours of compute a week, results stored for every domain, and no live scenarios.
- **Python in the browser (Pyodide).** About a 10 MB download and a slow start.
- **The GPU (WebGL or WebGPU).** Routing on networks of about 1,000 junctions is sequential, branchy work that a GPU doesn't speed up, and WebGPU's support on phones is patchy.
- **Overpass, a full OpenStreetMap extract, or harvesting places by hand.** Overpass can't take the load, and an extract is tens of gigabytes. Overture's bounding-box queries need no account and have no rate limits.
- **Comparing resorts.** Rejected for the reason above.

## Evidence

- **Speed:** the engine computes Les Trois Vallées in 1.2–1.4 s (on the owner's PC and in Node), against 27 s for the prototype's routing. Serre Chevalier takes 0.15 s. At phone width, in an emulator, it takes under 1 s.
- **Faithful to the prototype:** with the prototype's bug put back, its places and its commuting shares, every link's laps match within 1%. Day traffic correlates at 0.99 and morning and evening at 0.96–0.99; the differences come from different random draws and the exact sectors.
- **Overture places:** they matched Overpass's on 50 of 51 places in the four test domains. Building counts were within a few percent in the Alps, and 30–60% higher in Andorra. Grau Roig stayed a thoroughfare (10 buildings).
- **Bugs found by the port:**
  - The prototype counted lapping skiers from only one lift where several shared a top station (006).
  - Zero-pull exchanges put nursery lifts into sectors (007).
  - The new structure file at first rounded gradients, which flipped a run at 5.9997% over the 6% pull step.
- **The observations still hold** (011). Pelvoux is now 4th rather than 1st by day, and Combe and Lac 24th and 36th rather than 11th and 21st, all still busy. The project owner accepted these.

## Consequences

- **Two languages.** The pull rules are applied in both halves, guarded by the shared parameters and a fixture test. Every other piece of behaviour lives in one place.
- **Sectors are fixed per week.** Live scenarios will re-route skiers, but won't redraw the sectors. Splitting home areas from ski areas is known issue 11.
- **A lag of up to a week.** The overlay can trail the stats by up to a week, and shows the last good set if a busyness run fails.
- **First run.** Harvesting places for every domain takes about 15 s each. Later runs reuse the cache until the Overture pin moves.
- **Floating point.** Browsers may differ in the last digits of `Math.exp` and `Math.log`, so results agree to within 0.1% across browsers, not bit for bit.
