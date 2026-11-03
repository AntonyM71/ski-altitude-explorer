# Proposal

## Why

The busyness model doesn't conserve skiers. Every lift's top lets off a fixed share of its capacity (about 55%), whether anyone rode it or not, so every lift looks about half full by day. A lift nobody reaches still sends skiers down its runs. Skiers who ski away from an area never have to come back, so high areas empty out and valley lifts collect everyone (known issues 18 and 22). Tuning pulls can only move this fixed traffic around; trials of a stronger altitude preference, vertical per minute and a distance discount all failed to bring skiers back to the glaciers. The day, morning and evening are also three separate calculations with their own assumptions (a 40% ramp of laps in the rushes, a queue formula), not one consistent day.

## What Changes

- **New: a simulated day.** The engine steps through the day minute by minute. Each village's skiers appear over 09:00–10:00 and head for its lifts. They lap, or commute to another sector and lap there. At 15:00 everyone heads home. Skiers are conserved: a lift carries only who is waiting at its bottom, up to its capacity, and nobody comes off a lift's top unless they rode it. The skiers who can't board yet are the queue.
- **New pull rule:** a run pulls like the lifts it leads to, at full weight, times the easiest way on from it. So a lift a short run away counts as fully as one at hand, and a hard stretch on the only way to a lift dissuades skiers. A walk that climbs pulls like a near-flat run. This replaces the separate lookaheads for queues and altitude, and the scaling of runs against lifts by `LIFT_PULL`.
- **The three views come from the simulation:** the morning rush (09:00–10:30), the day (the settled middle of the day, 11:00–14:30) and the evening rush (15:00–16:30), each as skiers an hour per link and as load and modelled wait per lift.
- **BREAKING (engine internals):** removes the fixed lift-top releases (`lapSources`), the iterated day waits (`dayWaits`), the rush-wait formula (`rushWaits`), `RAMP`, `DAY_HOURS` and the passes of successive averages (`QUEUE_PASSES`). The overlay's results format stays the same.
- **Dead ends and islands (busyness-network):** conservation shows up junctions where runs end with nothing leading on, which the old model hid by dropping skiers there. A dead end gets a walk to the nearest lift bottom within 1 km, as a backup for gaps in the map. Parts from which no lift can be reached are dropped as islands.
- **Nursery areas stay usable:** lapping skiers can take nursery slopes and lifts, at 0.05 of the pull, as a last resort ("allowed, but bad form"), instead of never.
- **Population:** today's village skiers (lift capacity ÷ 3.5) as a first input, to be calibrated against decision 016's bed counts in a later change.
- **Out of scope:** breaks and lunch (they average out over the day), day visitors arriving by car (known issue 23), and run-time optimisation for the browser.

## Capabilities

### New Capabilities
- `busyness-day-simulation`: the simulated day. Who is on the hill and when, how lifts load from their queues, how skiers move over runs and lifts minute by minute, and how the views are taken from it.

### Modified Capabilities
- `busyness-laps`: lifts carry what reaches them, not a fixed share of capacity. Lift tops no longer release skiers on their own. New pull rule at junctions. The altitude preference sits in the lift's pull.
- `busyness-queues`: a queue is the skiers waiting at a lift's bottom, and its wait is that queue ÷ capacity. No overload iteration and no rush formula. Queues repel skiers through the current wait.
- `busyness-views`: the day, morning and evening views are averages over windows of the simulated day.
- `busyness-network`: walks out of dead ends, islands dropped, nursery areas kept at a reduced pull.
- `busyness-commuting`: commuters set off with everyone else over 09:00–10:00 and go home at 15:00, by routes that see the current queues. Riding down is limited by the lift's capacity through a queue at its top.

## Impact

- **Engine (`busyness-engine/src/`):** a new simulation module. `index.js` runs the simulation in place of the laps–routing passes. `laps.js` gets the pull rule (already trialled, uncommitted). `queues.js`, `rushWaits` and the RAMP in `views.js` go. `routing.js` gives next-hop route trees rather than path totals.
- **Parameters (`params.json`):** adds the simulation's times and step. Removes `RAMP`, `DAY_HOURS`, `PEAK_HOURS` (as a rush length), `QUEUE_PASSES` and the trial settings `LIFT_RATE_EXP` and `AHEAD_HALF_MIN`.
- **Tests:** laps, queues, views and routing tests rewritten for the new rules. Observation tests rerun, with any change in what they find recorded in decision 011.
- **Tools:** `bin/mapdiff.mjs` (new, uncommitted) renders before and after maps for every step. `bin/run.mjs` and `bin/diagnose.mjs` follow the new results.
- **Docs:** a new decision record for the simulated day. Notes in decisions 004, 006, 010 and 015. Known issues 17, 18, 22 and 24 updated.
- **Pipeline (Python):** dead-end walks and islands in `busyness/network.py`, so the test domains are rebuilt. Sectors keep using the plain pull.
- **Run time:** likely seconds per domain in Node. The browser budget is a later change.
