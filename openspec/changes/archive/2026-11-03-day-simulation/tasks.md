# Tasks

## 1. Pull rule (busyness-laps)

- [x] 1.1 Tidy the trialled full-weight pull rule in `laps.js`: lift pull with altitude and queue, runs and walks by the lift pull ahead × the easiest way on, uphill walks at the near-flat weight. Remove the trial settings `LIFT_RATE_EXP` and `AHEAD_HALF_MIN` from `laps.js` and `params.json`. Verify `node --test` loads.
- [x] 1.2 Rewrite the laps tests for the spec's scenarios (a big lift beside two runs, the same lift with a queue, a run ending at a queue, a bigger lift a short run away, a long black on the only way, a black beside an easier way, level and uphill walks, near-flat run, altitude). Verify they pass.
- [x] 1.3 Keep the sector check honest: the test comparing laps with the pipeline's exact exchange shares runs on plain pulls (no lookahead), matching `busyness/sectors.py`. Verify that test passes.

## 2. The simulated day (busyness-day-simulation)

- [x] 2.1 Add `src/simulate.js`: the network's delay lines with split arrivals, junction sweep within a step (highest first, climbing zero-delay links to the next step), lift queues boarding up to capacity per step, and cohorts by home village × purpose. Verify with a unit test on a two-lift loop that skiers are conserved every step (sum within 1e-6 of the population).
- [x] 2.2 Departures: each village's lappers and commuters appear at its stations by capacity, evenly over 09:00–10:00 (`START_H`, `ARRIVE_MIN`). Verify with a test that a village with two stations sends two-thirds from the bigger.
- [x] 2.3 Lappers by pull, with pulls refreshed every `PULL_MIN` = 5 minutes from current waits. Verify with a test that a lift nobody reaches carries nobody, and that a lift beside an overfull one gains skiers as the queue grows.
- [x] 2.4 Route trees: per destination (sector bottoms, village stations), ability and draw, by backwards Dijkstra on `routeTimes` with current waits; cohorts split over next steps by ability share and evenly over draws; refreshed every `REROUTE_MIN` = 15 minutes. Commuters switch to lapping on reaching a lift bottom of their sector. Verify with a test that a commuter cohort arrives at its sector and that a 20-minute queue on the quick way moves later routes to the other way.
- [x] 2.5 Going home at 15:00 (`HOME_H`): every cohort switches to heading home from where it is; queued skiers keep their place only in the share whose next step home is that lift; rides down queue at the top. Verify with a test that everyone in a small network is home by the end of the evening window, and that a ride down over capacity builds a queue at its top.
- [x] 2.6 Windows and reports: accumulate per-link entries, lift boarding, queue growth and sampled waits for the morning (09:00–10:30), day (11:00–14:30) and evening (15:00–16:30) windows; report the share not home at the end, the population on the hill by state, and links unsettled between the day window's halves (over 10% apart, links over 100 an hour). Verify with a test on a loop network that a settled day has no unsettled links and a trap is listed.
- [x] 2.7 Add the new parameters to `params.json` with their rationale note (`STEP_S`, `START_H`, `ARRIVE_MIN`, `MORNING_TO_H`, `DAY_FROM_H`, `DAY_TO_H`, `HOME_H`, `EVENING_TO_H`, `PULL_MIN`, `REROUTE_MIN`). Verify the engine reads them all (a test with changed windows changes the views).

- [x] 2.8 Dead ends and islands in the pipeline (`busyness/network.py`): a walk from each junction with no way on to the nearest lift bottom within `DEAD_END_WALK_M` = 1,000 m; then drop runs and walks from which no lift bottom can be reached. Verify with Python tests (a run stopping short gets a walk; a junction with a nursery way on gets none; a far run is dropped), and rebuild the four test domains.
- [x] 2.9 Nursery areas as a last resort in the engine: nursery lifts and slopes pull at `NURSERY_PULL` = 0.05 in `pulls`, and none in `plainPulls`. Verify with laps tests (a nursery slope beside a blue takes 1/21; a magic carpet that's the only way up is taken).
- [x] 2.10 Render the junctions with no way on (`data/deadends.html`) again after 2.8 and 2.9, and check the share of skiers stuck at junctions at noon is near zero on all four test domains (`bin/run.mjs`).

## 3. Engine wiring (busyness-views, busyness-queues, busyness-commuting)

- [x] 3.1 `index.js` runs the simulation in place of `dayWaits` and the routing passes, returning the same result fields (`links`, `runs`, `lifts`, `bands`, `waits`) plus the simulation's reports. Remove `queues.js`, `rushWaits`, `routeWithRidesDown`, `RAMP`, `DAY_HOURS`, `QUEUE_PASSES` and `DOWNLOAD_PASSES`, and their tests. Verify `node --test` passes except observation tests, and that the overlay worker's output format is unchanged (the `liftsForSite` test passes).
- [x] 3.2 Rewrite the views, queues and routing tests for the spec scenarios (a lift with a queue reported as demand over 1.0× and its average wait, a lift with room, commuters counted in the rush windows not the day, reading a wait from a queue). Verify they pass.
- [x] 3.3 Check determinism: run each test domain twice and verify identical results (a test).
- [x] 3.4 Update `bin/run.mjs` and `bin/diagnose.mjs` for the new results and reports (population by state, unsettled links, not home). Verify both run on the four test domains.

## 4. Results on the test domains

- [x] 4.1 Render before and after with `node busyness-engine/bin/mapdiff.mjs` on all four test domains, check the render (headless screenshot), and show the project owner: Daille, Tommeuses, Mont Blanc, the glaciers and Grande Motte first. Verify `data/mapdiff.html` is written.
- [x] 4.2 Run the observation tests; for each, record the new result in decision 011's table. Mark any that now fail as known failures (`todo`) with the reason, not loosened. Verify `node --test` passes with only the marked todos.
- [x] 4.3 Record each domain's run time in Node, and the population on the hill by state at midday, in the decision record. Verify the numbers are in the record.

## 5. Documentation

- [x] 5.1 Write `docs/decisions/017-day-simulation.md`: why conservation, the simulated day, the pull rule (with the Mont Blanc and Tommeuses trial and the scaling bug it fixed), what was tried before (fixed releases, the closed-loop trial and its traps), what the views mean now, and the population caveat. Add it to the decisions index. Verify the links resolve.
- [x] 5.4 Note the map gap at Serre Chevalier (Isolée should meet Rocher de l'Enfer and lead to the top of Forêt) in docs/ideas-and-fixes.md's map fixes. Verify it's listed.
- [x] 5.2 Update decisions 004, 006, 010 and 015 with notes pointing to 017 where their mechanisms are replaced, and known issues 8, 17, 18, 22 and 24 (and the diagram) for what's fixed or changed. Verify each mention of fixed releases, `RAMP` or `rushWaits` in docs/ is updated (grep).
- [x] 5.3 Commit `bin/mapdiff.mjs` with a usage line in the engine's README. Verify the documented command runs.

## Workflow follow-up

- Archive the change once the project owner is happy with the rendered results.
